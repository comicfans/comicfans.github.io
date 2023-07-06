This is also a interesting task of my previous job,
and also more than 5 years job before, so share this shouldn't hurt anybody

building C++ project can be very complex, especially when the project got larger
and larger. my company have such big project, it's windows project, based on visual studio 2010,
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
actually there's a simple way for this: visual studio build will generate logs,
(which named tlog under build dir)for its build steps, this log includes 
link command, after excluding most used
system libs (for example win32 and mfc libraries), all left libs are just built
by our projects, for example project A linked library B , we know project A
depends on project B. after extracting these information from build link log, 
we know the correct dependencies.

we can extract more useful information from the build log, it contains 
compile flags, so we can also extract them, cataloged them together,   
to generate a cmake script template. with mapping the library name directly to project name
I can generate which libraries it linked to, and it also includes information
of compiler input files, which including the source files,
so we can list these source files as cmake project sources. and now
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


Bonus of the migration:

after migration, cmake can generate a contains-every-project visual studio workspace,
with 500 projects all in it, opening it in visual studio spends very long time! plus that
not every developer interested to find their work out of 500 projects. they usually only care about
one of them. we can use cmake EXCLUDE_FROM_ALL property to improve this, the cmake script
has a 'interested project' list, all other targets which not in this list will be set EXCLUDE_FROM_ALL 
when cmake creating visual studio workspace, the top-level workspace will only show the interested
projects, all others hidden. (there's also a build all target, which will always build all projects,
even they're not shown in workspace). This greatly improved developer's experencie, their project
will only show interested projects (and their dependencies). There is also a special name 'all',
which generate the show everything workspace. this allow developer to build whole workspace, but still
focus on their specified project.

as the time of migrate, microsoft published vs2019 , which community version is free,
and cmake also support generating vs2019 projects (but still using vs2010 toolchain ), as I tested,
it can open 500 projects workspace much faster than vs2010. 

since migrated project has complete dependencies information, it can be built in parallel, just build
the generated vs workspace, msbuild will do both project-level parallisim and project file-level parallisim
to improve resource utilization. but msbuild has limitation for parallel build, it treat project relationship
and in-project file relationship as two levels, force a fixed file-level/ project-level parallel number
upfront. for example you specify project-level parallel number = 2, and in-project file level parallel number = 8,
idealy it should build 16 files at same time (say build machine is ideal for 16 build).
but if one project has only 1 file, and another as 100 file, msbuild still waste resource. 
if you try to specify very high number to avoid idle , msbuild will fire too many build process,
which also lower down build speed (they will run out of memory, spend time in context switch,or swap in/out frequency)
for my testing, it is better than one-by-one build, but still not best.
the build time decreased from 2.5 hour to 1.5 hour on a 32c64t 64G build machine(if I remember correctly).

Now we can try our next build tool: ninja , it doesn't have high-level concepts  
(it doesn't know projects or workspace like msbuild),
thus it's very simple, and dependencies can be exposed to it with best parallelisim preserved.
simpliy switch the cmake generator to ninja, rerun cmake config,
then we got a super low level ninja build script, let's time it!

it finish all the build in ... 22 minutes, 1/7 time of old build script. 
the build machine keeps full utilization until most library complete.
which is very impressive. 

for IDE users, cmake also support a "visual studio with ninja build" generator,
it generate vs2019 workspace/project files, but using ninja as actual build tool,
so you can enjoy both the IDE development environemnt and ninja build speed.

22 minutes is much faster than 2.5 hour, but can it be futuer improved ?
ninja provides a build script analysis script, to convert its build log
into a chrome profile trace, so we can see how command target scheduled on
ninja internal job queue, a clean build shows following trace profile:


as we can see, after about 11 minutes, most task complete, but there's one 
very long task, consume another 11 minutes. can we make ninja to schedule it earlier?
firstly we have to confirm it can be schedule earlier, just do a clean build
of this super-long task only, it completes in 13 minutes, with all of its dependencies
complete under 2 minutes, which means reduce overall build time is possible.
I tried author's another branch for this function, plus to support explicit build order,
with the most time consuming task as earlier build target, finally I got 
14 minutes build time, 1/20 time of previous build time. the ninja build trace like this:

as we can see, this super long job is scheuled much earlier. now there's another
bottomlack appeared, do clean build for this new bottomlack shows that 
its dependencies take much longer to complete, build time almost equal to build all time,
so we can't improve overall build time anymore.

bug hunting

our program are used in health care device, and has very complex user interact logic,
so must be tested extensively to avoid any possible crash, to achive this, it has a 
'input emulate', to inject action into system, emulate user operate, check if all
these emulation can complete. a full test run requires 2~3 week needless running to complete.
company use this approach to evulate if software satisify their MTBF standard.
Today such a huge codebase requires unit testing and regression test, but for such old
codebase (remember it has more than 20 years history!), input emulation may be
the best solution they can use.  remember what I said before ? 
developers can't verify whole program behavior without waiting 2.5 hours full build,
so they just modify and submit, wait the final emulation test can pass. so many
changeset of course introduce bugs, and now we hit a very nasty bug during emulation test.
it crashed for about a week run, nobody knows why!
such extensive testing only happened before production release (who wants to run a 
2~3 week testing for lots of random submit?), nobody can tell which version introduces this bug
(because almost nobody build whole program before submit, many history revision even can't build)
coredump show random backtrace, debugger trapped at random place, nothing useful in log,
we have to guess possible problem module and replace them by old versions(they're all com based,
ABI compatible make it possible to switch between versions) , expect to narrow down
which module has bug, but nothing found.

After many failed attemps, I realize this must be memory bug, which triggered earlier
than crash time, and lead later random crash. The only question is how to find it.
I tried a proprietary checking method, it use runtime hooking, apply on the normal binary,
but too slow, program startup takes 10 times slowdown, this is impossble to run to the bug!
seems address sanitizer is the only left option.
address santizer is a runtime memory checking technology developed by google, 
firstly it hook memory allocation/deallocation function, remeber allocated/deallocated memory
range information, secondly compiler will instrument every
low level load/store instruction, replacing them by runtime checking logic. combine
with the memory range information, it can find memory bugs, for example use after free.
since these changes is built into final binary by compiler, its much acurrate and faster
than other methods. we can tell cmake to use clang-cl (which supports address sanitizer)
to build whole projects. 

firstly I need to confirm clang-cl and address sanitizer do support msvc2010,
I created a super simple program which has the use-after-free bug, built by clang-cl
and address sanitier, it worked with msvc2019 runtime, but crash with msvc2010 runtime
(which our project built-on), I found the address sanitizer runtime
didn't list msvc2010 runtime as supported, then I tried to modify address sanitizer 
runtime, add msvc2010 runtime in list, rebuild clang-cl, then rebuild my buggy test 
code with new compiler and run it, finally the address sanitizer report the incorrect
memroy usage! next step is to build whole project, even clang-cl declared as msvc syntax compatible, 
it still needs some source code change, and for my company's project, it has
500 projects and 60000 files! but I have no choice...
 (address saniziter already support msvc2010 after I submit this problem)

I spend about two weeks (maybe even more) to make whole source code clang-cl
compatible, during this, I also find a clang-cl msvc2010 treat system include 
path as different priority (clang-cl follow gcc prioroty behavior), which leads same command line 
didn't give exactly same include order, thus some incomptable declaration build in 
one order but not another. again, I got the preprocessed file of two compiler
for comparsion to confirm this behavior difference. And I did a simple changes to clang-cl,
to make it behaviors more like msvc. 

when I complete the clang-cl compatible conversion, it already has been 1 month (maybe even more)
during this 1 month, we run emulation test on many device, everyone with a little
guess changes, still nothing found. And now it's time for the sanitized binary, I start it 
and wait it running. after 4~5 days, it also crashed, but this time with address sanitizer backtrace report!
exactly at the crash point, since address sanitizer has no false positive, it at least
is one of the bugs! it do is a memory bug, typical use-after-free, and asan shows the detail call stack
so I can easily understand what happend during the crash ! analysising the backtrace
shows that this is a reentrant problem of code, a function which not designed to be reentrant
is called recurisvly, thus its internal state already became inconsist before second entrant.
but this is wired, since this code didn't change recently, why does it suddenly break without change ?
future analysis shows these two entrants actually came from two different main loop, one is from MFC
and another is from QT, so the reason became clear, we recently migrate from MFC based UI to QT,
new code developed in QT and old code still depends on MFC, to make this work, there're two mainloop
running in code, it worked for most case, but for some win32 windows procedure call(which is used in the 'bug' code)
it will implictly trigger another roundtrip main loop process (since QT register its mainloop as
window procedure), thus Qt recalled the 'bug' code , lead its crash. to verify this, we add a small
additional protection, before calling the implicity window procedure, construct a Qt Mainloop Prevent
object, let Qt mainloop skip. then re-deploy the original codebase (without clang-cl changes) with 
the little fix, finally, it runs 1 week, 2 weeks... until all emulation is done. we also rerun
the emulation again and again, never crash.

built project with address santizer also discover more bugs, I also triggered another use-after-free bug,
it's so simple and seems can't be wrong:

``` C++
    vector<POD> vec;
    vec.push_back(vec.back())
```

In msvc2010, this is actually a use-after-free, why? address sanitizer shows that vector 
wants to access already freed memory by using back() after a internal resizing,
view the msvc2010 stl source code, we can see it actually called the move constructor variant of push_back,
which means msvc2010 auto generated the move constructor for our POD type (I didn't realize 
that msvc2010 already support move constuction), and the move construct variant push_back
first destroy its internal buffer without realizing that the passed in parameter is just reference of 
already freed memory 

google also provides a slide to detail how address sanitizer worked, it fill memory 
with special pattern to indicate it's freed, then load/store instrument will detect such access
and trap into runtime. similar method can also be used in some scenario which unsupported by address sanitizer .
for example we migrate some drawing logic from directdraw to direct2d, after the migration,
some display code just crash, but address sanitizer didn't report any error. founatly, 
this crash can be caught by debugger, it shows that after our bliting code writing,
some internal memory structure already destroyed, but can't provide exactly line number of the error code,
I still have to find it manully. address sanitizer didn't report it because it has to understand
how the memory is used. allocating memory is just ask operation system to
map some memory range valid to process, without knowning how this range is used,
if such range still valid (not returned to OS, even already freed in process)
address santizer can't know if you're read/write the bad memory (logically),
or just do correct things (for example memory allocator can reuse the freed memory range)
we're bliting memory into direct2d internal buffer, and these interface not supported
by address sanitizer, it can't help us. but we can do this manually. 
I just allocate the direct2d 1 pixel widther than blit needed. if the code
is correct, it won't overwritten contents in the extract 1 pixel, I fill the 
the extra 1 pixel location with special pattern, for example 0xfefefefe. 
then assert its contents still be same after bliting , this quickly hit the assert,
it's a classic off by one bug, it bliting more than needed thus overwritten direct2d internal state.
but why old directdraw code didn't crash ? analysising the directdraw and direct2d
internal buffer struture shows that directdraw return higher aligment than direct2d, 
so everyline it has more pending bytes, previously this bliting is also buggy, 
but it overwrite the pending bytes, thus nobody harmmed. direct2d has no pending,
bliting overwriten 1 pixel leads the crash.

so this is my experience of our build system migration and bug hunting, I hope 
to share more interest stuff with you!
