"""
mental arithmetics
"""

import random

complexity=1.0
try:
    while True:
        a=0
        b=100
        x=random.randint(a, b)
        y=random.randint(a, b)
        print(x, y)
        z=input()
        if int(x*y) == int(z):
            print('correct')
        else:
            print('incorrect')
except EOFError:
    pass
