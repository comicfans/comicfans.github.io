
    I have lots of experience on CMake build, I'm always satisified how straghtforward use it to build from source,
and ecently due to work requirements, I'm learning/using bazel, which a build tool from google, 
it gives me some interesting experience.

    the first feeling come to me is "complex language". the big scale of our codebase of course
is a lot factor to it, but even the small example of bazel is more complex to me. why should I 
need to declare some 'toolchain' and download/unpack it before build ? my environment has everything!
why not use my host toolchain ? then slowly I realized that it tries to avoid any depenencies of
build host, it also brings me some memory the problem I tried to resolve myself: environment differences

    traditional software build, almost everything is shared, for example compiler is
system gcc, libraries came from system install (apt/yum for example). it's possible
to use custom tools/libraries, but always requires extra steps, although people already tries to make it easier.
for example to use alternative compiler, you need to adjust PATH, or specified CC,
for  alternative libraries, you need PKG_CONFIG_PATH or maybe change --prefix.
many library still built with autoconf (honestly speaking after so many years linux
experience, I still don't understand What The Hell libtoolize/automake/autoconf/m4 is,
and refuse to learn any information about them, which I think is really a mess and a waste of time)
it's always hard to build a complete isolated set of libraries and use everything
from it (thing about LFS!), and it became one of the reason we love distributions,
they provide almost every libraries we need, you just install them by package manager.
But distributions also suffer from it, that is, to keep everything works together.

    people treat distributions is just a big set of pre-built binaries, is really
a simplified idea, a biggest problem of distributions is to maintain a big set of "compatible"
software components. Because everything is shared, you can't just use version X
of library A, because another software B may only works with version Y of A.
Consider the big quantity of software components (hundreds of thousands with intra-depdencies,
with possible changed depenencies requirements after upgrade),
it's impossible for human brain to finger out which should be a 'compatible set'
of all components. That's why distributions's package manager always came
with some sort of "depenencies resolve" algorithm, distribution developers
only specify Necessary depenencies between components, then package manager
use resolve algorithm to figure out which version of package should be used together,
or which set of packages should upgrade in one go. 

   If every package update increase their depenencies requirements step by step,
it's possible that after many updates, every package of current system became 
different to the initial one, and if you want one of the package to go back
to old version, suddenly package manager told you to almost reinstall whole
system. And this should be one reason every distributions only keep 

   since package install/upgrade may also involve some post configure steps,
and these steps also depends on other components, it's also possible that a package
which is compatible with other components, became unusable after some other packages
updates, even the contents itself still compatible with others. 





