Before learning the actual programming language, first we need to learn what is "Language". Computer can not understand "Natural Language" (such as English, very well yet). if you want to drive computer to do something for you, 

you must input something which computer understood, the input itself, is language. 

Any form of input which drive computer do something for you , can be a language, from this perspective, it is not limited to that on programming books. When you browse internet with a browser, the mouse move and keyboard input, is also "browser" language. The browser understand these inputs , and feeds back the result -- the web page.


picture


Most people don't treat this form of inputs as "programming language" , but any programming language also works in same way, the only differences is the input form. Most programming language take a "text" as inputs, you just write text with limited set words (which this language allowed), and computer take it in, run logic in it, feeds back the result.




To most newcomers , convert natural logic to "limited set of words which language understood" is the most complicate thing, to resolve this problem, we  ...  don't learn any of them (yet) ! We will learn a graphical understood easy language --

ControlFlow Graph Language

Let's write our first program in control flow graph language:


its just like the adventures gamebook with many decision points, you will got different story line and end(good or bad) depends on your decision.

It have some very basic construct blocks (or in other words,control block or statement) and construct rules:

     Normal Block: do something ,then control flow will goto following Block .
     Condition Block: depends on a condition (true or false), control flow will goto different Block (branch1 or branch2) . 
     Composite Block: contains one or more other Blocks (Any of Normal/Condition/Composite), you can treat it as "group multi block together as one"

Ok let's take a look at following control flow:

example1: view tutorial page:

1. power on computer
2. open browser 
3. goto https://comicfans.github.io


example2: decide what to do:

 is this tutorial interesting ?
Yes: continue reading.
No : close this page.



of course this program can be modified as following :

 is this tutorial interesting ?
Yes: continue reading.
No : answer this question again.
 
picture.

if you written such logic by mistake like this, which makes result unexpected, that said you have a 

# BUG

At early days ,computer is not as small/stable as today's, it's constructed by a large set of electronic components. A bug (acutal bug) inside the hardware triggered the world's first computer problem , so today we call any "mistake or fault" of computer "bug ".


today's computer is much more stable so unexpected result is likely 99.9999% bug inside your program (instead of hardware). When you hit a bug, you may want to exam your control flow graph and find it. This is called :

# DEBUG

In following tutorials , you may found many unexpected results when trying the code out, please note that computer is a dumb. it just try to execute the logic you guide it to,you should try following control flow graph:




Control flow graph seems too easy ? Well this is very useful for learning programming, when you write control flow graph first time, you're following "From Top to Bottom" approach, you avoid touching too many language detail while  lower your natural language to the computer style language.

# From Top to Bottom 

that means you construct program at very high level first (just like natural language ,which is called "top"), and then lower them down to low level steps(until as low as programming language ,which is called "bottom") step by step. you describe the highest level in natural language, without care low level language detail at all. It gives you better overall view of program, even for experienced programmer. For previously "view tutorial page" example, we may lower step 3 to following steps:

2.1 move mouse to the browser icon
2.2 double click

and step 2.2 can be lowered as :

2.2.1 click once
2.2.2 click once again in short time


step 3 can be lowered as:

3.1 move mouse to location bar of browser
3.2 type https://comicfans.github.io

even step 3.2 can be lowered to

3.2.1  press 'h'
3.2.2  press 't'
3.2.3  press 't'
3.2.4  press 'p'
...
3.2.xx  type 'Enter'



and finally our control flow graph looks like this:

1. power on computer
2. open browser 
  2.1
  2.2
    2.2.1
    2.2.2
3. goto https://comicfans.github.io
  3.1
  3.2
    3.2.1
    3.2.2
    ... 

Why we're repeating learning such stupid low level steps ? Remember that computer is a dumb ? There is not too much 'smart' stuff programming language can automatic recognize , you must 

  describe exactly every single precise step what you want to do

it's just like when surfing the internet, you have to use mouse and keyboard (or maybe touch screen) to tell browser which page you want. When every step you lowered can be understood by programming language, congratulations! You've been a programmer!  

to test whether you can describe precise steps , design a program as ControlFlow graph ,and asking your friend to execute it , to see if the result is expected !

picture



Note: it's not a good idea to learn programming from bottom to top , which is ,  try to learn all the language rules first, and then start programming. Different languages have different feature sets and rules which you must learn from scratch,but high level logic keeps same across different languages. 



can you describe if a integer is a prime number ?

