Disclaimer: this is mostly my complaint at work, shouldn't be considered seriously (some sort of)

I've worked with low-level language before, mostly C/C++ , also have some years
experience of java development. Recently I tried rust and go, as you can see,
they're all static-typed, compiler checked language. I do use script language like 
python and javascript, just for one-shot and throw-up usage, never use them
to create serious project. And for some reason, we have to use R language in our work,
because we need to import an existing R project as part of our codebase.

Let me give a short introduction of R language: it's a interpreted, dynamic typed, GC language,
it has good support for statistics and data analysis.  The main difference of R and most other
language is that its builtin type are always array, even a single number is just a 
one length array. and all operators are also array based , for example a + b does a element wise
add. 

We use this codebase for lots of data analysis, This improved my interactive
programming skills a lot, makes me rediscovered script language. Although I
also used chrome dev console to do some quick interactive jquery test,
but all of them are still one line try and throw temp code, I haven't tried
long context interactive programming.

At first it makes me feel 'uncomfortable', in static-typed language,
(which mostly pre-built ) I'll write lots of code, and predict
how my whole code will be acting, run all code at once, when error happened, 
do edit-build-rerun circle. But such flow works very badly in R, since some of the analysis
logic are very time-consuming and flexible, whether to apply some analysis is 
depends on previous step result, I can't predict whole logic in front,
and any bug/changes led me to waste lots of time (even some result of intermediate step
can be reused), so I tried to give up source coding and just run logic in R console. 

then it makes me feel 'forgettable', without source code for reference,
it requires me to very focus on context, it does not only requires me
to write code at where I am, but also requires me to remember almost everything
what I've written (I don't use jupter book alike editor since its operations
differ to vim too much), I quickly lost the track.
Therefor I tried to combine advantages of editor and console together,
to mimic jupter book alike experience. So I write short code snippet in temp source file, still using vim,
then using nvim-R plug to quickly send these lines to R console.
After I can quickly operate these basic blocks, my development experience
got much improved: history logic still kept in source code, all my vim skills
still apply, and I can run any block of these code easily.

