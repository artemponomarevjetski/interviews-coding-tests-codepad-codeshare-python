#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 23 10:56:11 2022

@author: artemponomarev
"""

# Task:
# Input: ((( Output: 3
# Input: ()) Output: 1
# Input: )( Output: 2

def solution(S):
    if len(S) == 0:
        return 0
    if len(S) == 1:
        return 1

    stack_ = []
    for c in S:
        if stack_:
            el = stack_.pop()
            if el == '(' and c == '(':
                stack_.append(el)
                stack_.append(c)
            elif el == '(' and c == ')':
                pass
            elif el == '(' and c == '[':
                stack_.append(el)
                stack_.append(c)
            elif el == '(' and c == ']':
                stack_.append(el)
                stack_.append(c)
            elif el == '(' and c == '{':
                stack_.append(el)
                stack_.append(c)
            elif el == '(' and c == '}':
                stack_.append(el)
                stack_.append(c)
            elif el == '[' and c == '(':
                stack_.append(el)
                stack_.append(c)
            elif el == '[' and c == ')':
                stack_.append(el)
                stack_.append(c)
            elif el == '[' and c == '[':
                stack_.append(el)
                stack_.append(c)
            elif el == '[' and c == ']':
                pass
            elif el == '[' and c == '{':
                stack_.append(el)
                stack_.append(c)
            elif el == '[' and c == '}':
                stack_.append(el)
                stack_.append(c)
            elif el == '{' and c == '(':
                stack_.append(el)
                stack_.append(c)
            elif el == '{' and c == ')':
                stack_.append(el)
                stack_.append(c)
            elif el == '{' and c == '[':
                stack_.append(el)
                stack_.append(c)
            elif el == '{' and c == ']':
                stack_.append(el)
                stack_.append(c)
            elif el == '{' and c == '{':
                stack_.append(el)
                stack_.append(c)
            elif el == '{' and c == '}':
                pass
            else:
                stack_.append(el)
                stack_.append(c)
        else:
            stack_.append(c)
            
    return len(stack_)
    
    
print(solution('((('))
print(solution('())'))
print(solution(')('))