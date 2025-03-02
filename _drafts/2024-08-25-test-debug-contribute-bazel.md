
    I have lots of experience on CMake build(see my previous post migrate more than 500 visual studio projects to cmake),
I'm always satisfied how straightforward to use it to build from source.
Recently due to work requirements, I'm learning/using bazel to build C/C++, which a build tool from google, 
it gives me some interesting experience.

    the first feeling come to me is "complex". the big scale of our codebase of course
contribute lots on it, but even the small example of bazel seems more complex than cmake to me. Why should I 
need to declare some 'toolchain' and download/unpack it before build ? My OS already has everything I need!
Why not use my host compiler? Then slowly I realized that it tries to avoid any dependencies of
host, which is a big problem for C/C++ development/deploy: environment differences.

    traditional software build in linux, almost everything is shared with host, for example compiler is
system gcc, libraries are installed by package manager (apt/dnf for example). It's possible
to use custom toolchains/libraries, just not as straightforward as using system ones.
For example you need to adjust PATH, specified CC,set PKG_CONFIG_PATH or change --prefix.
Many library built with autoconf which is tricky to use (Why I need to run libtoolize, but sometimes not? what is 
m4 stand for?). Who loves to build LFS everyday? That's one major reason we love distributions,
they provide almost every tool/libraries we need, we just install them by package manager.
Such convenient development experience is the major reason I prefer to develop in Linux
instead of windows. But distributions also suffer from it, that is, to keep everything works together.

   Because on (traditional) distributions, everything is shared, which means 
if you have two software A, and B, both depends on C, then
there's only one copy of C, it make sense in the early days of
PC, there aren't so many software available, and disk is expensive. The tradeoff is:
you can't use arbitrary version of C, because A and B may only works with 
specified version of it. For this reason, we can only choose "some compatible set"
of A,B,C, so they can work together. That's why almost every distribution
has some app called "package manager"(dnf/apt for example) to figure how to install/upgrade
packages. They tells user which app can be upgrade, or reject if 
the specified version can't work with the rest of system.

    The way distributions handle packages actually deeply affact how
we develop/deploy software. Since most software running on Linux is built from source
by distributions, different distributions may choose different build config/flag, leads 
final binary not compatible with each other (even with exactly same version), 
If you're building software depends on system provided library (remember that's one major reason I love to use distributions!)
Then such binary usually won't work on another distribution, or even
same distributions after/before a regular daily update.
because system package manager doesn't know your software requirements
and upgrade a library to incompatible version (unless you package it as distribution format 
and install it globally to provides this information to package manager).
Although most distribution tries their best to avoid this, but it's still possible.
Which is the Linux version of windows dll nightmare. 

   Another limitation of such workflow is that the system
may even can't provide the complete set of required libraries we need,
as I said, system need to maintain (almost) every components on system
compatible with each other, the version requirements is much stricter
than our own requirements, We may also have to build some dependencies ourselves.
In such situation, the binary we produce will have mixed dependencies on
both system and custom built ones (even built by different toolchains),
which increase the possibility to suffer from incompatible problem.

   When we're building C/C++ with autoconf/CMake or other similar build tool, 
we (almost) bind to this dependency model by default. We can try to build
every dependencies manually, then we goes back to LFS alike scenario,
autoconf/cmake also not designed to work for such usage by default, they require lots
of tunes to work correctly.

    And this is exactly what bazel trying to resolve (at least one prospective), a bazel C/C++ project
must contain toolchain config, which means even the most basic dependencies,
like syscall/libc/stdc++, is deterministic at build time(a complete toolchain usually bind them as a whole),
and every libraries used, should came from bazel central register (BCR for short, which provides pre-defined build script),
or build from source (by build script provided by us). In this way, bazel
build whole dependencies tree with exactly same toolchain/config, so the final binary is completely self-contained,
agnostic to host system. Bazel also provides version based dependency resolve functionality, which means
when you're using a dependency from BCR, then it'll auto pull in required indirect dependencies,
also make sure they're compatible.

    bazel also try to make the build dependencies more explicitily, that is
if user didn't declare correct dependencies, bazel tries to fail the build, 
instead of success build (by accident). For example if a library A depends on
a third party library B, but you forgot to declare B as dependencies of A,
Then autoconf/cmake which using system library B will almost success the compile, 
because all headers of libraries lives in shared folder, which is used as default
include dir, then such header can be found(just because other dependencies also use default include dir)
then you won't realize such problem until somebody 
build in a environment with B installed to different location and failed.
Someone may treat this "success by accident" is better, but that actually have 
more impact than thinking. For example depends on dependencies order, 
some of the code may include headers from system shared location,
but other parts of code using a custom built library header, leads incompatible
ABI which is only detectable at run time and very confusing to fix.


   To fix such problems, bazel will soft link any input (include dependencies and the source file to compile themselves)
