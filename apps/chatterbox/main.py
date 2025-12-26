#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 23 17:52:47 2020

@author: artemponomarev

Art's chatterbox
"""

import sys
from dick import DICK, check_for_greeting, ReadSnowWhite, art_nlp
from snow_white import text

print('Hi!')
i = 0
convo = False
for line in sys.stdin:
    i += 1
    print(f'Processing your message from sys.stdin *****{line}*****\nYou said, ', line)
    l = line.rstrip()
    print(l == 'Read Snow White')
    if l == '' or l is None:
        print('?')
    elif i == 1 and not convo:
        print("HERE1")
        l1 = check_for_greeting(l.split(' '))
        if l1:
            print(l1)
        else:
            if l in DICK:
                print(DICK[l])
    elif 'Bye' in l or 'bye'in l:
        break
    elif l in DICK:
        print(DICK[l])
    elif l == 'Read Snow White' or convo:
        convo = True
        print("HERE")
        convo = art_nlp(ReadSnowWhite(text))
        response = None
        for line1 in sys.stdin:
            l = line1.rstrip()
            if l in ('quit', 'stop', 'bye', 'exit'):
                convo.save()
                break
            response = convo.reply_to(l)
            convo.update(response, l)
            print(response)
    else:
        pass

print("Bye!")
