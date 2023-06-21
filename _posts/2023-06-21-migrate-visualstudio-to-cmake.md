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
it copies some of its header file to a common place, then later build will
use this common place as include dir. so this is the public API header
for the library,but using manual copy to expose them. 


