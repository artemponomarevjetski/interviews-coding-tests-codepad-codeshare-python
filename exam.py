#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 13 12:22:00 2022

@author: artemponomarev
"""

# my_list =[9, 9, 9, 9, 2, 3, 9, 1, 1, 4, 5, 5, 5]
# # Output:

# # 1 : 2
# # 2: 1
# # 3: 1
# # 4: 1
# # 5: 3
# # 9: 5

# dict1={}
# for el in my_list:
#     if el in dict1.keys():
#         dict1[el]+=1
#     else:
#         dict1[el]=1
    
# print(dict1)

#cli
# az -flag1 -flag1

# cubectl 

# primes from 1 to 100
primes = []
for i in range(100):
    if i == 50 and i  == 70:
        pass
    ndiv = 0
    for j in range(1, i):
      #  print(i/j)
        if int(i/j) != i/j:
            # i is a div
            ndiv += 1

    if ndiv==0:
        primes.append(i)
            
print(primes)

p =100
p/2

while TRue:
    i+=1
    p <i*i