During my job at some company, I got a very project, boss decide to stop using their more than 20 years 
version control system, IBM clearcase, and they want to preserve their development history as much as possible.
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
(which called a repository). and remember everything changed during your development even after
editor closing. Of course it isn't so intelligent, you have to use its client
tool at some time (usually when you finish some meaningful work) to tell it
'please remember state right now'. and VCS will record a 'version'.
(this procedure usually called 'commit') when you want to go back to early state,
just tell VCS a version to view, and you will have a history snapshot. 

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

clearcase behaviors much like cvs, file evoluted independently, and there'll
