This is also a interesting task of my previous job,
and also more than 5 years job before, so share this shouldn't hurt anybody

building C++ project can be very complex, especially when the project got larger
and larger. my company have such big project, it's windows project,
has lots of sub-project, every sub project build a lib, totally 500 sub-projects,
more than 60000 C++ source code! since there're intra-dependencies between
these sub-projects, we can't just build them with arbitrary order, a build script
is provided, written the build order of all these projects. To build whole project
we need to run this script, take some coffee, and wait 2.5 hours for its complete!
due to its super-long build time, developers prefer to download the pre-built binary,
only modify and rebuild project they're working on. this improve speed, but has 
a big drawback, the pre-built binary is usually out dated (it's impossible to create
an always up-to-date binary if build time is much slow than developer commit! if you
have only one build machine), developers're always using mismatched functional 
binaries to work together. since I have lots of software build experience, I decide to  
resolve this problem.


analysis why current build step is slow

to improve build speed, I must know why current build step is so slow, simply
view the task manager, it shows very low utilization. confirm with the build script,
I can see that it use visual studio msbuild to build every project, ** one by one **,
msbuild can only utilize all CPU when there're many enough files in one project,
and always waste CPU resource when project build near complete. it's CPU
utilization will like this:








old script using 1 by 1 build logic, it forbidden future speed improvement.
because if there're two individual dependencies chains, for example
A depends on B
C depends on D

you can build B and D at same time, build A immediately after B is complete

build C immediately after D is complete. but old script 1 by 1 build steps
can only build B,A,D,C. to maximize the resource usage, we need the build tool
to know exactly dependencies between projects, and also support visual studio
environment, to ease the migration. I choose cmake for this task. at the time
of this migration, there're also other solutions for example meson, but at 
that time it's focus on linux support, its visual studio support is still
experimental, thus I didn't consider it.

choose cmake reasons:

1. it has high level project/dependencies description, lots of documents,
   easy to find answers

2. many big project using it for example llvm/clang, they're very big projects
   confirm cmake scalable in such big projects.

3. it has long time visual studio multi-version multi-toolchain support,
   generated project can be used in visual studio, multi profile
   (Debug/Release/RelWithDebInfo) also match visual studio usage

4. it can also generate build script for ninja, which is the
   fastest low level build tool I've ever seen

what I have to do:

1. point out the intra dependencies of all these 500 projects

2. convert every project into cmake script

3. makes all these projects built successfully, verify it should be built 
   exactly same as visual studio build 

since there're 500 projects, find out dependencies between them is time consuming,
actually there's a simple way for this: visual studio build will generate logs 
for its build steps, this log includes link command, after excluding most used
system libs (for example win32 and mfc libraries), all left libs are just built
by our projects, for example project A linked library B , we know project A
depends on project B. after extracting these information from build link log, 
we know the correct dependencies.

we can extract more useful information from the build log, it contains 
compile flags, so we can also extract them, cataloged them together,   
to generate a cmake script template. with mapping the library name directly to project name
I got a cmake script converter, it reads msbuild log, set necessary build flags
and link libraries, catalog common used flags as dependencies (for example
when you link unicode MFC, it will add some compile/link flags), and Bang, 
a cmake script almost usable pop, I just need to reference the dependencies
between them (extracted from build log link command line), build/test the most
ancestor (because it didn't depends on others, so it can be built most easily) 
one by one , finally I can convert whole project to cmake based. and after
every project convert complete, I can verify it can build correctly and work.


some clean up:

during this convert, I also find old build script do some pre-build custom actions,
it copies some of project header file to a common place, then later build will
use this common place as include dir. so this is the public API header
for the library,but using manual copy to expose them. This approach also
limit the build parallelism, sine msbuild don't understand these header
are actually came from other project, when header changed, old build script
has to re-copy all files and rebuild all projects to make sure used header
are all up-to-date. cmake already provide corresponding command to satisfy this situation,
library public header. I decide to createa 'public_include' dir for every project,
and moving corresponding public header into it. it avoid the copy action, 
and any header change triggered depencency rebuild can also be understood by msbuild.
to future ease the header usage, I didn't just make it as binary library public
include dir property, intead I create a 'library_header' library for every
project, so these header library can be used without the binary library built,
it can greate simplify circle dependencies problem (two libraries depends on each other's header)

cleanup dll import

during this migrate , I've also faced another interesting problem, sometimes 
projects build will fail with error 'file protected' (sort of), but building C++
projects will involve header/cpp file read, and linker will only write to their
corresponding lib file, why such file process conflict happen ? after some digging
I found it only failed when two projects both including a header with dll import.

visual studio c++ compiler has special syntax for dll import
you can write 

```C++
#import <msxml3.dll>
```

to include msxml3 functional, If you just build a single project and use this syntax in a header (used by some cpp from this project),
everything seems working, but if two projects both including a single header file with this, and building simultaneously,
they will fail with due to file process conflict (randomly), checking documents and 
try with msvc command line, we will see that this import syntax envole some special internal process,
msvc compiler actually create special file for every import dll file, and such file path is global unique (bind to the included header),
for a single project build, this process only happen once,
but if two projects include same header, such file process  will conflict.
(msvc compiler must use file lock to avoid same path process conflict).
for this reason, it's not recommended to use import in public headers.
if analysis the preprocessed file by cpp we can see that, such dll import actually create a header file for the dll, 
and use the generated header as include. so we can wrap the dll import process as a project internal process,
and only expose the generated header, thus make header share can be used by other projec.
with this fix, such error never happened


cleanup  (possible) circle dependencies
another trickly part is that old build script has one project (named A) built twice, 
and first time build result is different to the second one. 
this is possible for circle dependency structure library, for example

libeary A feather 1 depends on library B,
but library B depends on library A to build
usually a stripped version of A  (without feather 1) is built (without B), to create library B,
then A is linked again with library B , to include the missed feather 1.
after checking the built twice project, I didn't find such requirements, 
it just include a outdated version header of another library (B), and after A build, 
old build script build project B, copy up-to-date header of B, then build A again,
thus A see different header contents. I think this is due to that during two projects
development indivdually , they don't have good method to include each other's public API header,
so they just keep each others' header as part of their source. thus create duplication and confusing.
with the public_header as library fix, two projects binary library can use each others' header library,
no more outdated header, and such twice build is also stripped.

fixing nastly include problem
with my public_header approach, include dir will be stay at every library dir,
if one library header include header depends
on another library header, that dependencies header should also be added to include path.
(old script put all header in a common place and use it as include dir, all needed file
can always be found ). plus that include order is also important (for example there're different msxml usage in different project)
they will fail the build (at best) or even built successfully but with slightly different semantic (worst).
to resolve this problem, we can also using msbuild generated log, it records old build process,
using its compile command record, I can replicate previous build commands, using msvc command
I can print out the included file tree, compare it with new command file tree, and
compare result of previous and now preprocess file, I can find out which include directoy is missing,
know which file is included at which order, thus fix the inconsist behavior.



