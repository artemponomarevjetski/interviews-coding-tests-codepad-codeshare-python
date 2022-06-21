#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  7 12:04:40 2022

@author: artemponomarev
"""

# An anagram is any pair of words that use the exact same letters, rearranged.

# Write a python function is_anagram() that checks whether two strings are anagrams of each other.

# e.g.

# is_anagram(“secure”, “rescue”)
# True

# is_anagram(“bba”, “dab”)
# False

def is_anagram(s, s1):
    if len(s) != len(s1):
        return False
    
    dict1  = {}
    for c in s:
        if c not in dict1.keys():
            dict1[c] = 1
        else:
            dict1[c] += 1
            
            
    dict2  = {}
    for c in s1:
        if c not in dict2.keys():
            dict2[c] = 1
        else:
            dict2[c] += 1
            
    print(dict1, dict2)
    if dict1 != dict2:
        return False

    
    # for c in s:
    #     for c1 in s1:
    #         if c1 in s and c in s1:
    #             continue
    #         else:
    #             return False
    return True
        
s='secure'
s1='rescue'

print(is_anagram(s, s1))

# O(N^2*M^2)
print(is_anagram("ba", "bab"))

"bacc" 'bbac'