of the target into a per-target directory, then utilize linux namespace as 
sandbox for the build process under this dir, so it can precisely control what file
can be read/write by the build steps(still not perfect although). And if the target's output
are being used by another, bazel also won't expose any file except ones that explicitly declared,
which means any file that not being declared explicitly as input/output, can't be seen
during build. it looks wired to most cmake users, Although cmake encourage out-of-tree build,
but none-generated source files and generated intermediate artifact are still shared during build and being read in-place, 
so it's easier to rerun build step command to easily spot/debug build problems. 
The reason for this is also try to force the correct,explicit dependencies,
instead of silent success but problematic build. Consider following example:

```CMake
CMAKE_MINIMUM_REQUIRED(VERSION 3.10)
PROJECT(test_project)


add_custom_command(OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/gen_first
  COMMAND "echo" "codegen" ">" "${CMAKE_CURRENT_BINARY_DIR}/gen_first"
)

add_custom_target(incorrect_dep
  COMMAND "cp" "${CMAKE_CURRENT_BINARY_DIR}/gen_first" "gen_second"
)

add_custom_target(correct_dep  ALL
  DEPENDS ${CMAKE_CURRENT_BINARY_DIR}/gen_first
)


```

we use custom command to generate a intermediate artifact, then two targets use it.
for correct_dep, it will run our codegen as expected, but not incorrect_dep.
the problem is that if we build correct_dep once, then incorrect_dep magically 
run successfully, but actually we're using out-of-date intermediate artifact.
We may never realize that incorrect_dep can only have expected result if we build correct_dep first! 
Or even worse, incorrect_dep generated artifact also being used by other generator steps, then one build 
can't create a consist result set, depends on which generator CMake use, 
you need to build whole project many times to get correct result, or maybe
never can! Because some generator( like ninja ) expect the build instruction generated
by CMake has 100% correct dependencies, so as they see incorrect_dep
build successfully once, they won't rerun it. 

but for bazel this can't (or at least much harder) happen, because the generated artifact
being placed in per-target directory, if we don't declare them correctly, then other
targets can never use any outputs in unexpected way. Consider similar build script in bazel


```bazel

genrule(name  = "first",
        outs=["gen_first"],
        cmd = "echo gen_first > $(OUTS)"
)

genrule(name = "second",
        outs= ["gen_file2"],
        cmd = "cp gen_first $(OUTS)")


```

we forgot to declare gen_first as input of second target, then
second build will always fail, because every target can only see
restricted filesystem provided by bazel, they can't see each
others' intermediate files unless correctly being declared.
The correct version show as following:


```bazel
genrule(name  = "first",
        outs=["gen_first"],
        cmd = "echo gen_first > $(OUTS)"
)

genrule(name = "second",
        outs= ["gen_second"],
        srcs = ["gen_first"],
        cmd = "cp $(SRCS) $(OUTS)")
```

We also notice that the $(SRCS) $(OUTS) usage, Because the isolated environment
controlled by bazel, we can only use input/output var which defined by bazel,
thus prevent any mismatch filename usage.

  Bazel also supports programming by its script language,
called skylark, a subset of python language, it's more feature complete
(but also more complex) language. As comparison, CMake script is much like
a bash script, everything is string and you need to interpret/escape/combine
strings under different scenario. Every input/output of cmake function ,
from include dir, to dependency target, are just
string (cmake use string and string list interchangeable, which is 
easy to hack, but also a big source of headaches). Consider that we need
to walk a target's dependencies, we will have a function that take a string
as target name, get target_link_libraries as string list, then repeat this 
process, but for bazel, the target is a structure (but can be easily constructed
from target name string), and every information are just member variable
of structure. For simple project script, without too much logic ,I feel cmake script 
much easier to write/understand, but for complex project with lots of custom
logic, untyped cmake script is more error-prone than bazel.

    
  Bazel's sandbox is a very important component, it's also applied to testcase
by default, so testcase can enjoy same isolation advantages to build step ,
and during testing, I hit a very interesting bug: my testcase try to utilize IPPROTO_ICMP 
to send ping packet, it runs without problem in host environment, but always 
failed to create the socket fd inside bazel sandbox environment. Since 
bazel is a open-source project, I decide to deep dive into this problem.


  First I tried to understand what permission is required for my code to run,
