#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 23 18:20:36 2020

@author: artemponomarev
"""

import random

DICK = {
        'Fuck you!': 'Fuck you, too!',
        'Hi' : 'Well, hello-oh!',
        'hi' : 'Well, hello-oh!',
        'Hi!' : 'Well, hello-oh!',
        'hi!' : 'Well, hello-oh!',
        }

#sentences we'll respond with if the user greeted us
GREETING_KEYWORDS = ("hello", "hi", "greetings", "sup", "what's up", "hey")
GREETING_RESPONSES = ["What the fuck?", "Dig it?", "Ready, Freddie?",
                      "Boobs, stop fucking around and get real"]

def check_for_greeting(sentence):
    """If any of the words in the user's input was a greeting, return a greeting response"""
    for word in sentence:
        if word.lower() in GREETING_KEYWORDS:
            return random.choice(GREETING_RESPONSES)
    return None

def ReadSnowWhite(text):
    return text

def art_nlp(text_):
    """
    Artem's method of text comprehension
    """
    return text_.split()
