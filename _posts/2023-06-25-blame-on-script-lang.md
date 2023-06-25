Disclaimer: this is mostly my complaint at work, shouldn't be considered seriously (some sort of)

I've worked with low-level language before, mostly C/C++ , also have some years
experience of java development. recently I tried rust and go, as you can see,
they're all strong-typed, compiler checked language. I do use script language like 
python and javascript, just for write-once and throw up purpose, never use them
to create serious project. And for some reason, we have to use R language in our work,
for that we need to maintain a R codebase.

Let me give a short introduction of R language: it's a interpreted, weak type, GC language,
it has good support for statistics and data analysis.  The main difference of R and most other
language is that its builtin type are always array, even a single number is just a 
one length array. and all operators are also array based , for example a + b do a element wise
add. 

we use this codebase for some data research, this worked well, and I think R has a killer
feather (for programmer), it's fully interpreted, even for its built-in debugger,
which means even when you're already trap at R built-in debugger , you can recusively 
call into some R code and trap at the breakpoint again. other script language, for example
python, when you trap at breakpoint, then you call the outer function (which contains breakpoint),
it will evulate the result, but won't trap again recusively. for some time consuming debugging,
the code you want to debug may just passed by, but re-run requires much longer time,
R debugger let you breakpoint on the passed by function, and then re-call it to trap immediately.
since this trap can be recusively, you can inspect the function easily, repeatly. This greate
improved the interactive development experience.



And to reuse these R code in other places, we decide to make some of our R logic run
headlessly every day, do some data update logic, suddenly all sort of bugs pop,
while developing and debugging these code, all the F word jump into my brain...

first problem is that when crashing during script mode execution (run with Rscript instead of R console interactive),
R can't show crash stack filename and line number, it just gives a function name call chain like:

```
apply->functiona-> paste-> ...
```

instead of normal script language crash stack
```
file1: line 234: apply
file2: line 456: functiona
file3: line 789: paste
```

This does not make any sense! R console already show full backtrace filename line number and function name, 
why script run have none of this ? I've asked this question on R-devel mailing list, seems nobody cares.
plus that even such simplified function name call chain,
R will omit parts of it! when you have long call chain, your output will be like this:

```
apply->functiona->paste-> ...    functionb -> functionc-> ...
```

yes, the three dots is not omitted by me, it's the output of R script.
R knows what exactly information is , but it won't tell you, you have to do fuzzy match and guess!
it's better than nothing output, but seems more like a joke.

Another approach I tried is the 'dump' function, set dump as error function, it will save
whole running workspace as a file, which can be loaded later for debugging, just like coredump.
but our R data update logic loads lots of data, even the smallest dump will take minutes 
to complete, and saved file is multi-GB, which is not pratical. so we have to repeat running
our code in Rconsole, to find which location the code crashed.

while debugging R crash, it shows another funny behavior: R console do output
filename, line number and function name, but the stack level is incorrect! 
I don't know how this is implemented, at least for other languages, if I want to go to some
stack level shown by stack trace, I just pick filename/line number/function I'm interested at,
enter the corresponding number, then I got that stack. but for R, this never worked,
the number you enter is always one level higher, or lower than shown line, everytime I have to 
guess it, using variable list and source code to confirm I'm at the correct stack location!
and R sometimes do lazy evolute, so the call stack order may be inversed, that makes 
your logic much harder to debug! for example in normal calling order, you call

```R
f(g(h()))
```

h is called first, then g, then f at last.  I call this 'normal' because if view the callsite as dependencies 
DAG,  f depends on g, g depends on h, so the most dependency (h) should be avaiable first,
otherwise other node don't have neccessary input. Any error happened in h should break immediately, 
before later g call (and of course f call), because later node don't have neccessary input.
but in lazy evulate, h call actually happened when the h output is accessed by g call,
and g call actually happened when the g output is accessed by f, so the running order is that f runs first,
it access a variable of g output, which leads g is called, and same thing happened , h is called last!
so the backtrace will show f and g first, but the bug actually happened in h! 
and such lazy evualte implicts another pontential problem, it will hide the buggy logic if that result is
not accessed! your code f seems worked for a long time, makes you think any of its input (g and h) also workes,
but actually g or h never run.


another problem of R is consistence, although its built-in type is array based,
but function based on these concept don't give consist result. for example in other language
you may write 

```
if(a > b) {
    do_something()
}
```

in R the if expression only accept a single value, but R can't tell a or b is single-value or not(single value are just 1 element array),
so it can't verify its correctness ahead of time, you must run to this line to know if it worked or not,
and once correctness does not mean such logic correctness! 
you may think it's not a big deal, just make sure a and b single element variable makes everything work,
but it's not! R logic is array based, code may quickly changed to make a/b any length in some other places, 
leave this if expression invalid. and by default R also don't force crash invalid usage, for example
if a and b are multi-value, such code will trigger R 'warning' you that only first element of array is used
as condition, if you run big codebase, such warning quickly being ignored !