you can reference [linux man page](https://man7.org/linux/man-pages/man7/icmp.7.html)
and check [LWN](https://lwn.net/Articles/422330/) to see how it works. So the basic idea is that
normal user should be allowed to create such socket type without root permission,
if its GID inside /proc/sys/net/ipv4/ping_group_range knob start/end range
on my host, it shows 
```
0 65535
```
which basically means any user group on my host can use IPPROTO_ICMP without special permission.
but such knob inside bazel sandbox is always a wired value
```
65534 65534
```
and that range definitely not including my GID inside bazel's sandbox,
so I tried to write ```0 65535``` range to mimic host behavior inside sandbox,
only got a permission denied error, even I'm running my testcase as 'fakeroot'.
According to linux man page, such range should be initialized to ```1 0```,  
I can't understand why it shows magic ```65534 65534```


First idea came to me is to check docker's behavior, because it also use namespace,
Unfortunately I can't see any problem to run my test inside docker. So I ask this question
in [runc discussions](https://github.com/opencontainers/runc/discussions/4366), and 
cyphar kindly answered my questions, then I realize docker and bazel sandbox are using
different mode of namespace, docker is running privileged mode as root, which can map range of 
UID/GID into namespace, make the environment pretty much like normal Host environment,
bazel is running as unprivileged mode, which can only map 1 UID/GID into namespace.
That's why we have 'fakeroot' tag in bazel, it will map our UID to 0 inside namespace.
But that still didn't explain why I have magic ```65534 65534``` value inside sandbox,
and why I can't change it even I'm running as 'fakeroot'. Then when I google this 65534 magic number,
I got [stackoverflow](https://stackoverflow.com/questions/34831861/can-i-assume-that-nobody-is-65534)

```
Historically, the user “nobody” was assigned UID -2 by several operating systems, although other values such as 2^(15)−1 = 32,767 are also in use, such as by OpenBSD. For compatibility between 16-bit and 32-bit UIDs, many Linux distributions now set it to be 2^(16)−2 = 65,534; the Linux kernel defaults to returning this value when a 32-bit UID does not fit into the return value of the 16-bit system calls. An alternative convention assigns the last UID of the range statically allocated for system use (0-99) to nobody: 99.
```
and

```
Maybe you can use the value of 
/proc/sys/fs/overflowuid.
```

 



That gives me some inspiration,which means kernel are treating our ping_group_range as invalid value,
I also got [this](https://discuss.linuxcontainers.org/t/setting-net-ipv4-ping-group-range-inside-an-lxd-container/2162/4)
```
So what this means is that if either the minimum or maximum GID value in the specified range is not valid inside of the user namespace, the kernel will (silently) set the sysctl’s value to the range of “1 0” from the init user namespace (IMO, it should be returning an error in this situation).

After the write has silently failed and you read back the sysctl value, the kernel does something silly by reporting that the min and max values of the GID range are the overflow gid (DEFAULT_OVERFLOWGID in the source code) since the actual sysctl value doesn’t map to a valid GID range inside the container. This is why you see 65534 65534 when reading the sysctl from inside the 18.04 container.
```
this thread also kind enough to provide corresponding kernel source code:
From net/ipv4/sysctl_net_ipv4.c
```C
static int ipv4_ping_group_range(struct ctl_table *table, int write,
                                 void __user *buffer,
                                 size_t *lenp, loff_t *ppos)
{
...
        if (write && ret == 0) {
                low = make_kgid(user_ns, urange[0]);
                high = make_kgid(user_ns, urange[1]);
                if (!gid_valid(low) || !gid_valid(high) ||
                    (urange[1] < urange[0]) || gid_lt(high, low)) {
                        low = make_kgid(&init_user_ns, 1);
                        high = make_kgid(&init_user_ns, 0);
                }
                set_ping_group_range(table, low, high);
        }

        return ret;
}
```


So what left is just to confirm what happened in kernel when I set ranges to this knob...
Debugging kernel over serial gdb seems very unstable to me, but I still manage to step
most important parts of the code, when I try to write ```0 65535``` to this knob as fakeroot,
it shows that low is valid gid if I run as fakeroot, but not high. Consider the unprivileged
sandbox one UID/GID map restriction, then the whole picture is clear:

1. when bazel create networkspace, the config knob reset to init value 1 0, which forbidden any user to use IPPROTO_ICMP
2. bazel use unprivileged namespace, it will have exactly one UID/GID inside the namespace
3. because GID = 1 can't map to valid GID inside namespace, so we got a magic ```65534 65534``` knob value

Then after that, it's also straightforward to fix it

1. this knob is only writable by root, so we must be fakeroot
2. the only valid GID inside namespace is the GID of root, so the range must be write as 0 0

A quick test shows that this fix do let me using IPPROTO_ICMP inside fakeroot sandbox, Nice!
And during that I also found [podman](https://github.com/containers/common/blob/ae4a61e1b2e0af84a668f87f7622d86ebc418cba/pkg/config/containers.conf#L80) have similar process during namespace initialization. 

Now my fix already being part of bazel 7.4 release, enjoy it!


