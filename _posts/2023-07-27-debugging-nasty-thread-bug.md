# Debugging a nasty thread bug

Some years ago I worked on a GUI project, which needs to 
stream video on screen, while paint some UI over video layer.
Our Project Manager decided to port this from ARM to X86.
The challenge is how to make this UI painting portable while still performant.

To achieve reasonable FPS on current low-profile ARM device,
previous implementation use device specified API to drive the display controller directly, 
you can blit pixels directly into display controller baking buffer,
which will be flushed on screen without passing through normal OS.
It also supports 'color key', when you paint GUI interface over
that special buffer layer, display controller will make any 
pixels with the color key to transparent, 
allow the application draw toolkit over underlay video layer.

We decide to migrate this to OpenGL shader based approach, 
first reason is that another production line already using shader based image processing algorithm,
we hope to reuse that work, another reason is that we're using Qt toolkits,
its QtGraphicScene component can be configured to use shared context, 
thus making image processing and toolkit painting in same context.


To ease that migration, we also consider using gstreamer pipeline, 
It's designed for video pipeline, portable/performant/easy-to-use,
supports OpenGL display, also have a Qt shared context example, seems quite a good fit.
But actually it has many hidden problems in practise,
If we reconsider the decision from the present point of view, gstreamer is still involving quickly during that time (
it's still 0.1x version when our project start),
and it's very risky to use that in a production. It takes
me about half a year to complete the migration, half of the time I'm digging
into gstreamer to point out how to make it work to satisfy our usage, later
I spend more time to keep API compatible with newer version,
and keep finding new bugs. 


But such development process is a very interesting journey to me, Since I have to learn how
it works and tell whether the problem is from my code or from gstreamer itself,
I had to ask developers a lot by mail listing, and I learn
how open source software being developed, how its community running, and how
to contribute back to it. This makes me fall in love with open source.

First problem I've faced is how to feed video data into its pipeline by loading from memory.
Video loading from file is reliable but not for loading through API at that time, especially input format/size can be dynamic changed.
Thus this is my [life-first open source patch submission](https://bugzilla.gnome.org/show_bug.cgi?id=729760),
I only report the issue to mail listing, patch is mostly based on 
suggestions of gstreamer's developers.


And later on, I mostly worked on the OpenGL stuff, find/fix random bugs
with help from developers (especially Matthew Waters (ystreet00)/
Sebastian Dröge (slomo)/Tim-Philipp Müller/ and many among others), like
use-after-free/[race-condition](https://bugzilla.gnome.org/show_bug.cgi?id=734830)
and other misc ones. To makes our project running 
without problem, I've also submitted a simple (yet useful enough)
[leak tracing](https://github.com/apitrace/apitrace/issues/416) 
function to API trace (final python implementation written by author
instead of my C++ one), with this tool, many object leak bugs also being addressed,
makes gstreamer and our project more and more stable.


I also spend lots of time on OpenGL context sharing, to improve gstreamer general stability.
I found some strange bugs in our project and gstreamer,
which lead by OpenGL context sharing dirty tricks, 
different vendor/driver/OS behavior, but finally I fix all of them, 
our Application has stable context sharing under Linux/Windows AMD/Nvidia, only with one exception: 
While running on windows XP, it randomly stop streaming images, with one gstreamer 
thread deadloop. With days and days repeating debugging, I realized that
it must have a low-level threading logic bug, from gthread (a library that Gstreamer used as portable pthread implementation) itself.
otherwise g_cond_broadcast (pthread_broadcast equivalent) shouldn't dead looping.
I never think about this possibility since it's being used as the thread implementation
by all GTK application on Windows XP, if there's bug in it,
it should be spot by others as well, But the truth is that
other application do suffer from similar issue (I think DIA, a diagram editor also random dead on windows XP)
just not that many people care about it, seems I'm the first one whom need to fix it badly.
Now let's dig into the rabbit hole.

The Gstreamer threading model at high level looks like this: (IIRC)

  1. OpenGL has implicit thread local context bind
     A GL control thread is used to call all OpenGL functions, that thread own the OpenGL context,
     its only responsible is to run callbacks from sending thread.

  2. Other thread can inject a callback using something like 
     ```call_on_gl_thread```, to inject callback into control thread slot,
     that callback will be run on the control thread, so it's safe to call OpenGL functions there.
     call_on_gl_thread also only return after the callback complete from control thread.

  3. OpenGL control thread must wait other thread complete inserting callback 
     for every paint loop, so there will be a condvar , which sending thread tell
     OpenGL control thread it complete inserting the callback.

  4. after OpenGL Control thread got the callback, it runs that callback, and use another condvar 
     to tell sending thread that callback already complete.

  5. next loop

To hunt the bug, I've inserted bunch of assert/logs in gthread, then run my testcase over and over,
to understand its behavior, expect any assert violating tells me the inconsistencies.
Since this bug might due to incorrect threading implementation ( for example some thread primitive 
not work as expected), these assert might also give false positive. With days and days testing,
I slowly got the idea on how gthread emulate pthread under windows.

gthread mimic pthread with minor naming change, It compile to exactly same pthread stubs under linux,
Their Windows implementation is based on Vista API, for windows XP, they first emulate the Vista API, then use the Vista based implementation.

1. use CriticalSection to emulate mutex
2. use win32 Event to emulate condition variable blocking/waking
3. when g_cond_wait being called, gthread create a TLS structure, which contains one win32 Event.
4. it append this structure to corresponding condvar waiter list, then call WaitForSingleObject to enter that thread into sleep state
5. g_cond_boardcast being called on other thread, it finds the event from waiter list, calling SetEvent to wake that Event.
6. the wait thread return from WaitForSingleObject, check return value to know if it's being waked, or timeout

Such logic seems correct to me at first glance, consider the gstreamer scenario, 
if two sending thread needs to call call_on_gl_thread, we need two
pairs of condvar for that, so for both sending threads, they are inserting their own callback
then wake OpenGL control thread to run these callbacks, that should have following actions:

1. OppenGL control thread enter sleep state through g_cond_wait (by WaitForSingleObject) to wait SendingThread1
2. SendingThread1 wake it up, control thread 
3. it should enter sleep again by g_cond_wait, wait SendingThread2 to wake it again, then run callback from SendingThread2


Since that TLS structure in g_cond_wait has only 1 win32 Event, that event will be reused
by different condvar (there can't be more than one Event entered sleep state in one thread at same time, right?), when following sequence happened, we have problems:

1. Control thread g_cond_wait on condvar1(for SendingThread1) WaitForSingleObject returned as TIMEOUT
2. g_cond_wait thinks it's timeout, correct
3. SendingThread1 calling g_cond_broadcast, which will call SetEvent, on an already TIMEOUT event
4. Control thread call g_cond_wait on condvar2 (for SendingThread2), WaitForSingleObject immediately returned because it has a pending SetEvent by SendingThread1 !
5. Control thread thinks it's being waken by SendingThread2.
6. Doomed


It's more likely to happen with our setup since we have multi input sources to Gstreamer OpenGL (which will create multi threads that calling call_on_gl_thread). This can't 
grantee the Event is always used by exactly same condition_variable on
the wake thread and wait thread !  You can  
call g_cond_broadcast multi one condition_variable infinitely from one 
thread, to make that Event 99% signaled, so the wait thread, matched 
condition_variable almost immediately return from g_cond_wait, then if the wait thread using
different condition_variable to wait other event, it reuse the signaled 
state Event, thus thinks it already being waked, but actually this is completely
signal from other condition_variable. 
   After identifying this bug, fix should be easy, firstly create individual win32
Event for every condition variable (of one thread), this can't be avoided since
during the window of WaitForSingleObject and it returns, it's impossible to have
another lock on that thread to assume the Event only used by one condvar.
Now every condvar will only set their own Event, no more strange behavior anymore

the full discussion and patch here:
https://bugzilla.gnome.org/show_bug.cgi?id=762853


