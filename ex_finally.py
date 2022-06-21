#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 24 14:29:14 2021

@author: artemponomarev
"""

def f1():
    try:
        print('2'+2)
        return 1
    except:
        print('exception')
        return 3
    finally:
        print('finally')
        return 2

    return 5


print(f1())