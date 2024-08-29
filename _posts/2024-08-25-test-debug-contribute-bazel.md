
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

    people treat distributions as just a big set of pre-built binaries, is really
a simplified idea, a biggest problem of distributions is to maintain a big set of "compatible"
software components. Because everything is shared, you can't just use version X
of library A, because another software B may only works with version Y of A.
Consider the big quantity of software components (hundreds of thousands with intra-depdencies,
with possible changed depenencies requirements after upgrade),
it's impossible for human brain to finger out a 'compatible set'
of all components. That's why distributions's package manager always came
with some sort of "depenencies resolver" , distribution developers
only specify necessary (directly) depenencies between components, then package manager
use resolve algorithm to figure out which version of package should be used together,
or which set of packages should upgrade in one go. 

   If every package update increase their depenencies requirements step by step,
it's possible that after many small updates, every package of system became 
complete different to the initial one, and none of them can be turned back 
to old version. and if you try it,suddenly package manager told you to almost reinstall whole
system. And this should be one reason every distributions only keep a very short
time lifecycle, they won't update packaget for ever. There so exist some
'rolling release' distribution, they usually requires you to update system
regularly, if not, then you'll be left into a staled state, then it's highly
possible that a update after long time stale, will break the depenencies.
I've hit such problem while using archlinux, because their new package depends
on newer version of glibc, and I didn't update system during the glibc upgrade
window, then every new package I installed won't work (I only update parts of 
software). it's also possible that the package manager itself or some basic 
command line got upgradad, and stop working,  then you suddenly being left in a
broken system, can't run package manager,even can't login, or can't boot at worse. 

   since package install/upgrade may also involve some post configure steps,
and these steps also depends on other components, it's also possible that a package
which is compatible with other components, became non-compatible after some other 
packages updates, even the contents itself(shared library for example) still 
compatible with others. 

    This complex dependencies problem lead people to find better way to run
software, appimage/ docker and many similar technology is the answer, they don't
try to create a complete compatible set of all software, instead, they create
an isolated environment, exactly for the target software only. For example
traditional distribution have openssl library shared by all other software,
but for appimage or docker, every software binary you run, may have its own
copy of openssl. And highly possible that they're not same version or have
different build config, not replaceable by each other. 

    This dependencies problem also exist in software development, if you 
create software which depends on system library, then your codebase may stop
building/working on other machine (even same distribution, only with
a few packages different!) or even on your machine after a package update.
To overcome this, you really need a isolated environment which has
every dependencies in it (and is tricky) and it has nothing to do with host,
that's exactly what bazel (tries to) do.

    first of all the bazel main binary, is based on java, because jvm tries 
to be a 'vm', it can be seen as one level of isolation. I know many people
loves python, but the python interpreter and library itself, is really not
as compatible as java.  you can always run old java code on new JVM,  but for 
python, the interpreter works at text language level, it's syntax broke several
times ()

secondly






