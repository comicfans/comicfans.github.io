
    I have lots of experience on CMake build, I'm always satisified how straghtforward use it to build from source,
and recently due to work requirements, I'm learning/using bazel, which a build tool from google, 
it gives me some interesting experience.

    the first feeling come to me is "complex language". the big scale of our codebase of course
contribute lots on it, but even the small example of bazel is more complex to me. why should I 
need to declare some 'toolchain' and download/unpack it before build ? my environment has everything!
why not use my host toolchain ? then slowly I realized that it tries to avoid any depenencies of
host, it also brings me memory the problem I tried to resolve myself: environment differences.

    traditional software build, almost everything is shared with host, for example compiler is
system gcc, libraries came from system install (apt/yum for example). It's possible
to use custom tools/libraries, but always requires extra steps.
for example to use alternative compiler, you need to adjust PATH, or specified CC,
for  alternative libraries, you need PKG_CONFIG_PATH or maybe change --prefix.
many library still built with autoconf 
it's always hard to build a complete isolated set of libraries and use everything
from it (think about LFS!), and it became one of the reason we love distributions,
they provide almost every tool/libraries we need, we just install them by package manager.
such convenient deveopment experience is the main reason I prefer to use linux
over windows. But distributions also suffer from it, that is, to keep everything works together.


    the complexcity of build system, actually have deep connection with
the way how different software components works together on today's operation system,
without understanding the problem on this topic, we can't truly understand the 
problem of build system. So this blog, serve as the first part of series blog, 
will focus on how distribution works(instead of talking about build system).
And why it changed, I mainly focus on linux distribution, and will
talk about windows/osx a little.


How software components works on today's linux system


   Now days most people prefer to use "distribution" instead of build whole 
linux themself(LFS for example), the distribution(debian/fedora for example) provides
pretty much complete software components, for example desktop, image viewer,
document writer, command line tools, and many development libraries out of box 
to use, you can use package manager (dnf/apt for exmaple) to easily install 
them from the "repository" of distribution, but actually most software components 
across different distribution is almost the same, the gnome desktop you used from fedora, 
won't be too different to the one that run on ubuntu, they both built from the gnome source code, only has
some differences on how binaries is packed together.

    But the idea to treat distributions as just a big set of pre-built binaries, 
is over simplified idea, a biggest problem of distributions is to maintain a big set of "compatible"
software components. Because on (traditional) distributions, everything is shared, which means 
if you have two software A, and B, both depends on another components C, then
there's only one copy of C, this behavior came nature on the early days of
PC, during that time, there aren't so many software available on one machine,
and disk is expensive, it make sense to work like this. it has tradeoff: you can't just use any version X
of C, because  A and B may only works with some specified version of C.
and for this reason, A can't be arbitrary version neither, if it has different 
C version requirements, then A and B clash each other.

  This is not big problem in the early days, software is simple and they never
upgrade frequency. But when the quantity increase, and all of them have
more and more depenencies and upgrades, it became a really big problem.
If you have used early version windows (windows 98/me for example), 
there're tons of errors about xxx.dll not found/conflict problem. Because
many software install their bundle libraries into common place, when they
overwritten each other, and one library can't guarantee to work exactly same
way across different versions, it quickly became headache of using windows
system.

    On recent windows system, microsoft seems to change how libraries being
works on system: they tries to keep different versions co-exists, and the software
will still see same set of libraries even another installed different version.
This takes more disk usage but at least make them less possible to break.
It's impossible to keep only one version of one library to satisfy everyone,
Because most software running on windows is distributed by many non-centralized
vendors in pre-built binary format, it's always possible they're depending 
on different versions of a common library, when it's being decided at build 
time , it won't change after distributed.


    Linux is different, almost every software provies source code, distribution
is the centralized place to build everything, so it's possible that to create
a "every library only one version " approach. Consider the big quantity of 
software components (hundreds of thousands with intra-depdencies,
with possible changed depenencies requirements after upgrade),
it's impossible for human brain to finger out a 'compatible set'
of all components. That's why distributions's package manager always came
with some sort of "depenencies resolver" , distribution developers
only specify necessary (directly) depenencies between components, then package manager
use resolve algorithm to figure out which version of package should be used together,
or which set of packages should upgrade in one go, so after install/upgrade, 
everything still being a compatible set. Because the install/upgrade will
write system wisely, it always requires administration permission, just like 
most windows software installation.


   If every package update increase their dependencies requirements step by step,
it's possible that after many small updates, every package of system became 
complete different to the initial one, and none of them can be turned back 
to old version. If you tried ,suddenly package manager told you to almost reinstall 
every package of whole system. And this should be one reason why distributions 
have "big version", and only keep that very short time lifecycle. 
then the "big version" increased , almost every package became new version,
and package in old big version won't be upgrade any more. 


   There do exist some 'rolling release' distribution, they usually requires you to update system
