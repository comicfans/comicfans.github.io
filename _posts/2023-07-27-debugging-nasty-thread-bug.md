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
but to me it mimic pthread exactly (if not at all) with minor naming change.
It just compile to exactly same pthread entry under linux,
and emulate pthread semantic under other OS. According to gthread source code,
gthread uses win32 Event to emulate condition variable (for Windows XP, actually
gthread on Xp is emulating some thread API of Vista, then emulate pthread 
through emulated Vista API). when g_cond_wait(pthread_cond_wait) entered, it use win32 Event
stored in TLS, and append it to the waiter list of condition_variable (because
condition_variable can be waited by multi thread),
when g_cond_broadcast want to wake the condition variable, it takes this waiter
list out of condition_variable , then set every event. And in gstreamer OpenGL
component, condition_variable is used as following (IIRC):

  1. OpenGL has implicit thread local context bind (1:1 map),
     A control thread is used to call all OpenGL calls, it has a slot to 
     run some callback which can contain OpenGL calls from other thread

  2. Other thread can inject a callback using something like 
     ```call_on_gl_thread```, to inject callback into control thread slot,
     so OpenGL calls in this callback can safely run on the control thread,
     this function also only return after the callback completed from control thread.

  3. So control thread will have a condition variable, which waits other thread
     complete inserting callback, and then inserted function will be called,
     then wake the condition_variable which wait on the other thread (which
     call call_on_gl_thread)

  4. call_on_gl_thread, which being called from other thread, after inserting
     callback, it wakes the condition_variable of control thread, after that,
     it waits on itself condition_variable, which wait control thread wake
     to tell it callback running completely
    
To hunt the bug, I've inserted bunch of assert, then run my testcase over and over,
expecting hitting assert can tell where the inconsistencies happen.
Since it may contain threading bug for example not correctly protecting 
code, these assert may also give incorrect result. After days debugging 
and reading, I found a design flaw in gthread condition variable implementation: 
no matter how many condition variable is used, there will be only one win32 Event used
(for one thread), it seems reasonable for simple scenario, because one thread can only
be blocked by only one Event, so this TLS event is used exactly once 
by only one condition_variable (which being called wait on this thread),
but gstreamer usage shows that this is not enough, because we can't 
grantee the Event is always used by exactly same condition_variable on
the wake thread and wait thread !  There's a window that wake thread calling
SetEvent on one condition_variable, but the shared win32 event already not
being used by that condition_variable in wait thread (for example you can  
call g_cond_broadcast multi times on one condition_variable infinitely on wake
thread, to make that Event 99% signaled, so the wait thread, matched 
condition_variable almost return from g_cond_wait), then if the wait thread using
different condition_variable to wait other event, it reuse the signaled 
state Event, thus thinks it already being waked, but actually this is completely
signal from other condition_variable. Since such wait/wake happened
very frequency in OpenGL control thread painting, it can be easily triggered.
   After identifying this bug, fix should be easy, create individual win32
Event for every condition variable (of one thread), and keep this mapping 
relationship, while waking up, wake thread always call the corresponding 
Event of that condition variable, thus mismatch gone.