After some days usage, development became 'enjoyable',  I don't run lots of 
code at once, instead I just run little piece of them in console, to verify result,
decide what to do, then try next block ... since all intermediate result is kept ,
I can easily reuse them to try different analysis, avoid lots of time waste.
I realized that such try-and-run development is much faster than my traditional
run-from-beginning workflow. It feels like I'm running a super powerful
debugger in any local scope, and it has exactly same language syntax support,
which is unimaginable for pre-built languages!  (today gdb/lldb are still trying to merge more
c++ syntax/ast support , since they can't eval complex expression)
and in such console you never need to worry about missing critical expression result in debugger,
just re-evalute expression again, result pop immediately, no need to reproduce 
the scene, it feels so convenient! Script language also mostly design their 
basic/composite type viewed as string directly in console, inspecting variable makes much easier.
now I can quickly write/verify my code, piece by piece, instead of predicting
too much context at once. 


And I think R has a killer feather (even among script languages),
that the built-in debugger is also fully interpreted (makes no differences to 
the code it's debugging), which means you've already trap in debugger ,
you can still call some R code with breakpoint in it, from current debugger!
then you will be recursively trap into debugger again. In other script languages,
for example python, when trap in pdb, you can evaluate python code, but if
the evaluated code contains breakpoints, it won't trap again recursively.


This may seem a little wired at beginning,  but actually very useful in practice.
While debugging complex logic, you may want to inspect multiply involved function's 
behavior, with different arguments to current debugging context (maybe 
the function you want to inspect is a unrelated function and 
even not being used in current debugging context).
then you can just set breakpoint on that function, call it with arguments
whatever you want, then you immediately dropped into new debug context,
with all expected input.

another usage is for repeat debugging one logic, for example you already run over
a line (maybe by mistake, or you just return from it but wants to debug it again),
you can just repeat call this logic in debugger, trap time by time endlessly.
This makes R debugging much easier to use than other languages, 
and for this reason I debug R code much more frequency, and feel that I can understand 
whole codebase more clear than using other languages. Since their debuggers can only
step over fixed debug path, I have to spend more time on constructing different entries
(for example testcases) to trigger different path debugging.
of course you can always use REPL to run different codes, but complex logic
have deeply nested function calls, debugging whole stack into most function
requires you to paste almost every lines through the code path. Such debugging
is much harder than R. 


The headache of interactive programming.

we also faced some headaches, the most critical one is result reproducible.
When sharing code between workmates,
we hit lots of result-mismatch/code-cant-run problems, even in my personal
environment some code don't produce same result between runs, or even don't work
at next run, which is very annoying. After debugging again and again, 
we realized that interactive programming has a very big drawback:
** every variable in current scope became global variable**.
we does not only enjoy the quick REPL experience, but also doing the 
'global variable considered harmful' practice. these variables names
coverages all the common name I used (because they're just named by me after 
long time running...), so even I run a function call with typo arguments,
it may still run and even give a very good result ! Unfortunately this doesn't
raise any error. After combined pieces of codes together and rerun, suddenly
all sort of bugs pop: mismatched function call, bad variable name …
so usually we reinitialize workspace after after code combined, 
then rerun combined code, to make sure it really does what it expected to do.
and we must be careful when run long-time calculation, it easily waste bunch
of hours/days to get incorrect result.  

Another weakness of R lang is parallel support, it doesn't have builtin
threading support, there do exist some libraries to utilize more system source
(using forking or multi process model), but as expected, 
this leaks implementation details of low level OS behavior to languages. It looks like 
'just change apply to future.apply should accelerate my code', but in reality
for developers who just do copy-paste found it slower than normal code (
threading library auto switched to multi-process model when it
detected it's running under Rstudio which is incompatible with threading, and
library spend all the time to transfer big object which is accessed
by parallel part of code) breakpoint/crash don't trap anymore(debugger only works in main console thread),
write to global variable doesn't take effect (they're just writing to forked memory space).
At last, developers who don't care about too much system detail just give up
using parallel, they find it too hard to use (funny enough they're deciding
to migrate to python, which suffer from GIL problem)


If the problem I mentioned is not the worst, using R headless is real nightmare.
To reuse most R logic in other places, we decide to make these logic run
headless every day, do some auto-data-update, more and more tricky bugs pop,
while developing and debugging these code,  the 'uncomfortable' feeling came
back and all the F word jump into my brain...

first problem is that when running R source with Rscript in command headless (instead
of running in R console interactively) , R don't show crash stack filename and line number!
it just gives a super-simplified call chain like:

```
apply->functiona-> paste-> ...
```

instead of normal interactive debugging display:
```
file1: line 234: apply
file2: line 456: functiona
file3: line 789: paste
```

This does not make any sense! R console already show full backtrace , 
why script run have none of this ? I've asked this question on R-devel mailing list, seems nobody cares.
and even such simplified call chain, R will omit parts of it! 
when you have long call chain, your output will be like this:

```
apply->functiona->...    functionb -> ... paste
```

yes, R script just replace some of the name with three dots,
you have to do fuzzy match and guess! it's better than nothing output, but seems more like a joke.

Another approach I tried is the 'dump' function, set dump as error function, it will save
whole running workspace as a file, which can be loaded later for debugging, just like coredump.
but our R data update logic loads lots of data, even the smallest dump will take minutes 
to complete, and create multi-GB file, which is not practical. So we have to repeat running
our code in Rconsole, to identify the crash location.


I've written lots of R debugging advantages, but it also has a funny behavior:
R debugger do output filename, line number and function name, but the stack level is incorrect! 
I don't know how this is implemented(maybe due to that R debugger is also interrupted?),
at least for other languages, if I want to go to target stack level shown by stack trace,
I just enter the corresponding number of the function line I interested,
then I got that stack. but for R, this never worked,
the number you enter is always one level higher/or lower than shown line, I have to 
guess it everytime, using variable list and source code to confirm I'm at the correct stack location!
and R sometimes do lazy evaluate, so the call stack order may also be inverse, that makes 
logic much harder to debug! for example in normal calling order, you call

```R
f(g(h()))
```

h is called first, then g, then f at last.  I call this 'normal' because if view this callsite as a 
data flow, the output of h flow into g, then output of g flow into f,
so the root node h should run first, otherwise other node don't have necessary input.
Any error happened in h should break whole flow immediately, because later node don't have necessary input.
but in lazy evaluate, h call actually happened when the h output is accessed by g call,
and g call actually happened when the g output is accessed by f, so the running order is that :
f runs first, it access a variable of g output, leads g is called, and h is called last!
so the backtrace will show backtrace of f and g first, but the bug actually happened in h! 
combined with normal evaluated order functions, some debugging became hard to understand.
such lazy evaluate implicates another potential problem, it will hide the buggy logic if that result is
not accessed! code f seems worked for a long time, makes you think any of its input (g and h) also workes,
but actually g or h never run.


another problem of R is consistence, although its built-in type is array based,
but function based on these concept don't give consist result. For example in other language
you may write 

```
if(a > b) {
    do_something()
}
```

in R the "if" expression accept only a single value, but R can't tell a or b is single-value or not(single value are just 1 element array),
so it can't verify its correctness ahead of time, you must run to this line to know if it worked or not,
and once correctness does not mean such line always correctness! 
you may think it's not a big deal, just pass a and b as single element variable makes everything work,
but it's not! R is array based, code may quickly changed to make a/b any length in some other places, 
leave this if expression invalid. and by default R also don't force crash invalid usage, 
if a and b are multi-value, R 'warning' you that only first element of array is used as condition, 
if you're also printing some other logs, such warning quickly ignored in headless execution.
R also has options to treat these warnings as errors (crash immediately), 
but even the base function in R has lots of such warnings (sqrt(-1) produce NAN also be a warning),
such warnings can also came from any of used library. Treat warning as error
can help you quickly find bad usage in interactive usage, but not suitable for a headless run.

another example of inconsistency is how zero sized array is handled, you can define a zero sized array as

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

another tricky of R is how paste (concate string together) worked. I want to add a prefix to a vector of string,
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
This is not only paste, but also lots of R code, they can't handle zero-length array well (or consist),
and zero-length array don't make any differences to normal ones, 
logic just continue to run, until some random place which triggered a hard error, trap at meaningless stack,
or even worse, gives back unexpected result without your notice. 
This is also the case for how most R function handle invalid parameter input,
they work well for expected input, but crashing at random location for invalid input.
to resolve similar problem, our logic add many input checking logic,
for example test their type/array shape is expected, and actively reporting 
invalid special value (NA/NULL)

R also has a 'helpful' feathure, when you slicing from high-dimension array, it will auto drop the size1 dimension of the result,
for example you have a 3x4 matrix, picking 2x1 from it doesn't result a 2x1 matrix, instead you got a length 2 array,
that may seems reasonable for simplify, but nightmare for headless run,
because depends on how length is picked (which is parameter controlled ), result array can be completely different,
but later process code expect this result have fixed layout!  (use drop = F avoid this but requires additional code)

Such inconsistenc appeared everywhere in R, for example sort return sorted result as array, but if you 
pass index.return  = TRUE, the result turned into a list which contains the sorted result and the index.

I realized that what I'm complainting is not a problem for interactive usage,
when viewed every step output, such 'bugs' can be easily spoted (actually 
these are 'feathures' to improve interactive experience). it has so many 'easy to use'
feature but in headless execution this just makes everything more complicit.
In headless execution you don't have oppotunity to view every step output(such code may run 
millions times with many different input parameter), so you must 'predict' program behavior,
and for predictable, consist behavior (even it's more complicit) is much more important than 
easier(but inconsist) usage. Since script language is (almostly) dynamic-typed,
there's no restriction on variable's type, thus make such consist behavior
prediction much, much harder than static typed language. This makes dynamic-typed
language not suitable for big scale codebase and none-interactive usage. 

Another minor(maybe major) problem is that IDE can't provide very helpful completion suggestion
for dynamic-typed language, since even the language itself don't know the actual
type of variable until runtime, of course IDE don't know what they should suggest!
oh the other hand static-typed language have all variable type defined at compile time,
IDE can easily understand what action your code is allowed to do, thus give
very percisie suggestion. If the suggestion engine and language have tight integration,
It can even provide almost correct suggestion.correct here doesn't mean correct logic,
it means the suggested code are always able to pass the compiler-check, but that's also
a big improvement for developing.

This is not simply a complaint on R language, I've also used other script languages before,
but never maintain such scale codebase for so much headless usage.
In theory, if you express exactly same logic in different language (as long as they're turing complete),
it should make no differences between their behavior, and dynaimic type language omit type declaration,
easier to write, without need to compile ahead of time, why not write whole software in it?  
Unfortunately in practical this is completely different. software always evuluate, with more and more function added,
most of time you're evluting/maintain it, instead of writing all the function to its final state at once.
for this reason, you're keeping 'changing' software behavior, and these requires some verify process,
to assume such modification not break existing logic, and different developers need to understand each other's work.
documentation, code review, testing can help this, but the language feathure itself, is also important.
so why are we using programming language, and more specified, why are we using computer?

I think the answser is that human are lazy, we want the computer to handle as much as possible for us.
dynamic/static-typed language choose different approaches:
dynamic-typed language try to simplify variable type declaration, let developer delay the type decision to runtime.
static-typed language try to let compiler checking the behavior of developer's decision, by require developer decide the type up front.

Developers found it's easier to use variables without declaring type, 
but does that mean you really don't care about the type ? of course not! 
you can only iterate key/value pair over a map, not over array; file-liked object can be read bytes from, 
but such read is meaningless on a function. even we don't write the exactly type of variable,
we still have to assume type of variable is expected. without knowing the type, we can't do anything meaningful.
(you may call some common functions like hash_code/ to_string, but that doesn't help)

so the hard part of dynaimc-typed language became: 
can you remember every type your code expect it to be? can you keep all these types correct all the time? without type declaration? 
My experience is that even I've read whole source code multi times, I still need runtime verification to know
the exactly type of variable. And when you need to share works with others, this workflow quickly exploded.
and dynamic-typed language don't restrict variable being always same type
(just like R sort changed result type depends on input parameter), your REPL result isn't always true.
not to mention that many runtime behavior can't be easily run in REPL.
to overcome this, even dyanmic-typed language are introducing type declaration, for example  
dropbox has a blog which share the similar point at 2019-Sep 
[Our journey to type checking 4 million lines of Python](https://dropbox.tech/application/our-journey-to-type-checking-4-million-lines-of-python):


```
Once your project is tens of thousands of lines of code, and several engineers work on it, our experience tells us that understanding code becomes the key to maintaining developer productivity. Without type annotations, basic reasoning such as figuring out the valid arguments to a function, or the possible return value types, becomes a hard problem
```

Dropbox also submitted their type hint proposal as PEP-484, and today we can see
many python code have variable type declaration (even it's still dynamic typed).

static typed language force you to declare type upfront and won't change it during runtime,
it also requires lots of code modifications when you change logic or type,
this seems more time-consuming, but actually it moved the runtime break into 
compile time error, because incompaitble type/usage is forbidden in static-type language (
even during execution such logic won't being called) for dynamic-typed language,
such incompaitble problem only triggered at runtime, or even worse,
incompatible function not being called at runtime without anybody notice,
or given silent incorrect result without crashing.

Another interesting thing is that while dynamic-typed language are introducing type declaration,
which make it more alike static-typed language, static-typed language are also introducing type infer,
let developer can omit some variable type declaration (if not all), thus make them alike
dynamic-typed language.  for example

```C++
    std::vector<std::map<std::string, std::set<int> >>::iterator it = container.begin();
```

became

```
    auto it = container.begin();
```

while type still being static, this still reduces lots of code. but this also brings the problem
of dynamic-typed language, you easily forgot type since they're not in source code anymore.
someone suggested to only use type infer on most obvious type to keep source code more readable.
I personally prefer IDE inlay hint function. when you open source code in IDE, 
editor will display type of every variable. This is not only useful for the type infer, it also
display function argument and return type, helps you to better understand code in their context.


Error handling in different languages

some languages using return code for error handling, for example
C/(and some C++), developer have to check result of every function call
(or check a special errno variable )to determine if they're hitting error 
condition, which is error-prone if developer forgot checking or 
compare it to incorrect values.

In go lang, forgot checking the error variable is a hard error 
(other languages usually treat unused variable as soft warning and let such
potential bug happen at runtime). rust also use return value,
it wrap normal return value into a Result type,
developer must explicitly 'unwrap' the Result type to get correct value or
read the error, rust also provide a syntax sugar to shortcut such handling.


most other modern languages use exception handling, 
which don't require handling logic exactly match every function call, instead, 
such handling can contains many function call, any unhandled exception
will immediately stop current stack execution and unwrap stack up recursively,
until matched handler found. it allows error handling code 
decoupled from where error happened, makes normal codepath clean,
but also requires handling logic match the actual exception spec.
if logic handle FileNotFound exception, but the code actually throws
FileCantOpen exception, although two errors are very similar, such handle
logic won't work. Such logic/exception match requires language support,
and for my personal experience, I think java exception handling is great.

Firstly java clearly distinct 'Unchecked Exception' and 'Checked Exception',
unchecked exception are used for programming logic error, for example dereference
null pointer or access out of range array index,such exception should be fixed at
source code level, instead of being handled during runtime, thus any of such
catalog exception don't (and shouldn't ) requires explicit handle, 
OTOH 'Checked Exception' to indicate the error only possible to be handled properly
during runtime, for example most IO exception. Java also force 
Checked exceptions must be declared as part of method signature, which means
it's impossible to missed such exception handling (otherwise code won't build),
or you declare it and let caller handle it. Such restriction greatly reduce
the potential mismatched error handle logic.

but script language usually don't have such strict declare requirements,
extra code is one reason (which conflicts to simple usage goal),
another reason is also that most script language is dynamic
typed, even the interpreter don't have enough type information until runtime,
thus it can't precisely verify code do-or-not follow the declaration.

This leads exception handling in script language very weak, 
almost any code is possible to throw any exception without any source hint, 
developers have to read documents to know what to handle, 
and most importantly, any mismatch led mis-behavior won't get any notice!

Here I may understand differences between languages deeper:
their trade-off does not only apply to easy or hard to use, different api call,
but also impacts how developers construct their logic, how they maintain codebase.




