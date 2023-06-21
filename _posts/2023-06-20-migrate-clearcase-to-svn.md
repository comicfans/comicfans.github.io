During my job at some company, I got a very project, boss decide to stop using their more than 20 years 
version control system, IBM clearcase to cost down (will stop clearcase service at deadline!),
and they want to preserve their development history as much as possible.
since I have experience of using cvs/svn/git, I'm glade to take this challenge. Finally I successfully
convert this super-big clearcase history to svn repo, with all file development history preserved. 
It's very interesting experience, I hope to share them here (It's already more than 5 years job before,
I think this won't hurt anybody)

   
What is version control system, why developer need this.

in this section I will give a quick view for VCS(short for Version-Control-System), if you already know
what VCS is , you can just skip this section

During software development (even the simplest ones), developers may face
'What did I changed? Why it became incorrect now?' problem (of course not you),
at that time they may want 'time machine' to take them back to 2 days ago.
and VCS is such this time machine. you can see it as a infinite undo-redo
history, it manage a folder which contains all dir/files needed to be remembered,
(which called a repository). And remember everything changed during your development even after
editor closing. Of course it isn't so intelligent, you have to use its client
tool at some time (usually when you finish some meaningful work) to tell it
'please remember state right now'. And VCS will record a 'version'.
(this procedure usually called 'commit') when you want to go back to early state,
just tell VCS a version to view, and you will have a history snapshot. 

VCS also allow none-linear history, means history timeline may divided at some time point,
and individual timeline evolute independently, history form a 'tree',
Usually this function is called a 'branch', just like a branch of the tree.
For example you may working on a new feathers branch with lots of unstable changes,
but another production branch only keep the most stable changes.

another important usage of VCS is for cooperate development ,
30 developers who're working on one software need a easy way to share
works to each other, if two people are modifying same file, their work
will conflict, this also requires VCS to help management. usually it will tell
developers changed contents by others, and force developers to resolve the conflict. 
some VCS also support user authorization and permission control, to control
who can access what, to ease management. 

of course VCS is not a hard requirements, I also heard some company just put 
source code on a shared folder, let developers modify them as they wish, 
and you can imagine that if someone delete source code by accident, everyone
is doomed.

early VCS records individual history for individual file, you may think file
as different timelines, file A version 2 has nothing to do with file B version 1.
since different file's history evolute independently, such VCS usually provide
a 'snapshot all' function, which fixed all files version as a single 'tag'. 
for example different team complete modifying different set of files, a 
overall tag will have a fixed version of all files (CVS and IBM clearcase)

some VCS choose time-based solution, they record version for whole repository,
for example svn will increase whole repository version for every changeset, ordered by
time every changeset is made.  I use changeset here because changeset not limit to one file modification,
multi related changes can be treat as a atomic changeset, when repository version
increase, it will including all changes of one changeset. svn (dir) history behavior
like a single timeline, when two user modify completely different set of files
and submit simutinously , svn will force second submit version based on first
submit version, even when second user don't see first one's work before he submit.
for the good part, when users modify different files, they never need to
manual operate (because no file conflict will happen), they just throw their work
to svn just like their changeset happen one after another. 
but for the bad part, earlier submit changeset will be 'magically inserted'
before later submit changeset, just like the later one is based on earlier ones
but this is actually not the case! say later commit change file A , which depends
on file B, but another user which changed file B to a incompatible state and
submit earlier, the later commit user won't know file B already changed 
until he submit (because such changeset submit may just 1 second before later one)
now repository contains a incompatible A and B, without user notice.

People quickly realized that there're intra dependencies between files,
if file A version 2 must depend on file B version 1, it's meaningless to just 
record file A version 2 (without knowing that file B must be version 1 at that time)

