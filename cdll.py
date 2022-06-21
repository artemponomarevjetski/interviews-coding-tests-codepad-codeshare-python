#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 23 12:46:18 2022

@author: artemponomarev
"""
# Python3 program to illustrate inserting
# a Node in a Circular Doubly Linked list
# at the end
start = None

# Structure of a Node
class Node:
    def __init__(self, data):
        self.data = data
        self.next = None
        self.prev = None

# Function to insert at the end
def insertEnd(value) :
    global start

	# If the list is empty, create a
	# single node circular and doubly list
    if (start == None) :

        new_node = Node(0)
        new_node.data = value
        new_node.next = new_node.prev = new_node
        start = new_node
        return

	# If list is not empty

	# Find last node
    last = (start).prev

	# Create Node dynamically
    new_node = Node(0)
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
    while (temp.next != start) :

        print (temp.data, end = '<->')
        temp = temp.next

    print(temp.data, end = '')
    print ('-> (to 1)')


# Driver Code
if __name__ == '__main__':

	# Start with the empty list
    start = None

	# Insert 5. So linked list becomes 5.None
    for i in range(1, 8):
        insertEnd(i)
    print ("Created circular doubly linked list is: ")
    display()

