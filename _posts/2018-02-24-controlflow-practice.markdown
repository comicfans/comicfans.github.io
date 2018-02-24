---
layout:     post
title:      "practice and more"
subtitle:   "Blog"
date:       2018-01-23 10:00:00
author:     "comicfans"
tags:
    - c++
    - computer
    - programming
---

# practice

Now we have completed controlflow language and data storage, with these two combined , we can write our program to do most any kind of calculation, of course it can resolve many math problems. And it also have not much differences to any other 'real' programming language except syntax and execution (we must execute control flow graph language by ourselves instead of by computer), most basic construct block has no difference to C language in logical. Before enter C chapters , I'll leave some practices, this help to think in "programming" way.



# find max number inside a number bag :

suppose that the number bag is declared as 'some_numbers' and it always have elements

declare variable 'current_max' = minimum_value_integer

loop element inside some_numbers:
    if element > current_max:
        set current_max as element value

now current_max value is the max value of all numbers in bag


# tell if a positive number is a primer:

suppose that the number to test is always positive , which name is 'to_test'

declare variable 'test_divider' as 1    , used to divide to_test from 1~to_test-1
declare variable 'divide_number' as 0   , used to record how many numbers can be divide to_test without reminder

loop condition : test_divider < to_test
     body : declare variable reminder = to_test % test_divider 
            if reminder is not 0 :
                 divide_number = divide_number +1
                 if divide_number> 1:
                      END this is not a primer
            else:
                 continue loop
          

# find max primer from a number bag:

suppose that 
            
            









