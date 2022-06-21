# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import random
import numba

@numba.jit
def monte_carlo_pi(nsamples: int):
    """
    numba ex.
    """
    acc = 0
    for _ in range(nsamples):
        x = random.random()
        y = random.random()
        if (x**2 + y**2) < 1.0:
            acc += 1
    return 4.0 * acc / nsamples

print(monte_carlo_pi(10000000))
