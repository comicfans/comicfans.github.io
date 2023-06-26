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
leave this if expression invalid. and by default R also don't force crash invalid usage, 
if a and b are multi-value, R 'warning' you that only first element of array is used as condition, 
if you're also printing some other logs, such warning quickly ignored in headless execution.
R also has options to treat these warnings as errors (crash immediately), 
but even the base function in R has such warning (sqrt(-1) produce NAN also be a warning),
not to mention that such warnings can came from any of used library. treat warning as error
can help you quickly find bad usage in interactive usage, but not suitable for a headless run.

another example of inconsistence is how zero sized array is handled, you can define a zero sized array as

```R
zero_sized_array = c()
```

now testing its properties:
```
length(zero_sized_array)
is.null(zero_sized_array)
```
it gives you 0 and TRUE, 

but if we create a none-empty array and pick zero length element out of it, result changed:
```
none_empty_array = c(1,2)
zero_sized_array = none_empty_array[c()]
```
now testing again:
```
length(zero_sized_array)
is.null(zero_sized_array)
```
its length is still zero, but is.null return FALSE !? why they're both zero-sized array 
but didn't have same is.null result? print two variable, it shows that 'c()' is just NULL,
c(1,2)[c()] is 'numeric(0)', they're different. following code
```R
is.null(as.numeric(c()))
```
return FALSE, match second output. 
when comparing function result, c() won't be equal to numeric(0), you have to cast one to another, which is annoying.

another tricky part of R is how paste (concate string together) worked. I want to add a prefix to a vector of string,
so call
```R
paste("prefix", string_array)
```
and expect it return result with same length to string_array,
it worked for most scenario, but string_array is a empty length array, it gives back

"prefix "

instead of empty array, which makes me confusing! after reading docs of paste, it does mention this behavior:

```
Vector arguments are recycled as needed, with zero-length arguments beging recycled to '""'
```
running behavior matched documents, but such behavior makes code ugly,
I have to add lots of if(length(input) == 0) special handling in code, 
This is not only paste, but also lots of R code, can't handle zero-length array well (or consist),
zero-length array don't make any differences to other ones, 
even library code didn't handle them correctly,
such code will continue to run, until some random place which such result is a hard error, trap at meaningless stack,
or even worse, gives back unexpected result without your notice. 

R also has a 'helpful' feathure, when you slicing from high-dimension array, it will auto drop the size1 dimension of the result,
for example you have a 3x4 matrix, picking 2x1 from it doesn't result a 2x1 matrix, instead you got a length 2 array,
that may seems reasonable for simplify, but nightmare for headless run,
because depends on how length is picked (which is parameter controlled ), result array can be completely different,
but later process code expect this result have fixed layout!  (use drop = F avoid this but requires additional code)

Such inconsistenc appeared everywhere in R, for example sort return sorted result as array, but if you 
pass index.return  = TRUE, the result turned into a list which contains the sorted result and the index.

This is not simply a complaint on R language, I just realize that what I'm complainting is not a problem
for interactive usage, because you viewed every step output, such bugs can be easily discovered during
running. but for headless execution is completely different, youd don't have oppotunity to view every step output, 
so you must 'predict' program behavior, but script language usually is weak typed, there's no restriction on
variable real type, thus make such prediction in weak typed language much, much harder than static typed language.

In theory, if you express exactly same logic in different language (as long as they're turing complete),
it makes no differences between their behavior, and weak type language can omit type declaration,
easier to write, without need to compile ahead of time, why not written whole software in it?  
Unfortunately in practical this is completely different. software always evuluate, with more and more function added,
most of time you're evluting/maintain it, instead of writing all the function at once. for this reason,
you're 'changing' software behavior, and these requires some verify process, how can you assume
changed software still keep their existing behavior correct? how different developers can understand each other's logic?
and more specified, why we're using computer ?

The answser is that human are lazy, they want the computer to handle as much as possible for them.
weak typed language are trying to achive it by let developer delay the type decision time, 
strong typed language are trying to achive it by let compiler checking the contract of developer's type decision.
weak typed language seems easier to write, but does that mean it really get rid of type ? of course not!
you can only iterate read/value pair over a map, not over array; file-liked object can be read bytes from, 
but such read is meaningless on a function. even we don't write the exactly type of variable,
we're expecting the type of variable. because without knowing the type, we can do nothing meaningful.
(some language let you call most common functions like hash/ to_string), and the challenge of weak typed language became: 
can you remember every type your code expect it to be ?
for a simple project, you may remember everything, but when codebase became larger and larger, 
when you need to share work with others, this quickly exploded. and due to fact that weak typed language
don't restrict variable have always same type, your REPL result may lie to you  (just like the R sort function changed return type)




