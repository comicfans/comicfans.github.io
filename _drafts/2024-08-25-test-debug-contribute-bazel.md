
    I have lots of experience on CMake build, I'm always satisified how straghtforward use it to build from source,
and recently due to work requirements, I'm learning/using bazel, which a build tool from google, 
it gives me some interesting experience.

    the first feeling come to me is "complex language". the big scale of our codebase of course
contribute lots on it, but even the small example of bazel is more complex to me. why should I 
need to declare some 'toolchain' and download/unpack it before build ? my environment has everything!
why not use my host compiler? then slowly I realized that it tries to avoid any depenencies of
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
such convenient development experience is the main reason I prefer to use linux
over windows. But distributions also suffer from it, that is, to keep everything works together.


    the complexcity of build system, actually have deep connection with
the way how different software components works together in operation system,
without understanding the problem on this topic, we can't truly understand the 
problem of build system. So this blog, serve as the first part of series blog, 
will focus on how distribution works(instead of talking about build system).
And why it changed, I mainly focus on linux distribution, and will
extend it to windows/osx a little.


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

    The idea to treat distributions as just a big set of pre-built binaries, 
is over simplified idea, the biggest problem is keep this big set "compatible with each other",
Because on (traditional) distributions, everything is shared, which means 
if you have two software A, and B, both depends on another software C, then
there's only one copy of C, this behavior came nature in the early days of
PC, during that time, there aren't so many software available,
and disk is expensive, it make sense to work like this. The tradeoff is:
you can't just use any version X of C, because A and B may only works with 
specified version of C. For this reason, we can only choose "some compatible set"
of A/B/C, to make sure they work together.

  This is not big problem in the early days, for that software is simple and they don't
upgrade frequency. But with the quantity increased, with more depenencies and upgrades,
it became big problem. If you have used early version windows (98/me for example), 
there're tons of errors about xxx.dll not found/conflict problem. Because
many software install their bundle dlls into common place and
overwritten each other, as different versions of one dlls usually have different
behavior (even very small),this easily silently break lots of software.
it quickly became headache of using windows system.

    On recent windows system, microsoft changed how libraries being
works on system: they tries to keep different versions co-exists, and the software
will still see same set of libraries even another installed different version.
This takes more disk usage but at least make them less possible to break.
It's impossible to keep only one version of one dll to satisfy everyone,
Because most software running on windows is distributed by non-centralized
vendors in pre-built binary format, different dlls requirements already being
determined at build time, can't change after distributed.

    Linux is different, most software provies source code, distribution
is the centralized place to build everything, so it's possible that to create
a "every library only one version " approach. Consider the big quantity of 
software components (hundreds of thousands with intra-depdencies,
with possible changed depenencies requirements after upgrade),
it's impossible for human brain to finger out a 'compatible set', 
That's why distributions's package manager always came
with some sort of "depenencies resolver" , distribution developers
only specify necessary (directly) depenencies between software, then package manager
use resolve algorithm to figure out which version of package can be used together,
or which set of packages should upgrade in one go, so after install/upgrade, 
everything still being a compatible set. Because the install/upgrade will
write system wisely, it always requires administration permission, just like 
most windows software installation.

   If every package update increase their dependencies requirements step by step,
it's possible that after many small updates, every package of system became 
complete different to the initial one, and none of them can be turned back 
to old version. If you tried ,suddenly package manager told you to almost reinstall 
every package of whole system. And this should be one reason why distributions 
have "big version", and only keep that very short time lifecycle,
when the "big version" increased , almost every package became new version,
and old big version won't have upgrade any more. A biggest problem of using 
these distribution is that if you don't upgrade with "big version", then
you can't use some up-to-date software, and if you upgrade with "big version",
a lot of software may change the way they work. 

   There do exist some 'rolling release' distribution, provides most up-to-date
version of every software, they usually requires you to update system
regularly, if not, then you'll be left into a staled state, and it's highly
possible that a update after long time stale, will break the system.
I've hit such problem while using archlinux, because their new version software
depends on newer version of glibc, and I didn't update system during the glibc upgrade
window, then every new package I installed won't work, and if I upgrade
glibc, then all old software stop working. It's also possible that the package 
manager itself or some basic command line got upgradad and stop working. 
Then you suddenly being left in a unrepairable state: you can't run package manager
to install compatible version, even can't login, or can't boot at worst. 

    This complex dependencies problem lead people to find better way to run
software, Appimage is one of the answers, they packs every dependencies
as a "big fat binary" and don't depends on any host software (or at least
tried their best), so no matter which distribution/version user use, they
can always running this "big fat binary".

    For example traditional distribution openssl library is shared across whole system software, 
but for Appimage, every "big fat binary" have its own copy of openssl. 
And it's highly possible that they're not same version, with
different build configuration , not inter-replaceable. 

    This idea is not new invention, this is exactly how Android/ios/osx Application
