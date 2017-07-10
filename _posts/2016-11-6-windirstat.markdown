---
layout:     post
title:      "Disk Usage analyze in VERY BIG VCS migration"
subtitle:   "Blog"
date:       2016-11-06 12:00:00
author:     "comicfans"
tags:
    - git
    - vcs
---

Recently my company's VCS is migrating From ClearCase to Git, but old ClearCase repo contains not only software codebase , but also many docs/3rd libs/binaries, this leads 20G 60k+ files in repo! Even Git-LFS provides big binary file support for git,  but how can I quickly decide which files should be handled by Git-LFS? I need a disk usage anlyaze tool ,but only working on specified set of files (only analyze unstaged files, or only analyze staged files)

Since most Disk Usage Anaylze tool didn't provide this function, I decide to hack on existing one.

* jdiskusage : Java is easy to Hack! but... not open source.
* qdirstat(formly kdirstat) : get rid of kde libs, so it's easier to port! but it use unix file api instead of Qt… so not easy to port to windows (which I'm working on)
* windirstat : Written in MFC/Win32 API which I'm not familiar with, but it windirstat provides useful feature which alternatives didn't have: catelog file size by file type.

After half day hack and debug, I've created a modified version of windirstat, if you select a folder as anaylze target and it contains a file.list file, following anaylze only works on these files.file.list contains one file relative path (to anaylze target) per line. you can generate this file to analyze unstaged file by :

```bash
git status --porcelain --untracked-files=all | grep ?? | cut -d " " -f 2 > file.list
```

or 

```bash
git ls-tree --name-only -r HEAD > file.list
```

to analyze git already tracked files. 

cli generated list seems more complicated ,but filter files by cli is more flexible than hard code git action. for example you can analyze Git-LFS tracked files by 

```bash
git lfs ls-tree | cut -d " " -f 3 > file.list
```




### C++ API design 


Windirstat use ATL CFileFind to iterate children of folder, which a wrapper for FindFirstFile/FindNextFile, but its design is questionable. you still needs to call FindFile before calling FindNextFile. Everything appears same except that replace WIN32_FIND_DATA with CFileFind. 

before calling FindFirst, your CFileFind is invalid object

C++ introduce RAII idom, 






VCS takes important rule in software development today, better tools gives better workflow, but as my working experience, Companies didn't makes VCS works as it should be.(mostly)





### 1st company

J2EE development with CVS but never create tag for product release. Nobody knows which version is running on server . And developer directly copy local compiled class file to final running server, nobody knows code running on server is actually CVS contains.  Code migrate to git with my help , but they decide to move code back to SVN when I turnover .Maybe central control makes them feel "safer", but actually it only increase 

### 2nd company

C/C++ developmnt with SVN,  migrated to git as I suggested, but manager decide to keep all history in SVN, so we develop all our code in git branch (but always use rebase to keep linear history), then dcommit back to SVN.


### 3rd company

OMG ClearCase ! the very first commit appears at 1994!? 60k files inside whole repository, even including compiled dll/lib/pdb ... with expenrise in using CVS, I should say file basis VCS is a nightmare. but worse than that, my task is miragrate this repository to git, with history reserved.

