Now we have talked about the control flow graph language and binary form of data, we can finally enter the real programming , means that most code blocks of following chapter is valid C source code. Our first mission is very easy : creating a variable, this is written as following:

```C
int this_is_a_variable;
```
This small code blocks declare a variable which is called "this_is_a_variable" of type **int** (short for **integer**) , ```int``` is a C language keyword, it tells C language your variable is a integer type. ```int``` is the only data type we will touch in recent chapters.

# learning int

In C language, integer can be positive , zero or negative. C language use 32 bit binary to represent this number. Can you guess the value range of int ? What's your answer ?


picture : it must be 0~255 ,response : that's value range of 8bit !


# How to represent a integer by binary bits?

Let's take a simpler example, if you have 8 bits to represent a integer, how will you design it ? 2^8 different state can be represented by 8 bits , we also need to represent the sign of number, negative or positive, that requires 1 bit. So try our first design :

first 1 bit as sign bit, 0 means positive , 1 means negative
left 7 bit as the absolute value

So value range we can represent is :

positive: from  0000'0000 (BIN) to 0111'1111(BIN), that is +0 ~ +127 (DEC)  = 127 different number
negative: from  1000'0000 (BIN) to 1111'1111(BIN), that is -0 ~ -127 (DEC)  = 127 different number
total range: -127 ~ 127 = 255 different number 

Wow, we have two forms of same zero ! That wastes 1 effective state, it also brings some problems:

    Are 1000'0000 and 0000'0000  equal ?

It should be, but binary bits different ! Well let's stop wasting time, there're already smart people whom already designed the best (at least for now) representation form, which is used on every computer today, let's enjoy it !

#picture : So why do we waste time on the bad design?  Because I've wasted time on that ,not fair if you don't.

# Two's complement 

Let's keep the positive form of our design, but make it different for negative number:

1~127: keep as our first design
0:  0000'0000
-0: there is no negative zero 
-1: 1111'1111
-2: 1111'1110
-3: 1111'1101
...
-127: 1000'0001
-128: 1000'0000

This is called :
  **Two's complement**. Which the most used represent form of binary number in computer
It looks a little wired at first, but it makes calculation simpler,  for example

 1 + (-1)  = 0

Binary input0 1  = 0000'0001 (BIN)
Binary input1 -1 = 1111'1111 (BIN)

Let's treat them both as plain positive number and sum them together:

  0000'0001 (BIN) + 1111'1111 (BIN) = 1'0000'0000 (BIN)

We got a 9 bit result, and we only preserve lowest 8 bit , we got result:

  0000'0000

Interesting ? Take another example: 

  5 (DEC) : 0000'0101
 -6 (DEC) : 1111'1010

Sum them as both positive : 1111'1111, which is -1 . You may think the wall clock as example: It's rounded every 12 hours, if you advance time by 9 hours forward, it makes no difference to that bring time by 3 hours backward. We can map original number range

0 ~ 11 into two parts:
0 ~ 5: keeps as original
6 : -6 
7 : -5
8 : -4
9 : -3
10: -2
11: -1

We can also treat our 8bit number as wall clock , which rounded every 256 numbers, this helps better understand two's complement. 

## what happened when result overflow ?

If we calculate two 8bit number represent as two's complement  120 + 120 , we will got such process:

120 (DEC) : 0111'1000 (BIN)
120 (DEC) : 0111'1000 (BIN)

result    : 1111'0000 (BIN)
which in two's complement means: -16 ???? Although this seems incorrect for math, but correct from perspective of "wall clock" meanings. 8bit integer is a wall clock which rounded in [-128 ~ 127], when any number exceeds this range ,it will wrap from another side, 254 exceeds 127 , so left number 113 (240 - 127) will count from -128 , 1st number (of the left 113) wrapped as -128 ,2nd number wrapped as -127 ... finally 113th number wrapped as -16.

In today's computer , lowest level hardware do work in such way. (no matter 8 bit or 32 bit) C language's ```int``` is just map to hardware function, so C language's ```int``` will also "wrapped".

# Does this matter ?

Most of time , this is OK, step back to our 32 bit ```int``` , it can represent value range ...

#picture: it must be -128 ~ 127 !

C language ```int``` value range -2147483648 ~ 2147483647,  it can fulfill wild range of integer math requirements, except for ... the exceptions, for example the time. 

Some System (for example your Android Mobile phone, or your iphone maybe) use int to represent time, in form of elapsed seconds from 1970 January 1st (which is time point such system started to run) , that will warp back at Jan 19 2038 , since it exceeds 2147483647 . You can test this by adjust your mobile phone time after year 2038 and see if it still works. 

picture  my phone not even boot !

Someone reports that their phone didn't work anymore!

# how to resolve this ?

It is hard to tell if this is a "BUG", when you're developing system at 1970, how can you think such system will run over 60 years ? Your mobile phone system of course not developed at 1970, but they followed many design choice of old system, including this "BUG". 

      Why not simply increasing bits of integer , for example 64bit ? 

Some of you may ask question like this,Firstly this is a trade-off, the more bits you support, the more digital circuits you need (or more time calculation spent). Please note that in early days computer can only handle 8 bit integer! Secondly even we increasing bit width of integer, no matter how long it is, it still have limit, it still can not fulfill all usage requirements, for example in 