regularly, if not, then you'll be left into a staled state, and it's highly
possible that a update after long time stale, will break the dependencies.
I've hit such problem while using archlinux, because their new package depends
on newer version of glibc, and I didn't update system during the glibc upgrade
window, then every new package I installed won't work (I only update parts of 
software). It's also possible that the package manager itself or some basic 
command line got upgradad and stop working. Then you suddenly being left in a
broken system, can't run package manager,even can't login, or can't boot at worst. 


   since package install/upgrade may also involve some post configure steps,
and these steps also depends on other components, it's also possible that a package
which is compatible with other components, became non-compatible after some other 
packages updates, even the contents itself(shared library for example) still 
compatible with others. 

    This complex dependencies problem lead people to find better way to run
software, Appimage is the answer, they don't 
try to create a complete compatible set of all software, instead, they create
an minimal set compatible components environment, exactly for the target software, contains
every dependencies the software using, it forms a "fat package", or can be treated 
as a minimal "distribution". For example traditional distribution 
openssl library is shared across whole system software, 
but for Appimage or docker, every "fat packet" have its own copy of openssl. 
And it's highly possible that they're not same version, with
different build configuration , not inter-replaceable. 

    This idea is not new invention, this is exactly how Android/ios/osx Application
works, people almost won't complain install/uninstall one Application will
randomly break another one. Of course it takes more space, the storage today
is much cheaper, and it gives developer great flexibility to develop different
Application without worrying about breaking unrelated things. 

    Distribution also developing their 'Appimage' alike approach, for example
flatpak from fedora and snapd from Ubuntu, but after reading their introduction,
I feel the Appimage is the only right choice: you simply download a file,
run it without special permission, just like the any windows that don't 
requires install.  I can't understand why flatpak/snapd is designed as their
ways, it looks stupid to me : they still requires some pre-setup, for example the flatpak/snap 
command itself , to use software themselves.  And to install software with snap, 
it even requires sudo, what the hell differences between it and 
sudo apt-get install to the user? 

   I think they may consider the centralized authentication for these software
and make sure non-experienced user not hammed by malware, but as long as the package
still requires some special tool to install, instead of simply download and 
click, it's absolutely not the solution for software distribution.



   There're some distribution which choose a different approach to maintain packages, 
nixos for example, will always use the exactly library version during build,
and one library can have multi different versions co-exists at same time, it's
pretty much like today's windows idea. Of course someone don't like it, we will
mention that part later. suckless linux, static link everything, even libc (using musl instead of glibc),
so every binary became independent, they don't share anything at all if ideally. 
But I think it's still questionable, will also mention it later. Gentoo/LFS 
choose another approach: they're install/update software by provides build
script instead of pre-built binary, user build software on their own machine.
Will also mention it later. But before all of them, a more interesting topic
is that: 


   how software components works individually or cooperate together on today's
Operating system ?


  It's path follows pretty much the same as the way software is managed, in 
early days, operating system (and the hardware) is very basic, for example
the earliest operating system I use is "DOS", it only supports one user running
one program at same time,which means you can't run a music player while game running, 
except that the game program itself, contains a music play function.
and software running under dos can do almost everything the hardware allowed, 
it should be careful here, I didn't say "everything operating system allowed",
because DOS almost have no restriction on program running in it, which means 
if you like, your software can completely take control of the hardware, and 
behaves like the "operating system" itself, makes DOS itself vanished.
It sounds like you download a APP on your iphone, then it wipes IOS itself,
like a joke, but in early days, consumer level hardware lacks necessary function to let 
operating system implements protection to itself, it's understandable.
During this time, the hardware is shared between OS and application, no isolation,
if application mess up the hardware state, then OS also can't recover.

   Then the hardware have proper MMU and ring level support, it lets OS itself
to have more permission than normal userspace process, if implements correctly,
the hardware is completely controlled by operating system, userspace process
won't control hardware directly, they're controlling "virtual resources", 
which is the hardware abstraction from the OS, for example
how much CPU/memory can be used.  Because application never take direct control
of hardware (or at least, under proper management of OS), OS can support
running multi application at same time. The multi user support, became another
level of abstraction, it's similar to multi-process support, but usually OS
define user as a predefined resource group, for example all process run
under one user, can freely read/write files belongs to this user, and OS
usually impose less restrictions between different process under same user,
than the ones belongs to different user. During this time, there're isolations
between different process, also between different users.

   And on today's mobile phone, such isolation became more restrict: it's
between different applications. 





    


  



To be clear, install App on android/ios
may involve a authentication , it behaves like "sudo", but usually that's 
because most App on them requires purchase, this step make you may spend money
on it, it make no sense that 

    
    




(honestly speaking after so many years linux
experience, I still don't understand What The Hell libtoolize/automake/autoconf/m4 is,
and refuse to learn any information about them, which I think is really a mess and a waste of time)


Gentoo linux

