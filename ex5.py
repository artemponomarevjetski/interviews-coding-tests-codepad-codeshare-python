# you can write to stdout for debugging purposes, e.g.
# print("this is a debug message")

def solution(A):
    # write your code in Python 3.6
    N = len(A)
    if N == 1 or N == 2:
        return 0
    if N == 3:
        if A[0] < A[1] and A[1] > A[2]:
            return 1
        else:
            return 0
    if not (N >= 1 and N <= 1e5):
        return 0
    if not (min(A) >= 0 and max(A) <= 1e9):
        return 0
    npeaks = 0
    for i in range(N-2):
        if A[i] < A[i+1] and A[i+1] > A[i+2]:
            npeaks += 1
    if npeaks == 1:
        return 1
    
    k = 1
    k_max = 0
    b_present = False
    while k<= N:
        if (N/k)%1 != 0:
            k+=1
            continue
        for i in range(k):
            b_present = False
            range_ = N//k
            for j in range(range_):
                if j+range_*i+1 != N:
                    if A[j+range_*i-1] < A[j+range_*i] and A[j+range_*i] > A[j+range_*i+1]:
                        b_present = True
                        break
            if b_present == False:
                break
        if b_present:
            k_max = max(k_max, k)
        k += 1
        
    return k_max


Analysis summary
The solution obtained perfect score.
Analysis


Detected time complexity:
O(N * log(log(N)))
expand all
Example tests
▶
example 
example test
✔
OK
expand all
Correctness tests
▶
extreme_min 
extreme min test
✔
OK
▶
extreme_without_peaks 
test without peaks
✔
OK
▶
prime_length 
test with prime sequence length
✔
OK
▶
anti_bin_search 
anti bin_search test
✔
OK
▶
simple1 
simple test
✔
OK
▶
simple2 
second simple test
✔
OK
expand all
Performance tests
▶
medium_random 
chaotic medium sequences, length = ~5,000
✔
OK
▶
medium_anti_slow 
medium test anti slow solutions
✔
OK
▶
large_random 
chaotic large sequences, length = ~50,000
✔
OK
▶
large_anti_slow 
large test anti slow solutions
✔
OK
▶
extreme_max 
extreme max test

Task description

A non-empty array A consisting of N integers is given.
A peak is an array element which is larger than its neighbors. More precisely, it is an index P such that 0 < P < N − 1,  A[P − 1] < A[P] and A[P] > A[P + 1].
For example, the following array A:
    A[0] = 1
    A[1] = 2
    A[2] = 3
    A[3] = 4
    A[4] = 3
    A[5] = 4
    A[6] = 1
    A[7] = 2
    A[8] = 3
    A[9] = 4
    A[10] = 6
    A[11] = 2
has exactly three peaks: 3, 5, 10.
We want to divide this array into blocks containing the same number of elements. More precisely, we want to choose a number K that will yield the following blocks:
* A[0], A[1], ..., A[K − 1],
* A[K], A[K + 1], ..., A[2K − 1],
* ...
* A[N − K], A[N − K + 1], ..., A[N − 1].
What's more, every block should contain at least one peak. Notice that extreme elements of the blocks (for example A[K − 1] or A[K]) can also be peaks, but only if they have both neighbors (including one in an adjacent blocks).
The goal is to find the maximum number of blocks into which the array A can be divided.
Array A can be divided into blocks as follows:
* one block (1, 2, 3, 4, 3, 4, 1, 2, 3, 4, 6, 2). This block contains three peaks.
* two blocks (1, 2, 3, 4, 3, 4) and (1, 2, 3, 4, 6, 2). Every block has a peak.
* three blocks (1, 2, 3, 4), (3, 4, 1, 2), (3, 4, 6, 2). Every block has a peak. Notice in particular that the first block (1, 2, 3, 4) has a peak at A[3], because A[2] < A[3] > A[4], even though A[4] is in the adjacent block.
However, array A cannot be divided into four blocks, (1, 2, 3), (4, 3, 4), (1, 2, 3) and (4, 6, 2), because the (1, 2, 3) blocks do not contain a peak. Notice in particular that the (4, 3, 4) block contains two peaks: A[3] and A[5].
The maximum number of blocks that array A can be divided into is three.
Write a function:
def solution(A)
that, given a non-empty array A consisting of N integers, returns the maximum number of blocks into which A can be divided.
If A cannot be divided into some number of blocks, the function should return 0.
For example, given:
    A[0] = 1
    A[1] = 2
    A[2] = 3
    A[3] = 4
    A[4] = 3
    A[5] = 4
    A[6] = 1
    A[7] = 2
    A[8] = 3
    A[9] = 4
    A[10] = 6
    A[11] = 2
the function should return 3, as explained above.
Write an efficient algorithm for the following assumptions:
* N is an integer within the range [1..100,000];
* each element of array A is an integer within the range [0..1,000,000,000].
Copyright 2009–2020 by Codility Limited. All Rights Reserved. Unauthorized copying, publication or disclosure prohibited.