now most popular VCS is git, it does not only record version for whole repository,
but also strictly treat the whole state of all files as the version contents,
which means if user commit file A which requires exactly old state of other files,
then such version will be a snapshot of changed file A and all non-changed other files,
exactly same as user commit. This behavior greatly improved development experience,
because every commit is the exactly snapshot of whole repository, no 'magic insert'
will happen and break your work silently. When user need to share their work
they must do a manually 'merge' (even they're modifying completely different set of files). 
it seems to be a extra work, but there's nothing to do if modified files not conflict,
plus that user can be noticed that other parts of file changed. 

another advantage of git is that it's distributed, means user can experimental
lots of stuff locally without waiting for slow network or harming final repository.
there're lots of post for this topic, I will skip it.


Now back to my task, how clearcase worked? 

disclaimer: most of these section is from my memory, since clearcase is a 
propriety software,expensive and hard to be deployed locally, so I can't verify
every behavior. 

clearcase behaviors much like cvs, file evolute independently, all files default
live in 'main' branch, you can create branches, but branch doesn't require 
all files exist (you may have branch1 which contains file1, but branch2 only contains file2)

so it's checkout (which is called spec) behaves just like route table or SQL

dir1/subdir1: branch1   -----> you have these files development in branch1 
dir2/subdir2: branch2   -----> you have these files development in branch2
*: main                 -----> other files left as default 'main' branch

it will pick dir1/subdir1 contents from branch1, dir2/subdir2 from branch2, and not specified files will using ones from main branch
but why should you checkout different branch for different files? Isn't it confusing?
I think clearcase may suppose developers should have some of files evolute 
in some branch, but other files kept as original (which we have seen in previous section, such concept has some limitation).
another possible answer is that different team may using same repo with different naming/development convention,
nobody can force a unique branch convention for all the development, thus when
you need to combine their work together, checkout different branch for different files
is the only (quickly) solution.

you may find problem here, such spec don't ensure exactly same version of two runs,
because file in branch1/branch2 may change after you checkout the spec!

only the checkout local copy has a consist view. clearcase also provide tag function,
using local checkout copy, clearcase can create a fixed view of all files at specified version.
and such tag will be a unchanged snapshot view (but if you're using checkout spec
to pick some files from branch instead of tag, such files still won't be consist)

clearcase have some concept to help divide individual repo to different top level
containers which is called a "VOB", different VOB can be viewed as different repository,
since they can have different permission control. I think different VOBs should
hold completely independent codebase, but for my task, source code
spread across 7 vobs (and clearcase also allow you to pick files from multiply vobs into same dir),
I think such concept didn't help to split codebase.


after comparing basic concept and available convert tool ,  I think svn match clearcase
mostly, for the reasons:

1. there exists a cc2svn script to convert clearcase repo to svn, simplify the convert logic
2. every file of clearcase live in a branch, a tag pick file from specified branch(or tag),
   and branch/tag in svn can be viewed as a folder, clearcase tag pick procedure can be viewed
   as svn copy from its branch folder to destination branch/tag dir
3. clearcase don't force overall file in one branch/tag, every file evolute independently,
   although svn have global version, but branches is just dir under branches dir,  
   different dir can have their own history (as long as you don't treat their root as overall dir)
   so clearcase per-branch history can be placed under some old_migrate dir, so these old clearcase branches (
   which only contains history of part of files) won't confuse user

I've also considered git conversion, but for two reasons I don't take this approach

1. git don't have permission control, any user can access repository can view all contents,
   but svn allow user authorization and permission control. our company needs permission control

2. clearcase branch can be mapped to git branches too,
   (as long as you always start empty branch and only contain files within this branch)
   but git branch usually shown as top level object, hundreds old clearcase history branch 
   (which only contains history of parts of files) will confuse user


first challenge : get full clearcase history description

I want to preserve all file history, so history of all files must exist, but 
after trying cc2svn script from github, I realized that it only preserve the files
existed under specified view of local checkout ,
don't including all history of the VOB(files not selected or files already deleted won't appear),
the correct command to dump all history of VOB is 

```

```


it will describe every changes of the VOB, including branch tree, file path, commit message
and much bigger than cc2svn will download.
with this full description, I can download every single version of all files 
cc2svn script said that to start the tool 2 days before to pre-download the history, 
but seems my company's history is much-much bigger, it has 7 VOBS and total revision more than 4000000!
(actually there isn't so many changes, clearcase records version for every single file,
so even you change 100 files at once, it will create 100 revision in total), 

what makes it worse is that my company's firewall rule limits network traffic,
even I'm just downloading clearcase history! clearcase download speed will drop down
after a while, and disconnected frequency, I may miss lots of download contents!
(seems clearcase use udp traffic? I didn't confirm that)

thus I decide to improve the download script, 

1. it need to resume after break or failed command
2. download process must be distributable across different machines, to lower down per-machines's traffic,  and accelerate total speed

finally I use a shared folder share download files, every file using clearcase history path
as its dir so path won't clash, and while downloading, use simple mark file
to record if such file is being processed, or completed, to help resume downloading from interrupted command
and avoid two machines operate one file. with more than a week downloading
(and pingpong with our security team, because I have unusual traffic)
I finally downloaded all the history, and now It's time for the actual convert

svn convert is also very straightforward, you write series of svn import commands
every command record the operate file path, the action, feed this commands
into svn command, then it will construct a repository based on these commands
of course you must ensure the later commands must have corresponding history,
otherwise it will have different history structure. 


because history records is parsed from clearcase VOB log file,
and parse process is very slow and not easy 
for analysis, so I decide to convert these records into database,  
this is required because converting 4000000 commits repo will spend hours and days,
incorrect convert logic just waste too much time. records in database not only
allow me to skip slow parse process, but also filter parts of file/time to create a simplified repo,
and verify its correctness. since this is just a correctness verify process,
I even don't need to put actual
file contents in it, just dump the file version information and the real path of 
my pre-download cache path can help me to verify the contents. 

converting the parsed log into database also brings me interesting experience,
since records are formed by sequence/datetime , so it doesn't matter which
records is imported earlier, that makes parallel parse/import possible. 
usually split files by parts of lines requires parse whole file (to find correct line break)
but we have have a simple hack, just split file by bytes range, and for every
bytes range start, just look ahead to find next valid line header,
(because clearcase log format has fixed header format of records)
so it just need a head seek and a little bytes look ahead.
every process part looks ahead to find next valid line, so different process won't 
overlap each other, and won't miss lines.  
be aware of python GIL, you should use multiprocess instead of thread.


currently the converted svn repo is just a small part of files/history,
every file is dummy text, but enough for me to verify history structure.
with some enhancement to cc2svn script, I can also including the delete/moved file history,
in converted repo, now I can use svn client to view every file history graph,
to verify it's same as graph of clearcase client shown. maybe this can be checked strictly 
by topically sort their history, but I don't have enough time to try , just verify some of them.


improvement of clearcase history

1. reducing duplicate commits

I didn't try to convert 4000000 revisions to svn at once, because there're too many duplicated commits
(remember that 100 file changes in one changeset will create 100 commits?), if possible, I hope 
to 'merge' these commits back as one changeset, that will much improve the final history. 
since commit multiply files in clearcase will have exactly same commit message, I can use this information
to re-construct the history, when commits submit adjacent to each other, and these commits have same comment,
merge them as one changeset, after this process and verification, final svn history can be greatly reduced
to 600000 revisions, less than 1/6 of raw clearcase history, not bad!

2. fix bad comment message

another problem of clearcase history is that it doesn't support unicode, dumped records have messages in all locales,
so I use firefox chardet to guess their original encoding, and for some special case which chardet didn't give correct 
result, I tried multi encoding and record their frequency words as part of guessing procedure, it does not only
get them right, but also correct similar messages.

before finally actual convert, I also need a overall svn dump,
its file contents is still empty, but whole repository history structure won't
be different to final repository, this is just to verify all the generated
svn history is correct and can be constructed correct svn history.

it turns out to be a very good idea, I found that even after reducing history down to 600000 revisions,
and file contents still dummy contents, such dump construct still spend too much time,
since windows filesystem is not friendly to many small files, plus my company has antivirus protection
to future lower down, or even interrupted the import process! 
I have to try linux in virtual machine, but still too slow, I already tried ext4 on a passthrough ssd!
which filesystem and disk can be faster? tmpfs on ram! 
tmpfs using memory as baking store , and will auto swap to disk when capacity exceeds.
so I put the repo in tmpfs, thanks to the 64GB memory, the convert process speedup a lot! 
but I quickly hit another limitation, file number exceeds tmpfs limit, maybe nr_inodes can 
fix it , but I tried another method, just run svnadmin pack endlessly, it will compact 
the repository every 1000 revisions reduce file number, 
and importantly it can operate simutinously when the importing running, 
so I don't need to care about inode exceeds. This approach has only one drawback:
I must save the converted repository before any shutdown/crash…

after some tries, I finally got the all file dummy repository, 
without hitting any problem during construction,
and confirm file history graph appears same as clearcase shown, 


construct clearcase local view from imported svn history

and before the final actual convert, I still need another check,
to confirm branches/tags in clearcase can be correctly generated 
from this dummy history. Because clearcase local view is only a specified version
collection, so it can be viewed as svn 'copy' action, to copy every specified
version from their living branch (because we know the last version of every file,
and we know where we put this file under svn dir) to the final tag dir
the only required input is the clearcase local view description (tell you version
of every file). 

after checking some tags dummy file history same as clearcase history,
I finally switch the dump generate code to read actual file contents
and feed it into svn repo reconstruction, and finally got the svn repo,
containing 600000 revisions, more than 20 years history of every file,
every file has exactly same history structure as clearcase.

last missed part is your local checkout view (tags/branch), without their
version description, you don't know which revision of every file came from.
maybe we can compare file contents to pre-downloaded file contents, but it 
can't assume the file is exactly the revision (file can be identical at different version)
so can't construct exactly same history structure (but latest contents is same)

if you like, it's also possible write a clearcase spec parser, to support the 
'dynamic' checkout logic, just pick files from their branch(of course it can only
include latest changes inside pre-downloaded)

following up tasks: authorization in svn
due to some company policy, we have to use windows system for svn server,
and manage user authorization will be time consuming, since our company use LDAP,
I think this can be done by deliver svn authorization to LDAP. with some 
google, seems that svn can use sasl to do authorization, but sasl + LDAP needs
extra plugins on LDAP server. (I can't understand why this is needed, since I 
also configure JIRA to use LDAP authorization, it only requires a admin username/password,
then I can config which users should be filtered as JIRA accounts),
so I wrote a very simple SASL plugin simpleldap, just filling username
part as ldap bind path (someone suggested this is a security hole, but this
is just enough for my usage), it's here. But unfortunately this code didn't 
get upstream before I left that company. Since I don't have the environment for
testing anymore, I also use intention to improve it.


