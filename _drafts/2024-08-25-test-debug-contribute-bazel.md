
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

   To accomplish this goal, bazel will soft link any input (include dependencies and the source file to compile themselves)
of the target into a per-target directory, then utilize linux namespace as 
sandbox for the build process under this dir, so it can precisely control what file
can be read by the build steps(still not perfect although). And if the target's output
being used by another, bazel also won't expose any file except ones explicitly declared,
which means any file that not being declared explicitly as input/output, can't be seen
during build. it looks wired to most cmake users, Although cmake encourage out-of-tree build,
but none-generated source files and generated intermediate artifact are still read in-place, 
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