works, people almost never complain install/uninstall one Application will
randomly break another one on these system. It do take more disk space, but the storage today
is cheap enough, and it gives developer great flexibility to develop different
Application without worrying about breaking unrelated things. 

   A interesting changes of traditional distribution is that they also developing 
their 'Appimage' alike approach, for example flatpak from fedora and snapd from Ubuntu,
but after reading their introduction, I feel the Appimage is the only right choice: you simply download a file,
run it without special steps (except executable permission to it), just like the way a "portable" windows 
application that don't requires install.  I can't understand why flatpak/snapd is designed as their
ways, it looks stupid to me : they still requires some pre-setup, for example the flatpak/snap 
command itself , to use software themselves.  And to install software with snap, 
it even requires sudo, what the hell differences between it and 
sudo apt-get install to the user? And for upstream project (who developed
the source code), they still don't have a distribution agnostic way to pack/run
their software, these package won't work on distribution
that don't have flatpak/snapd, which completely make them valueless as 
"universal" binary distribution approach.

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
which is the hardware abstraction from the OS. For example OS can decide
how much CPU/Memory a application can use.  Because application never take direct control
of hardware (or at least, under proper management of OS), OS can support
running multi application at same time, one process corruption, have very
limited impact to other process. 

   The multi user support, being another level of abstraction, OS
define user as a predefined resource group, for example all process run
under one user, can freely read/write all files belongs to this user, and OS
usually impose less restrictions between different process under same user,
so a user can have multi process cooperate together, at the same time if
one user's setup is corrupted, it has very limited impact to other users.

   And on today's mobile phone (Android/IOS), such isolation became more restrict: 
Every "App" being an isolated running environment, even it seems like all 
Apps is "owned" by you, the single user. And the old cooperate ways that works 
within multi-user-multi-process, almost don't work anymore, due to that they're
too relax. For example on linux/windows system, if user running a malware,
it can stole all file information belongs to this user, but on mobile system,
one malware can only access very limited information of other part of system
(unless user permit it). These changes, is very similar to the history of 
how software being packed/distributed, they share less, became more individually.

    From user's perspective, mobile phone is much easier to use than computer,
every App simply works after install, it will never told you to "install App A version X"
to make "App B version Y" work. 

    There're also some interesting argument between "share less" and "share more"
approach, first one is a 2021 blogspot from [Gentoo](https://blogs.gentoo.org/mgorny/2021/02/19/the-modern-packagers-security-nightmare/),
for people who aren't familiar with Gentoo, it's a source based distribution,
every software is distributed as source code, and built on user's machine.
User can adjust build options, which provides the most
flexibility/customized behavior of dependencies. You can determine if software A
depends on software B or not(by tradoff to support B-related function or not).
Author in this blog express the concern about static linking, bundled/vendored 
dependencies, and Go/Rust/Python don't follow stable ABI/shared linking practise,
which make distribution's work harder, and recently a 2024 blogspot from [Debian](https://jonathancarter.org/2024/08/29/orphaning-bcachefs-tools-in-debian/)
also express concern on how bcachefs-tools is packed, it shares similar idea
with Gentoo ones': (traditional) distribution maintainer prefer to share more,
but new languages other than C, usually don't have stable ABI, and their packing/building
model, prefer "share less" approach, this conflict make them headache. There're 
also a reddit thread for first blogspot [here](https://www.reddit.com/r/rust/comments/ml77p3/the_modern_packagers_security_nightmare/).

  Personally, I respect these traditional distributions maintainer's work,
they helped me to quickly enjoy the linux environment, maintaining different
versions on one system compatible with each other, but I got to say on this
topic, these traditional distribution really don't get the real point: the users,
care about if they can use the software, and don't care about how
these software being packed/run. The top voted response from the reddit thread
expressed this idea:(if I remembered correctly): why software developer bundle/vendored
their dependencies instead of relaying on system shared libraries? 
because you can't tell user/customer that the software is unable to run
just due to their host lacks required dependencies!  As our blog mentioned, today's
user-friendly operation system **do** prefer "share less" approach, it's the way that
impact user least. Traditional distribution maintainer expects software can run
correctly with different version of dependencies is a good desire, but unfortunately not realistic. 

  And these new languages (python/rust/go) provide their own package/dependencies manager
(and they usually pin all dependencies version to some specified version)
and do static linking(or alike behavior), Because that's currently the best
known way to keep final running binary behaves same as when its maintainers developed
them. If users run with different dependencies, developers can't
tell if a bug belongs to software itself, or just a behavior change of its
dependencies. The term "bug" is really hard to define in this scenario, 
sometimes developers tries to fix unreasonable/buggy behavior, but some others
are already depends on this behavior. Can distribution maintainers just changes
these dependencies as their will? Yes they can, but it also becomes their
response to support user's question about why software don't behave same to upstream
project's. Because 



