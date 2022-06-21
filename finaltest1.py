#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 23 13:13:24 2022

@author: artemponomarev
"""

# Node is defined as
# self.left (the left child of the node)
# self.right (the right child of the node)
# self.info (the value of the node)
class NodeBT:
    """
    class for binary tree
    """

    def __init__(self, info):
        self.info = info
        self.left = None
        self.right = None
        self.level = None

    def __str__(self):
        return str(self.info)


class BinarySearchTree:
    """
    class for circular double-linked list
    """
    def __init__(self):
        self.root = None

    def create(self, val):
        if self.root == None:
            self.root = NodeBT(val)
        else:
            current = self.root

            while True:
                if val < current.info:
                    if current.left:
                        current = current.left
                    else:
                        current.left = NodeBT(val)
                        break
                elif val > current.info:
                    if current.right:
                        current = current.right
                    else:
                        current.right = NodeBT(val)
                        break
                else:
                    break

def inOrder(root, arr2):
    if root:
        inOrder(root.left,arr2)
        arr2.append(root.info)
        inOrder(root.right,arr2)
    print(arr2)
    return arr2



class NodeCDLL:
    """
    class for circular double-linked list
    """
    def __init__(self, data):
        self.data = data
        self.next = None
        self.prev = None


def insertEnd(value) :
    global start

	# If the list is empty, create a
	# single node circular and doubly list
    if not start:

        new_node = NodeCDLL(0)
        new_node.data = value
        new_node.next = new_node.prev = new_node
        start = new_node
        return

	# If list is not empty

	# Find last node
    last = (start).prev

	# Create Node dynamically
    new_node = NodeCDLL(0)
    new_node.data = value

	# Start is going to be next of new_node
    new_node.next = start

	# Make new node previous of start
    (start).prev = new_node

	# Make last previous of new node
    new_node.prev = last

	# Make new node next of old last
    last.next = new_node


def display() :

    temp = start

    print ('(from 7) ',end = '')
    print('->',end = '')
    while temp.next != start :

        print (temp.data, end = '<->')
        temp = temp.next

    print(temp.data, end = '')
    print ('-> (to 1)')


# Driver Code
if __name__ == '__main__':
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


# Circular double-linked list
	# Start with the empty list
    start = None
    arr1 = []
    for el in inOrder(tree.root,arr1):
        insertEnd(el)
    print ('\nCreated circular doubly linked list is:')
    display()
