#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 23 11:40:48 2022

@author: artemponomarev

Node is defined as
self.left (the left child of the node)
self.right (the right child of the node)
self.info (the value of the node)
"""

# This code solves the following assingment:
# 1. Given a binary tree made of these nodes, convert it, in-place (i.e. don't allocate new Nodes), into a circular doubly linked list in the same order as an in-order traversal of the tree.

#        |
#   __4__
#  |         |
#  2        6
# |   |     |   |
# 1 3    5   7
#
# (from 7) ->1<->2<->3<->4<->5<->6<->7-> (to 1)

class Node:
    """
    binary tree class
    """
    def __init__(self, info):
        self.info = info
        self.left = None
        self.right = None
        self.level = None

    def __str__(self):
        return str(self.info)

class BinarySearchTree:
    def __init__(self):
        self.root = None

    def create(self, val):
        if self.root == None:
            self.root = Node(val)
        else:
            current = self.root

            while True:
                if val < current.info:
                    if current.left:
                        current = current.left
                    else:
                        current.left = Node(val)
                        break
                elif val > current.info:
                    if current.right:
                        current = current.right
                    else:
                        current.right = Node(val)
                        break
                else:
                    break

def inOrder(root):
    if root:
        inOrder(root.left)
        print(root.info, end=" ")
        inOrder(root.right)

# Example 1. Test input for inOrder traversal
# this tree
   # 1
   #    \
   #     2
   #      \
   #       5
   #      /  \
   #     3    6
   #      \
   #       4

# is cnverted to this input
t = 6
arr = [1, 2, 5, 3, 6, 4]
tree = BinarySearchTree()
for i in range(t):
    tree.create(arr[i])
inOrder(tree.root)
print()
print()
print()

# Assingment
#     0
#     |
#   __4__
#  |         |
#  2         6
# |   |     |   |
# 1   3     5   7

# (from 7) ->1<->2<->3<->4<->5<->6<->7-> (to 1)

print("This generates inOrder traversal of the binary tree")
t = 7
arr = [4, 2, 6, 1, 3, 5, 7]
tree = BinarySearchTree()
for i in range(t):
    tree.create(arr[i])
inOrder(tree.root)
