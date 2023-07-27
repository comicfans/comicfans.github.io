  Some years ago when I'm working on a ARM project, it will streaming 
images on screen, with many business logic workflow UI around it, 
our Project Manager decided to port our application to run on X86 device, one challenge is that how to  
make its display function portable but also performant. To achieve reasonable
FPS on current low-profile ARM device, previous application use device specified API,
which driven the display controller directly, it behaves like a 'overlay' layer
on normal GUI surface, we blit image pixels into its bake buffer. 
We decide to migrate to OpenGL shader based approach, since another production line which runs on
windows, already using some image process algorithm based on OpenGL shader, 
we hope to reuse that work.
    To avoid inventing wheels, we also have to find some libraries to ease our migration,
with some research, they decide to use gstreamer as the base, it's 
designed for video pipeline , try to be portable/performant/easy-to-use,
already supports OpenGL display node, already handle many common case logic.
    It seems to be a good fit, but actually has many hidden problems in practise, it takes
me about half a year to complete the migration, half of the time I'm digging
in gstreamer to point out how to make it work to satisfy our usage, fix API
breakage with version upgrade, and any bugs in it.
    If we look at it from the present point of view, gstreamer is still 
involving quickly during that time (it's still 0.1x version when our project start),
and it's very risky to base our implementation on it, but such development process
is a very exciting journey to me, very interesting. Since I have to learn how
it works and tell whether the problem is from my code or from gstreamer itself,
I have to ask developers a lot by mail listing, and I learn
how open source software is developed, how its community running, and how
to contribute back to it. And this makes me fall in love with open source.
    First problem I've faced in using gstreamer is how to feed video frame
data into its pipeline, such workflow is reliable for file based input, 
but not for API feed (at that time). Thus this is my [life-first
open source patch submission](https://bugzilla.gnome.org/show_bug.cgi?id=729760),
of course I just discover the fundamental problem, patch is mostly based on
suggestions of gstreamers developers.
    And later on, I mostly worked on the OpenGL stuff, find/fix random bugs
with help from developers (especially Matthew Waters (ystreet00)/
Sebastian Dröge (slomo)/Tim-Philipp Müller/ and many among others), like
use-after-free/race-condition and other misc ones. To makes our project running 
without problem, I've also submitted a simple (yet useful enough)
[leak tracing](https://github.com/apitrace/apitrace/issues/416) 
function to API trace (final python implementation written by author
instead of my C++ one), with this tool, many object leak bugs also being addressed,
makes gstreamer and our project more and more stable.
    Our project also migrate its graph part to QtGraphicScene based,
which is also OpenGL based, thus I also spend some time to test OpenGL context
share, 
  


