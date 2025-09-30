# Debugging a nasty thread bug

Some years ago when I'm working on a ARM project, it will streaming 
images on screen, with many business logic workflow UI around it, 
our Project Manager decided to port our application to run on X86 device, one challenge is that how to  
make its display function portable but also performant. To achieve reasonable
FPS on current low-profile ARM device, previous application use device specified API,
which driven the display controller directly, it behaves like a 'hardware display layer',
which is independent to normal OS/UI surface, we blit image pixels into its bake buffer,
it directly goes into screen, without passing through OS.
and it also supports 'green key', we can place this layer under
normal GUI surface, if that area pain key color as background color,
such color will be transparent, shows underline image stream, 
allow the application draw some toolkits over image.
We decide to migrate to OpenGL shader based approach, first reason is 
that another production line which runs on windows, 
already using some image process algorithm based on OpenGL shader, 
we hope to reuse that work, another reason is that we're using Qt toolkits,
its QtGraphicScene component can be used to draw toolkits, it can be  
configured to use shared context with other OpenGL context, thus making image
and toolkit painting in same context.


To avoid inventing wheels, we also have to find some libraries to ease our migration,
with some research, they decide to use gstreamer as the base, it's 
designed for video pipeline , try to be portable/performant/easy-to-use,
already supports OpenGL display node, handle many common case logic,
and also have a Qt shared context example, seems quite a good fit.
But actually has many hidden problems in practise, If we look at it from the
present point of view, gstreamer is still involving quickly during that time (
it's still 0.1x version when our project start),
and very risky to base implementation on it. It takes
me about half a year to complete the migration, half of the time I'm digging
into gstreamer to point out how to make it work to satisfy our usage, later
I spend more time to keep API compatible with new gstreamer version,
and keep finding new bugs. 


But such development process is a very exciting journey to me, very interesting. Since I have to learn how
it works and tell whether the problem is from my code or from gstreamer itself,
I have to ask developers a lot by mail listing, and I learn
how open source software is developed, how its community running, and how
to contribute back to it. This makes me fall in love with open source.

First problem I've faced in using gstreamer is how to feed video frame
data into its pipeline, such workflow is reliable for file based input, 
but not for API feeding (at that time, especially input format/size can be dynamic changed).
Thus this is my [life-first open source patch submission](https://bugzilla.gnome.org/show_bug.cgi?id=729760),
of course I just discover the fundamental problem, patch is mostly based on
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


Since we need to use OpenGL context sharing, I also spend some time on it,
to improve general stability. Some strange bugs found in our project and gstreamer,
which lead by some tricks in OpenGL context sharing, different behavior
by different vendor/driver/OS, but finally I fix all of them to make our application
have stable context sharing under Linux/Windows AMD/Nvidia, only except one: 
our application running on windows randomly stop streaming images, a gstreamer 
thread deadloop. With days and days repeating debugging, I realized that
it must have bug in low-level threading logic, otherwise the function
g_cond_broadcast (pthread_broadcast equivalent) should return in meaningful 
time instead of dead looping, I can only have my answer after entering the rabbit hole.

Gstreamer using gthread for portable threading. Even glib is designed to be portable,
it mimic pthread exactly (if not at all) with minor naming change.
It just compile to exactly same pthread entry under linux,
and emulate pthread semantic under other OS. According to gthread source code,
gthread uses win32 Event to emulate condition variable (for Windows XP, actually
gthread on Xp is emulating some thread API of Vista, then emulate pthread 
through emulated Vista API). In gstreamer OpenGL component, 
condition_variable is used as following (IIRC):

  1. OpenGL has implicit thread local context bind (1:1 map),
     A control thread is used to call all OpenGL calls, its responsible is to 
     just run callbacks from sending thread.

  2. Other thread can inject a callback using something like 
     ```call_on_gl_thread```, to inject callback into control thread slot,
     that callback will be run on the control thread, so it's safe to call OpenGL functions there.
     call_on_gl_thread also only return after the callback completed from control thread.


  3. OpenGL control thread must wait other thread complete inserting callback 
     for every paint loop, so there will be a condvar , which sending thread tell
     OpenGL control thread it complete inserting the callback.

  4. after OpenGL Control thread got the callback, it runs that and use another condvar 
     to tell sending thread that callback already complete.

  5. next loop
    
To hunt the bug, I've inserted bunch of assert, then run my testcase over and over,
expecting hitting assert can tell where the inconsistencies happen.
Since it may contain threading bug for example not correctly protecting 
code, these assert may also give incorrect result. After days debugging 
and reading, I found a design flaw in gthread condition variable implementation: 


1. gthread using win32 Event to emulate condition variable blocking/waking
2. when g_cond_wait being called, gthread create a TLS structure, which contains one win32 Event.
3. it append this structure to corresponding condvar waiter list, then call WaitForSingleObject to enter sleep state
4. g_cond_boardcast being called, it finds the event from waiter list, calling SetEvent to wake that Event.
5. the wait thread return from WaitForSingleObject, check return value to know if it's being waked, or timeout

Seems perfect right? Unfortunately not, consider that OpenGL scenario, we need a pair of condvar
for one sending thread, then if two sending thread needs to call call_on_gl_thread, we need two
pairs of condvar for that, so for both sending threads, they are inserting their own callback
then wake OpenGL control thread to run these callbacks, it should have following actions:

1. from OppenGL control thread, it enter sleep state through g_cond_wait (by WaitForSingleObject)
2. that should be waken by SendingThread1, run callback from SendingThread1
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


