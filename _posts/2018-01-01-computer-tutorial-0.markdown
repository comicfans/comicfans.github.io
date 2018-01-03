---
layout:     post
title:      "computer tutoial zero"
subtitle:   "Blog"
date:       2018-01-01 11:00:00
author:     "comicfans"
tags:
    - c++
    - computer
    - programming
---



for some people computer seems to be Voodoo, how can you control it to do almost anything for you ? Well actually before you have written even one line of code , you have been a programmer before, don't belive that ? can you tell me the result of 89 + 64 ? well it's 153, but how did you got this 

picturce got a calculator ...

well almost everyone got this forumla:

<pre>
    89
  + 64
  _____
   153
</pre>


picture placeholder


with this method, you can calculate sum of any two integers, no matter how long they are, even you can only remember the sum of two number less than 10.

picture too easy ,don't leave 


Actually, you have not only written a program, but also acted as a computer to execute your own program. So let's take a look into this:

sum of any two number less than 10, which you already know is invariantable, predefined, is called "builtin rules"

continuously adding one digit, using builtin rules, until no more digit left. this is called "procedure", we created a "plus procedure" in previous example

now everything setuped, you gives input 89 and 64 to this plus procedure, and the procedure gives output to you: 153

this is just programming , computer programming works exactly the same way. the computer have some builtin rules predefined, and the whole progress you send your procedure to computer, is just called :

   programming

computer can not understand human language like "continuously adding one digit until no more digit left", you must speak a language which it can understand , so the language you provided your procedure , is called 

   programming language

to learn computer deeply and still easily, I choose

   C language

as our entry point, we will learn more languages for other purpose in following tourial.

our first code ,is to calculate the sum from 1 ~ 5,

lets start!

```C
int result = 0;
result = result+1;
result = result+2;
result = result+3;
result = result+4;
result = result+5;
```
at last, result will be 15
That's it!  simple enough ?  this is a very basic C language block, let's take a overview on this:

* C code blocks is made up by many "statement"
* statement execute one by one
* every statement followed by a  ;

now line by line :

```
int result = 0;
```

this is called a "declaration", a variable which is called "result" appears,and its initial value is 0 . we store result of every step on it.
and int means "integer" ,it act just like integer in math. you can add two integers, just like math.(computer already have builtin rules for integer add)

```
result = result + 1
```
this is a assignment statement,means 
caculate the sum of (result+1) 
and then put it to result. you may think this statement breakup into following parts is eaier to understand:

tempvalue = result +1
result = tempvalue


the right part of assigment is executed first, so you don't need to worry about result may have different values during this statment.



ok ,lets get a more complicate one , get the sume from 1~10!

```C
int result = 0;
result = result+1;
result = result+2;
result = result+3;
result = result+4;
result = result+5;
result = result+6;
result = result+7;
result = result+8;
result = result+9;
result = result+10;
```

a little longer... what if we need to got sum from 1 to 999 ?well ,let's make it easier:


```C
int result = 0;

int current=1;

while(current <=999){
result = result + current;
current = current+1;
}
```

this is called "loop" statement, which means :

* when some condition  


