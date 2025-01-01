This Christmas I want to play with Unreal, so here comes this complaining post: WTF!!!

First I followed the official guide from Unreal website to install it on Windows: 
  1. install epic launcher, I already have some games from epic store, that's not a big problem for me.
  2. install Unreal Engine, I tried version 5.5.1 while writing this blog.
  3. create a tutorial project: I tried vehicle 

then I got my first WTF impression from Unreal Engine: for an almost empty project template, 
the editor was running ~10 FPS or even worse? I can understood unreal engine is powerful and resource hungry,
but a bare project for ~10 FPS still shocks me. (FYI, I'm running on 4800U iGPU + 16GB laptop,
even this is not very powerful setup, it can still running Doom Eternal at 60 FPS with low configuration)

  Then I tried to build this project in Visual Studio, the noise of laptop fan sounds like a jet engine,
Why? With task manager opened, I got my second WTF impression: the top cpu consuming process is not 
compiler cl.exe, but the windows malware scanner process. I guess the scanner process is trying its best to find
any potential malware, from hundreds and thousands of header files (of course this is only my suspect). 

  Another possible cause may be my laptop is too weak to work with latest 5.5.1, I
also tried version 4.27, which the editor runs much smoother than 5.5.1, but project build is still slow.
After checking the documentation from Unreal (https://dev.epicgames.com/documentation/en-us/unreal-engine/hardware-and-software-specifications?application_version=4.27)
it mentioned Operating System	Ubuntu 18.04, so let's try Unreal in Linux!

  And I didn't expect this is the beginning of my nightmare ...

  Because there's no unify way to distribute C/C++ binary on multi distros, we need to compile Unreal Engine
4.27 from source, this is the ["Official Guide"](https://dev.epicgames.com/documentation/en-us/unreal-engine/linux-quick-start?application_version=4.27)
it mentioned:

  first git clone source code (at 4.27.2 tag), and then run Setup.sh, this should be easy ... 
until it encourage errors like:
```
Failed to download 'http://cdn.unrealengine.com/dependencies/UnrealEngine-16546836/0115693eb18085175fb3bd9da53e044d46e4b6f4': The remote server returned an error: (403) Forbidden. (WebException)
```

then google find a [Unreal forum thread](https://forums.unrealengine.com/t/linux-couldnt-compile-unreal-4-27-2/820507) :
![image]({{ site.baseurl }}/images/2024-12-30-wtf-unreal.markdown/Commit_gitdeps_xml.png)

Even the error message is different to mine, I think it should also resolve my problem, 
it said that I need the Commit.gitdeps.xml from the Unreal repository, which I simply think it's the up-to-date one in unreal git repo,
I ignored fact that UnrealEngine source is being developed in house (seems with perforce), and only sync to github periodically,
so I grab a random Commit.gitdeps.xml from unreal git repo head version. Running Setup.sh start to download lots of dependencies (with my 30 Mbps slow internet...), 
I thought everything is fine and got to sleep. After 8 hours downloading, the script shows some xdg-mime command not found warnings, 
seems that Unreal build script hardcode xdg-mime directly in source code, without checking its availability...

     ```
     rg xdg-mime
     Engine/Source/Developer/DesktopPlatform/Private/Linux/DesktopPlatformLinux.cpp
     253:            RunXDGUtil(*FString::Printf(TEXT("xdg-mime query default %s"), MimeType), &Association);
     395:    if (!RunXDGUtil(FString::Printf(TEXT("xdg-mime install --novendor --mode user %sPrograms/UnrealVersionSelector/Private/Linux/Resources/uproject.xml"), *FPaths::Engi
     neSourceDir())))
     399:    if (!RunXDGUtil(TEXT("xdg-mime default com.epicgames.UnrealEngineEditor.desktop application/uproject")))

        ````
then
        ```
      rg RunXDGUtil
      Engine/Source/Developer/DesktopPlatform/Private/Linux/DesktopPlatformLinux.cpp
      233:static bool RunXDGUtil(FString XDGUtilCommand, FString* StdOut = nullptr)

tracing this RunXDGUtil funciton call, we got 
Engine/Source/Runtime/Core/Private/Unix/UnixPlatformProcess.cpp,
which launch "/bin/bash" with "xdg-mime and read stdout/stderr, 
so when xdg-mime command not present on that system, these check
became useless... to make sure it works, I installed xdg-mime commands and rerun
Setup.sh to make sure it complete without warnings, now it outputs:


```
target arch set to: x86_64-unknown-linux-gnu
Building ThirdParty libraries

If you don't see SUCCESS message in the end, then building did not finish properly.
In that case, take a look into /home/xwang/project/UnrealEngine/Engine/Build/BatchFiles/Linux/BuildThirdParty.log for details.

No third party libs needed to be built locally
```


next step is run GenerateProjectFiles.sh, should be also easy? but here comes the tricky part: it print lots of "xxx.dll not referenced" warning, from the C# project build log.  I've seen too much such stupid useless warnings while compiling C# project, so I completely ignored all of them, and then the final step: 

   ```
```make
  ```

it quickly error out: 

```
Please make sure that Engine/Source/ThirdParty/Linux is complete (re - run Setup script if using a github build)
```

why? Setup.sh already shows 
```
No third party libs needed to be built locally
```
I rerun Setup.sh , then GenerateProjectFiles.sh, then make, same error.
let's find the source code then...
```
rg "re - run"
Engine/Source/Programs/UnrealBuildTool/Platform/Linux/LinuxToolChain.cs
1322:					throw new BuildException("Please make sure that Engine/Source/ThirdParty/Linux is complete (re - run Setup script if using a github build)");
```

```csharp
string LinuxDependenciesPath = Path.Combine(UnrealBuildTool.EngineDirectory.FullName, "Source/ThirdParty/Linux", PlatformSDK.HaveLinuxDependenciesFile());
				if (!File.Exists(LinuxDependenciesPath))
				{
					throw new BuildException("Please make sure that Engine/Source/ThirdParty/Linux is complete (re - run Setup script if using a github build)");
				}
```

so the build is driven by C#, it's looking for a mark file exists, but such file isn't created by neither Setup.sh nor GenerateProjectFiles.sh.
I manually touch this file, and suddenly this error gone ... then I found UE4.27 build script from [AUR](https://aur.archlinux.org/cgit/aur.git/tree/PKGBUILD?h=unreal-engine-4)
```
  # For some reason, despite this file explicitly asking not to be removed, it was removed from the UE5 source; it has to be re-added or the build will fail - this is the UE4 package, but this will remain in place in-case this occurs for UE4 branches
  if [[ ! -f ${pkgname}/Engine/Source/ThirdParty/Linux/HaveLinuxDependencies ]]
  then
    mkdir -p "${srcdir}/${pkgname}/Engine/Source/ThirdParty/Linux/"
    touch "${srcdir}/${pkgname}/Engine/Source/ThirdParty/Linux/HaveLinuxDependencies"
    sed -i "1c\This file must have no extension so that GitDeps considers it a binary dependency - it will only be pulled by the Setup script if Linux is enabled. Please do not remove this file." "${srcdir}/${pkgname}/Engine/Source/ThirdParty/Linux/HaveLinuxDependencies"
  fi
```

I can't believe such a big 3D Engine (already reached version 5.5.1), still have bug in build script ... 
or maybe nobody developing with UE under Linux ...

then I hit another wired bug, when it starts compiling C++ , it immediately complain that initialize_list from std can't be found? ok, let's make it VERBOSE
```
make VERBOSE=1  
```
no verbose log ? 
```
VERBOSE=1 make VERBOSE=1  
```
still no verbose log ? let's check the Makefile 
```
BUILD = bash "$(UNREALROOTPATH)/Engine/Build/BatchFiles/Linux/Build.sh"
```

all targets being built by this script, digging into it:
```bash

source Engine/Build/BatchFiles/Linux/SetupEnvironment.sh -mono Engine/Build/BatchFiles/Linux
 If this is a source drop of the engine make sure that the UnrealBuildTool is up-to-date
if [ ! -f Engine/Build/InstalledBuild.txt ]; then
	if ! xbuild /property:Configuration=Development /verbosity:quiet /nologo /p:NoWarn=1591 Engine/Source/Programs/UnrealBuildTool/UnrealBuildTool.csproj; then
		echo "Failed to build to build tool (UnrealBuildTool)"
		exit 1
	fi
fi
xbuild /property:Configuration=Development /verbosity:quiet /nologo /p:NoWarn=1591 Engine/Source/Programs/UnrealBuildTool/UnrealBuildTool.csproj
echo Running command : Engine/Binaries/DotNET/UnrealBuildTool.exe "$@"
mono Engine/Binaries/DotNET/UnrealBuildTool.exe "$@"

```

so UnrealEngine doesn't use Makefile (or at least for the most important build part) , 
it's built with UnrealBuildTool (again ,in C#), and it didn't respect VERBOSE=1 flag...
when something goes wrong, you can't simply tell it to output the
detailed command invoke, which simply prevent you from fixing the problem...

with some code reading, it seems that LocalExecutor is the class to execute
command, and command invoke information piped with Log.TraceVerbose. 
I don't know how to turn on this log level so I removed the verbosity compare 
(add -verbose argument will do this trick, I found it later, again, from a [random forum thread](https://forums.unrealengine.com/t/how-do-you-run-unrealbuildtool-verbose/328764)) .  
Now make finally shows the problematic clang invoke, Unreal
use its bundled clang to compile, with bundled libc++, which sit at ```Engine/Source/ThirdParty/Linux/LibCxx```, 
It's wired that this folder only contains very a few headers, why ?
I thought it must be some download/unpack error, so tried to remove this folder, or reset git source,
re-run Setup.sh to re-download everything, change to random Commit.gitdeps.xml ... nothing works.

Finally I found in another [random forum thread](https://forums.unrealengine.com/t/unable-to-build-4-27-from-source-setup-bat-403-forbidden-error/1156805/3), and one suggested
```
 I found a fix - this error is coming from this file: Engine/Build/Commit.gitdeps.xml
Just be sure to download the xml file for your release tag.
```
![image]({{ site.baseurl }}/images/2024-12-30-wtf-unreal.markdown/424_release_notes.png)

cross check with the AUR script, I slowly realized that the Commit.gitdeps.xml I use is still incorrect,
I must download the one in release page... I just want to say 

```
F**K
```

After Setup.sh re-download everything, now GenerateProjectFiles.sh don't output any warnings now...
at least this show sign that I'm on the correct track...
Make finally success (spent another 8 hours? I'm sleeping during build). Then I followed tutorial to open a template project, try to build it, now here comes the next WTF: UE4 Editor just exit after creating the project? I forgot where the information came from, maybe logging or a dialog?
which told me UE4 editor can't build the project, I have to build it myself. So I looked the contents of project dir:

it has a CMakeLists.txt, so I naturally think this is for project build, but build with it shows
```
/home/comicfans/project/UnrealEngine/Engine/Source/Runtime/Core/Public/Misc/Build.h:45:3: error: Exactly one of [UE_BUILD_DEBUG UE_BUILD_DEVELOPMENT UE_BUILD_TEST UE_BUILD
_SHIPPING] should be defined to be 1
        #error Exactly one of [UE_BUILD_DEBUG UE_BUILD_DEVELOPMENT UE_BUILD_TEST UE_BUILD_SHIPPING] should be defined to be 1
 
```
WTF is these error ? It lacks these important define flags, and I also realized that the CMakeLists.txt simply set clang++ as C++ compiler with
```

set(CMAKE_CXX_COMPILER /home/comicfans/project/UnrealEngine/Engine/Extras/ThirdPartyNotUE/SDKs/HostLinux/Linux_x64/v19_clang-11.0.1-centos7/x86_64-unknown-linux-gnu/bin/clang++)
```

after project directive so this config won't be picked by cmake, configure can confirm this:
```
-- The C compiler identification is GNU 14.2.1
-- The CXX compiler identification is GNU 14.2.1
```

it has nothing to do with clang++. then I tried to put this line before project
```
-- The C compiler identification is GNU 14.2.1
-- The CXX compiler identification is Clang 11.0.1
-- Detecting C compiler ABI info
-- Detecting C compiler ABI info - done
-- Check for working C compiler: /usr/bin/cc - skipped
-- Detecting C compile features
-- Detecting C compile features - done
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - failed
-- Check for working CXX compiler: /home/comicfans/project/UnrealEngine/Engine/Extras/ThirdPartyNotUE/SDKs/HostLinux/Linux_x64/v19_clang-11.0.1-centos7/x86_64-unknown-linux
-gnu/bin/clang++
-- Check for working CXX compiler: /home/comicfans/project/UnrealEngine/Engine/Extras/ThirdPartyNotUE/SDKs/HostLinux/Linux_x64/v19_clang-11.0.1-centos7/x86_64-unknown-linux
-gnu/bin/clang++ - broken
CMake Error at /usr/share/cmake/Modules/CMakeTestCXXCompiler.cmake:73 (message):
  The C++ compiler

    "/home/comicfans/project/UnrealEngine/Engine/Extras/ThirdPartyNotUE/SDKs/HostLinux/Linux_x64/v19_clang-11.0.1-centos7/x86_64-unknown-linux-gnu/bin/clang++"

  is not able to compile a simple test program.

  It fails with the following output:

    Change Dir: '/home/comicfans/project/unreal/demo1/build/CMakeFiles/CMakeScratch/TryCompile-1NHlQZ'
    
    Run Build Command(s): /usr/bin/cmake -E env VERBOSE=1 /usr/bin/gmake -f Makefile cmTC_90248/fast
    /usr/bin/gmake  -f CMakeFiles/cmTC_90248.dir/build.make CMakeFiles/cmTC_90248.dir/build
    gmake[1]: Entering directory '/home/comicfans/project/unreal/demo1/build/CMakeFiles/CMakeScratch/TryCompile-1NHlQZ'
    Building CXX object CMakeFiles/cmTC_90248.dir/testCXXCompiler.cxx.o
    /home/comicfans/project/UnrealEngine/Engine/Extras/ThirdPartyNotUE/SDKs/HostLinux/Linux_x64/v19_clang-11.0.1-centos7/x86_64-unknown-linux-gnu/bin/clang++    -MD -MT CMa
keFiles/cmTC_90248.dir/testCXXCompiler.cxx.o -MF CMakeFiles/cmTC_90248.dir/testCXXCompiler.cxx.o.d -o CMakeFiles/cmTC_90248.dir/testCXXCompiler.cxx.o -c /home/comicfans/pro
ject/unreal/demo1/build/CMakeFiles/CMakeScratch/TryCompile-1NHlQZ/testCXXCompiler.cxx
    Linking CXX executable cmTC_90248
    /usr/bin/cmake -E cmake_link_script CMakeFiles/cmTC_90248.dir/link.txt --verbose=1
    /home/comicfans/project/UnrealEngine/Engine/Extras/ThirdPartyNotUE/SDKs/HostLinux/Linux_x64/v19_clang-11.0.1-centos7/x86_64-unknown-linux-gnu/bin/clang++ -rdynamic CMak
eFiles/cmTC_90248.dir/testCXXCompiler.cxx.o -o cmTC_90248
    /home/comicfans/project/UnrealEngine/Engine/Extras/ThirdPartyNotUE/SDKs/HostLinux/Linux_x64/v19_clang-11.0.1-centos7/x86_64-unknown-linux-gnu/bin/x86_64-unknown-linux-g
nu-ld: warning: /usr/lib/gcc/x86_64-redhat-linux/14/../../../../lib64/crt1.o: unsupported GNU_PROPERTY_TYPE (5) type: 0xc0008002

```

let's ignore the mismatch C/C++ compiler problem. The clang++ seems try to link with system gcc crt, not the bundled one, I guess the CMakeLists.txt is completely broken, I can't understand why a broken CMakeLists.txt being kept 
in project dir ? just to confusing people like me? 

then I also found a .pro file, which is a Qtcreator project file, then I tried it,
Qtcreator open project successfully, but build project spends 5 minutes to 
start actual compiling? then I found a [bug report](https://forum.qt.io/topic/26118/solved-qt5-qmake-performance-issue-8-times-slower-than-qt4-qmake),
so building with Qtcreator is a bad idea. besides that , Qtcreator IDE also 
shows exactly same inline code error 

```
exactly one of [UE_BUILD_DEBUG...
```

which indicates that although Qtcreator can build project, the flags used by build is not setup correctly for the IDE part.
then I found this [link](https://gist.github.com/wuyingnan/4730db8eb6df590f9a5ac00f28f0db14)
which records another guy's UE4 try under Linux:
```
We build the project for once to generate the intermediate files.
We find the Definitions.MyGame.h in path Path/To/UnrealProjects/MyGame/Intermediate/Build/Linux/SomeBuildID/UE4Editor/Development/MyGame. 
... Copy the generated texts in defines.pri ...
```

it indicates that at least the failure is not from my side ...
the actual build process (which has correct compile flags) must be initialized by some other entry, then I found [Unreal official qtcreator guide](https://dev.epicgames.com/documentation/en-us/unreal-engine/how-to-set-up-qt-creator-for-ue4?application_version=4.27) said that qmake step should be removed from build step, 
which left "make" as the only step required to build, so UE4 does not only provide a broken CMakeLists.txt,
they also generated a (almost not) broken qtcreator project ... Fantastic.


since Qtcreator project does not come with correct flags configured, it's no better than my Neovim,
so I wonder if it's possible to get compile_commands.json , that's another WTF...

a [forum thread](https://forums.unrealengine.com/t/get-compile-commands-json/433389/3) said 4.24 
supports GenerateClangDatabase command , but 4.24 release notes already removed from unreal website, 
I can't read what command/commit provides this feature, great...
since I already read the UBT build command in Build.sh, I think it should be easy to figure out how to call 
it to generate compile_commands.json, right ?

```bash
$HOME/project/UnrealEngine/Engine/Binaries/DotNET/UnrealBuildTool.exe -mode=GenerateClangDatabase $PWD/demo1.uproject  
permission denied: /home/comicfans/project/UnrealEngine/Engine/Binaries/DotNET/UnrealBuildTool.exe
```

WTF ?
```bash
file $HOME/project/UnrealEngine/Engine/Binaries/DotNET/UnrealBuildTool.exe
PE32 executable (console) Intel 80386 Mono/.Net assembly, for MS Windows, 3 sections
```
but why Unreal Engine build can run this? Search under 
```Engine/Build/BatchFiles/Linux``` I found SetupMono.sh/SetupEnvironment.sh
reading them shows that Build.sh will setup Mono before calling UnrealBuildTool.exe, so give it a try:  
([this link](https://gist.github.com/chillpert/1a76ae8e9cfafb36d3bf9e343d32fedc) provides some useful information on how to feed the command line arguments, but it said that he/she can't get GenerateClangDatabase work on 4.27 )

```
$HOME/project/UnrealEngine/Engine/Build/BatchFiles/Linux/Build.sh -mode=GenerateClangDatabase demo1.uproject  

ERROR: No platforms specified for target
```

```bash
$HOME/project/UnrealEngine/Engine/Build/BatchFiles/Linux/Build.sh "/?"  
ERROR: No platforms specified for target

$HOME/project/UnrealEngine/Engine/Build/BatchFiles/Linux/Build.sh -help
ERROR: No platforms specified for target

$HOME/project/UnrealEngine/Engine/Build/BatchFiles/Linux/Build.sh --help
ERROR: No platforms specified for target
```
```

what can I say? a command line tool, without any F**KING help message? 
at least there's source code ...

```

```bash
rg "No platforms specified for target"
Engine/Source/Programs/UnrealBuildTool/Configuration/TargetDescriptor.cs
278:                            throw new BuildException("No platforms specified for target");

```

```csharp
UnrealTargetPlatform ParsedPlatform;
					if(UnrealTargetPlatform.TryParse(InlineArguments[0], out ParsedPlatform))
					{
						Log.TraceVerbose("add platform:"+ParsedPlatform);
						Platforms.Add(ParsedPlatform);
						for(int InlineArgumentIdx = 1; InlineArgumentIdx < InlineArguments.Length; InlineArgumentIdx++)
						{
							Platforms.Add(UnrealTargetPlatform.Parse(InlineArguments[InlineArgumentIdx]));
						}
						continue;
					}
```

since I already modified Log to print everything, it easily shows that
```
Running command : Engine/Binaries/DotNET/UnrealBuildTool.exe -mode=GenerateClangDatabase demo1.uproject
VERBOSE:     Registering build platform: UnrealBuildTool.MacPlatformFactory
VERBOSE:         Registering build platform: Mac - buildable: True
VERBOSE:     Registering build platform: UnrealBuildTool.TVOSPlatformFactory
VERBOSE:         Registering build platform: TVOS - buildable: True
VERBOSE:     Registering build platform: UnrealBuildTool.AndroidPlatformFactory
VERBOSE:         Registering build platform: Android - buildable: False
VERBOSE:     Registering build platform: UnrealBuildTool.HoloLensPlatformFactory
VERBOSE:         Registering build platform: HoloLens - buildable: False
VERBOSE:     Registering build platform: UnrealBuildTool.IOSPlatformFactory
VERBOSE:         Registering build platform: IOS - buildable: True
VERBOSE:     Registering build platform: UnrealBuildTool.LinuxPlatformFactory
VERBOSE:         Registering build platform: Linux - buildable: True
VERBOSE:         Registering build platform: LinuxAArch64 - buildable: True
VERBOSE:     Registering build platform: UnrealBuildTool.LuminPlatformFactory
VERBOSE:         Registering build platform: Lumin - buildable: False
VERBOSE:     Registering build platform: UnrealBuildTool.WindowsPlatformFactory
VERBOSE:         Registering build platform: Win64 - buildable: True
VERBOSE:         Registering build platform: Win32 - buildable: True

```

let's try it stupidly:

```
$HOME/project/UnrealEngine/Engine/Build/BatchFiles/Linux/Build.sh -mode=GenerateClangDatabase demo1.uproject Linux
ERROR: No configurations specified for target

```
ok ... then ... 
```
rg "No configurations specified for target"
Engine/Source/Programs/UnrealBuildTool/Configuration/TargetDescriptor.cs
282:                            throw new BuildException("No configurations specified for target");

```

```csharp
UnrealTargetConfiguration ParsedConfiguration;
if(Enum.TryParse(InlineArguments[0], true, out ParsedConfiguration))
                                        {
                                                Log.TraceVerbose("add configraution:"+ParsedConfiguration);
                                                Configurations.Add(ParsedConfiguration);
                                                for(int InlineArgumentIdx = 1; InlineArgumentIdx < InlineArguments.Length; InlineArgumentIdx++)
                                                {
                                                        string InlineArgument = InlineArguments[InlineArgumentIdx];
                                                        if(!Enum.TryParse(InlineArgument, true, out ParsedConfiguration))
                                                        {
                                                                throw new BuildException("Invalid configuration '{0}'", InlineArgument);
                                                        }
                                                        Configurations.Add(ParsedConfiguration);
                                                }
                                                continue;
                                        }
```
```bash
rg "enum UnrealTargetConfiguration"
Engine/Source/Programs/UnrealBuildTool/Configuration/UEBuildTarget.cs
577:    public enum UnrealTargetConfiguration
```
```csharp
public enum UnrealTargetConfiguration
        {
                /// <summary>
                /// Unknown
                /// </summary>
                Unknown,

                /// <summary>
                /// Debug configuration
                /// </summary>
                Debug,

                /// <summary>
                /// DebugGame configuration; equivalent to development, but with optimization disabled for game modules
                /// </summary>
                DebugGame,

                /// <summary>
                /// Development configuration
                /// </summary>
                Development,

```
ok , so seems that we should use "Development" as configuration... before feed this argument, Let's also check how it handle these arguments:

```csharp
for (int ArgumentIndex = 0; ArgumentIndex < Arguments.Count; ArgumentIndex++)
			{
					
				string Argument = Arguments[ArgumentIndex];
				if(Argument.Length > 0 && Argument[0] != '-')
				{
					Log.TraceVerbose("parse:"+Argument);
					// Mark this argument as used. We'll interpret it as one thing or another.
					Arguments.MarkAsUsed(ArgumentIndex);

					// Check if it's a project file argument
					if(Argument.EndsWith(".uproject", StringComparison.OrdinalIgnoreCase))
					{
						FileReference NewProjectFile = new FileReference(Argument);
						if(ProjectFile != null && ProjectFile != NewProjectFile)
						{
							throw new BuildException("Multiple project files specified on command line (first {0}, then {1})", ProjectFile, NewProjectFile);
						}
						ProjectFile = new FileReference(Argument);
						continue;
					}

					// Split it into separate arguments
					string[] InlineArguments = Argument.Split('+');

					// Try to parse them as platforms
					UnrealTargetPlatform ParsedPlatform;
					if(UnrealTargetPlatform.TryParse(InlineArguments[0], out ParsedPlatform))
					{
						Log.TraceVerbose("add platform:"+ParsedPlatform);
						Platforms.Add(ParsedPlatform);
						for(int InlineArgumentIdx = 1; InlineArgumentIdx < InlineArguments.Length; InlineArgumentIdx++)
						{
							Platforms.Add(UnrealTargetPlatform.Parse(InlineArguments[InlineArgumentIdx]));
						}
						continue;
					}

					// Try to parse them as configurations
					UnrealTargetConfiguration ParsedConfiguration;
					if(Enum.TryParse(InlineArguments[0], true, out ParsedConfiguration))
					{
						Log.TraceVerbose("add configraution:"+ParsedConfiguration);
						Configurations.Add(ParsedConfiguration);
						for(int InlineArgumentIdx = 1; InlineArgumentIdx < InlineArguments.Length; InlineArgumentIdx++)
						{
							string InlineArgument = InlineArguments[InlineArgumentIdx];
							if(!Enum.TryParse(InlineArgument, true, out ParsedConfiguration))
							{
								throw new BuildException("Invalid configuration '{0}'", InlineArgument);
							}
							Configurations.Add(ParsedConfiguration);
						}
						continue;
					}

					// Otherwise assume they are target names
					TargetNames.AddRange(InlineArguments);
				}
			}
```

so they don't parse arguments with positional argument name, just blindly assume they should be one of "platform" "configuration" and "target name"...
I wonder who can understand how to use this command line without reading the source code?

```
$HOME/project/UnrealEngine/Engine/Build/BatchFiles/Linux/Build.sh -mode=GenerateClangDatabase $PWD/demo1.uproject  Linux Development demo1

ERROR: Clang must be installed in order to build this target.
```

alright, another WTF ...
```bash
rg "must be installed in order to build this target" 

Engine/Source/Programs/UnrealBuildTool/Platform/Windows/VCEnvironment.cs
491:                            throw new BuildException("{0}{1} must be installed in order to build this target.", WindowsPlatform.GetCompilerName(Compiler), String.IsNullOrEmpty(CompilerVersion)? "" : String.Format(" ({0})", CompilerVersion));
514:                                    throw new BuildException("{0}, {1}, or {2} must be installed in order to build this target.", WindowsPlatform.GetCompilerName(WindowsCompiler.VisualStudio2019), WindowsPlatform.GetCompilerName(WindowsCompiler.VisualStudio2017), WindowsPlatform.GetCompilerName(WindowsCompiler.VisualStudio2022));
541:                                    throw new BuildException("Windows SDK{0} must be installed in order to build this target.", String.IsNullOrEmpty(WindowsSdkVersion) ? "" : String.Format(" ({0})", WindowsSdkVersion));

```

why, a Linux build will involve VCEnvironment ?
since UnrealBuildTools is so mystery, I decided to modify Build.sh, compile it
every time, so I can print tracing here and there to check its behavior ...

in ```Engine/Source/Programs/UnrealBuildTool/Modes/GenerateClangDatabase.cs```
```csharp
					// Find the location of the compiler
					VCEnvironment Environment = VCEnvironment.Create(WindowsCompiler.Clang, Target.Platform, Target.Rules.WindowsPlatform.Architecture, null, Target.Rules.WindowsPlatform.WindowsSdkVersion, null);
					FileReference ClangPath = FileReference.Combine(Environment.CompilerDir, "bin", "clang++.exe");

```
to generate compile_commands.json, it tries to find windows specified
config to locate clang... but all compile_commands based tool only cares 
about the arguments, not the compile exe path ... after replacing this useless clang path logic with a string literal , I finally got GenerateClangDatabase finish running, seems generated the file under .qtc_clangd folder in project dir
then load it with clangd, and open a cpp file
```
Exactly one of [UE_BUILD_DEBUG UE_BUILD_DEVELOPMENT UE_BUILD_TEST UE_BUILD_SHIPPING] should be defined to be 1
```

Fantastic, the UnrealBuildTools do generate a compile_commands.json, but the flags required to success compile, still living
int Intermediate file
```./Intermediate/Build/Linux/B4D820EA/UE4Editor/Development/demo1/Definitions.demo1.h```

so this compile_commands.json is useless... 

since this project can be built with UnrealBuildTool, so it must have correct
build flags, somewhere. so with another round google, I found [this blog](https://www.gamedeveloper.com/programming/working-with-ue4-on-linux-using-qt-creator),  shows that the target to make is "${project_name}Editor", 
so with this make command, I can finally read the C++ build command

```
/home/comicfans/project/UnrealEngine/Engine/Extras/ThirdPartyNotUE/SDKs/HostLinux/Linux_x64/v19_clang-11.0.1-centos7/x86_64-unknown-linux-gnu/bin/clang++  @"/home/comicfans/project/unreal/demo1/Intermediate/Build/Linux/B4D820EA/UE4Editor/Development/demo1/demo1.cpp.o.rsp"
```

let's check its contents:
``` -c -pipe -nostdinc++ -IThirdParty/Linux/LibCxx/include/ -IThirdParty/Linux/LibCxx/include/c++/v1 -Wall -Werror -Wsequence-point -Wdelete-non-virtual-dtor -fno-math-errno -fno-rtti -mssse3 -fvisibility-ms-compat -fvisibility-inlines-hidden -fcolor-diagnostics -fdiagnostics-absolute-paths -Wno-unused-private-field -Wno-tautological-compare -Wno-undefined-bool-conversion -Wno-unused-local-typedef -Wno-inconsistent-missing-override -Wno-undefined-var-template -Wno-unused-lambda-capture -Wno-unused-variable -Wno-unused-function -Wno-switch -Wno-unknown-pragmas -Wno-invalid-offsetof -Wno-gnu-string-literal-operator-template -Wshadow -Wundef -gdwarf-4 -ggnu-pubnames -O2 -fPIC -ftls-model=local-dynamic -fexceptions -DPLATFORM_EXCEPTIONS_DISABLED=0 -D_LINUX64 -target x86_64-unknown-linux-gnu --sysroot="/home/comicfans/project/UnrealEngine/Engine/Extras/ThirdPartyNotUE/SDKs/HostLinux/Linux_x64/v19_clang-11.0.1-centos7/x86_64-unknown-linux-gnu" -I"." -I"/home/comicfans/project/unreal/demo1/Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/demo1" -I"/home/comicfans/project/unreal/demo1/Source" -I"Runtime" -I"Runtime/TraceLog/Public" -I"Runtime/Core/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/CoreUObject" -I"Runtime/CoreUObject/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/Engine" -I"Runtime/Engine/Classes" -I"Runtime/Engine/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/NetCore" -I"Runtime/Net" -I"Runtime/Net/Core/Classes" -I"Runtime/Net/Core/Public" -I"Runtime/ApplicationCore/Public" -I"Runtime/RHI/Public" -I"Runtime/Json/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/SlateCore" -I"Runtime/SlateCore/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/InputCore" -I"Runtime/InputCore/Classes" -I"Runtime/InputCore/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/Slate" -I"Runtime/Slate/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/ImageWrapper" -I"Runtime/ImageWrapper/Public" -I"Runtime/Messaging/Public" -I"Runtime/MessagingCommon/Public" -I"Runtime/RenderCore/Public" -I"Runtime/Analytics" -I"Runtime/Analytics/AnalyticsET/Public" -I"Runtime/Analytics/Analytics/Public" -I"Runtime/Sockets/Public" -I"Runtime/Net/Common/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/AssetRegistry" -I"Runtime/AssetRegistry/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/EngineMessages" -I"Runtime/EngineMessages/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/EngineSettings" -I"Runtime/EngineSettings/Classes" -I"Runtime/EngineSettings/Public" -I"Runtime/SynthBenchmark/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/Renderer" -I"Runtime/Renderer/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/GameplayTags" -I"Runtime/GameplayTags/Classes" -I"Runtime/GameplayTags/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/DeveloperSettings" -I"Runtime/DeveloperSettings/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/PacketHandler" -I"Runtime/PacketHandlers" -I"Runtime/PacketHandlers/PacketHandler/Classes" -I"Runtime/PacketHandlers/PacketHandler/Public" -I"Runtime/PacketHandlers/ReliabilityHandlerComponent/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/AudioPlatformConfiguration" -I"Runtime/AudioPlatformConfiguration/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/MeshDescription" -I"Runtime/MeshDescription/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/StaticMeshDescription" -I"Runtime/StaticMeshDescription/Public" -I"Runtime/PakFile/Public" -I"Runtime/RSA/Public" -I"Runtime/NetworkReplayStreaming" -I"Runtime/NetworkReplayStreaming/NetworkReplayStreaming/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/PhysicsCore" -I"Runtime/PhysicsCore/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/Chaos" -I"Runtime/Experimental" -I"Runtime/Experimental/Chaos/Public" -I"Runtime/Experimental/ChaosCore/Public" -I"ThirdParty/Intel" -I"Runtime/Experimental/Voronoi/Public" -I"ThirdParty" -I"Runtime/SignalProcessing/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/AudioExtensions" -I"Runtime/AudioExtensions/Public" -I"Runtime/AudioMixerCore/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/PropertyAccess" -I"Runtime/PropertyAccess/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/UnrealEd" -I"Editor" -I"Programs/UnrealLightmass/Public" -I"Developer/Android/AndroidDeviceDetection/Public/Interfaces" -I"Editor/UnrealEd/Classes" -I"Editor/UnrealEd/Public" -I"Developer" -I"Developer/DirectoryWatcher/Public" -I"Editor/Documentation/Public" -I"Runtime/Projects/Public" -I"Runtime/SandboxFile/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/EditorStyle" -I"Editor/EditorStyle/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/SourceControl" -I"Developer/SourceControl/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/UnrealEdMessages" -I"Editor/UnrealEdMessages/Classes" -I"Editor/UnrealEdMessages/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/GameplayDebugger" -I"Developer/GameplayDebugger/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/BlueprintGraph" -I"Editor/BlueprintGraph/Classes" -I"Editor/BlueprintGraph/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/EditorSubsystem" -I"Editor/EditorSubsystem/Public" -I"Runtime/Online" -I"Runtime/Online/HTTP/Public" -I"Runtime/UnrealAudio/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/FunctionalTesting" -I"Developer/FunctionalTesting/Classes" -I"Developer/FunctionalTesting/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/AutomationController" -I"Developer/AutomationController/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/Localization" -I"Developer/Localization/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/AudioEditor" -I"Editor/AudioEditor/Classes" -I"Editor/AudioEditor/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/AudioMixer" -I"Runtime/AudioMixer/Classes" -I"Runtime/AudioMixer/Public" -I"Developer/TargetPlatform/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/LevelEditor" -I"Editor/LevelEditor/Public" -I"Developer/Settings/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/IntroTutorials" -I"Editor/IntroTutorials/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/HeadMountedDisplay" -I"Runtime/HeadMountedDisplay/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/VREditor" -I"Editor/VREditor" -I"Editor/VREditor/Public" -I"Editor/CommonMenuExtensions/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/Landscape" -I"Runtime/Landscape/Classes" -I"Runtime/Landscape/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/PropertyEditor" -I"Editor/PropertyEditor/Public" -I"Editor/ActorPickerMode/Public" -I"Editor/SceneDepthPickerMode/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/DetailCustomizations" -I"Editor/DetailCustomizations/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/ClassViewer" -I"Editor/ClassViewer/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/GraphEditor" -I"Editor/GraphEditor/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/StructViewer" -I"Editor/StructViewer/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/ContentBrowser" -I"Editor/ContentBrowser/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/ContentBrowserData" -I"Editor/ContentBrowserData/Public" -I"Developer/CollectionManager/Public" -I"Runtime/NetworkFileSystem/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/UMG" -I"Runtime/UMG/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/MovieScene" -I"Runtime/MovieScene/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/TimeManagement" -I"Runtime/TimeManagement/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/MovieSceneTracks" -I"Runtime/MovieSceneTracks/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/AnimationCore" -I"Runtime/AnimationCore/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/PropertyPath" -I"Runtime/PropertyPath/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/NavigationSystem" -I"Runtime/NavigationSystem/Public" -I"Developer/MeshBuilder/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/MaterialShaderQualitySettings" -I"Runtime/MaterialShaderQualitySettings/Classes" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/InteractiveToolsFramework" -I"Runtime/Experimental/InteractiveToolsFramework/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/ToolMenusEditor" -I"Editor/ToolMenusEditor/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/ToolMenus" -I"Developer/ToolMenus/Public" -I"Editor/AssetTagsEditor/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/AddContentDialog" -I"Editor/AddContentDialog/Public" -I"Developer/MeshUtilities/Public" -I"Developer/MeshMergeUtilities/Public" -I"Developer/HierarchicalLODUtilities/Public" -I"Developer/MeshReductionInterface/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/AssetTools" -I"Developer/AssetTools/Public" -I"Editor/KismetCompiler/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/GameplayTasks" -I"Runtime/GameplayTasks/Classes" -I"Runtime/GameplayTasks/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/AIModule" -I"Runtime/AIModule/Public" -I"Runtime/AIModule/Classes" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/Kismet" -I"Editor/Kismet/Classes" -I"Editor/Kismet/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/ClothingSystemRuntimeInterface" -I"Runtime/ClothingSystemRuntimeInterface/Public" -I"../Plugins/Runtime/PhysXVehicles/Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/PhysXVehicles" -I"../Plugins/Runtime/PhysXVehicles/Source" -I"../Plugins/Runtime/PhysXVehicles/Source/PhysXVehicles/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/AnimGraphRuntime" -I"Runtime/AnimGraphRuntime/Public" -I"../Plugins/Runtime/PhysXVehicles/Source/ThirdParty" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/AugmentedReality" -I"Runtime/AugmentedReality/Public" -I"../Intermediate/Build/Linux/B4D820EA/UE4Editor/Inc/MRMesh" -I"Runtime/MRMesh/Public" -I"/home/comicfans/project/UnrealEngine/Engine/Source/ThirdParty/PhysX3/PxShared/include" -I"/home/comicfans/project/UnrealEngine/Engine/Source/ThirdParty/PhysX3/PxShared/include/cudamanager" -I"/home/comicfans/project/UnrealEngine/Engine/Source/ThirdParty/PhysX3/PxShared/include/filebuf" -I"/home/comicfans/project/UnrealEngine/Engine/Source/ThirdParty/PhysX3/PxShared/include/foundation" -I"/home/comicfans/project/UnrealEngine/Engine/Source/ThirdParty/PhysX3/PxShared/include/pvd" -I"/home/comicfans/project/UnrealEngine/Engine/Source/ThirdParty/PhysX3/PxShared/include/task" -I"/home/comicfans/project/UnrealEngine/Engine/Source/ThirdParty/PhysX3/PhysX_3.4/Include" -I"/home/comicfans/project/UnrealEngine/Engine/Source/ThirdParty/PhysX3/PhysX_3.4/Include/cooking" -I"/home/comicfans/project/UnrealEngine/Engine/Source/ThirdParty/PhysX3/PhysX_3.4/Include/common" -I"/home/comicfans/project/UnrealEngine/Engine/Source/ThirdParty/PhysX3/PhysX_3.4/Include/extensions" -I"/home/comicfans/project/UnrealEngine/Engine/Source/ThirdParty/PhysX3/PhysX_3.4/Include/geometry" -I"/home/comicfans/project/UnrealEngine/Engine/Source/ThirdParty/PhysX3/APEX_1.4/include" -I"/home/comicfans/project/UnrealEngine/Engine/Source/ThirdParty/PhysX3/APEX_1.4/include/clothing" -I"/home/comicfans/project/UnrealEngine/Engine/Source/ThirdParty/PhysX3/APEX_1.4/include/nvparameterized" -I"/home/comicfans/project/UnrealEngine/Engine/Source/ThirdParty/PhysX3/APEX_1.4/include/legacy" -I"/home/comicfans/project/UnrealEngine/Engine/Source/ThirdParty/PhysX3/APEX_1.4/include/PhysX3" -I"/home/comicfans/project/UnrealEngine/Engine/Source/ThirdParty/PhysX3/APEX_1.4/common/include" -I"/home/comicfans/project/UnrealEngine/Engine/Source/ThirdParty/PhysX3/APEX_1.4/common/include/autogen" -I"/home/comicfans/project/UnrealEngine/Engine/Source/ThirdParty/PhysX3/APEX_1.4/framework/include" -I"/home/comicfans/project/UnrealEngine/Engine/Source/ThirdParty/PhysX3/APEX_1.4/framework/include/autogen" -I"/home/comicfans/project/UnrealEngine/Engine/Source/ThirdParty/PhysX3/APEX_1.4/shared/general/RenderDebug/public" -I"/home/comicfans/project/UnrealEngine/Engine/Source/ThirdParty/PhysX3/APEX_1.4/shared/general/PairFilter/include" -I"/home/comicfans/project/UnrealEngine/Engine/Source/ThirdParty/PhysX3/APEX_1.4/shared/internal/include" -x c++ -std=c++14 -include "/home/comicfans/project/unreal/demo1/Intermediate/Build/Linux/B4D820EA/demo1Editor/Development/Engine/SharedPCH.Engine.ShadowErrors.h" -include "/home/comicfans/project/unreal/demo1/Intermediate/Build/Linux/B4D820EA/UE4Editor/Development/demo1/Definitions.demo1.h" -include "/home/comicfans/project/unreal/demo1/Intermediate/Build/Linux/B4D820EA/UE4Editor/Development/demo1/Definitions.h" -o "/home/comicfans/project/unreal/demo1/Intermediate/Build/Linux/B4D820EA/UE4Editor/Development/demo1/demo1.cpp.o" "/home/comicfans/project/unreal/demo1/Source/demo1/demo1.cpp" -MD -MF"/home/comicfans/project/unreal/demo1/Intermediate/Build/Linux/B4D820EA/UE4Editor/Development/demo1/demo1.cpp.d"

```

alright, the UnrealBuildTool will set these important flag in generated header (Definitions.demo1.h/Definitions.h), 
which will be included by "-include" flag,  which compile_commands.json generated by GenerateClangDatabase command lacks... 
but what drives me more crazy is that,  after spending hours on this, I eventually found that, Unreal already created a 
ready-to-use compile_commands.json, under project .vscode/ folder (with a project-name suffix)! so what's the point of GenerateClangDatabase command?


