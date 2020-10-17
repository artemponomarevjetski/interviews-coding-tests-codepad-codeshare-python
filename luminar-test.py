#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 16 11:38:01 2020

@author: artemponomarev
"""

# Time sync the messages from different topics, coming in at different times 
# input: dict of topic_name: sorted list of timestamps {<topic_name>:[timestamps]}
# output: list of synced topics.  [{<topic_name>:timestamp}]

import sys
def sync_msgs(messages):
  """
  Artem wrote this, there is a repeating code that needs to be simplified
  """
  lst = []
  b_test0 = False
  for ts1 in messages['lidar_0']:
    for ts2 in messages['lidar_1']:
      if ts1 == ts2:
        b_test0 = True
        
# make code O(N), list comprehensions, make it more readable

  if b_test0:
    for ts0 in messages['lidar_0']:
      dict_ = {}
      dict_['lidar_0'] = ts0
      min_ = sys.float_info.max
      ts1_star = 0.0
      for ts1 in messages['lidar_1']:
        if min_ > abs(ts0-ts1):
          min_ = min(min_, abs(ts0-ts1))
          ts1_star = ts1
      dict_['lidar_1'] = ts1_star  
      min_ = sys.float_info.max
      ts2_star = 0.0
      for ts2 in messages['lidar_2']:
        if min_> abs(ts0-ts2):
          min_ = min(min_, abs(ts0-ts2))
          ts2_star = ts2
      dict_['lidar_2'] = ts2_star
      lst.append(dict_)
  else:
    i = 0
    for ts0 in messages['lidar_0']:
      if i > 0:
        dict_ = {}
        dict_['lidar_0'] = ts0
        min_ = sys.float_info.max
        ts1_star = 0.0
        for ts1 in messages['lidar_1']:
          if min_ > abs(ts0-ts1):
            min_ = min(min_, abs(ts0-ts1))
            ts1_star = ts1
        dict_['lidar_1'] = ts1_star  
        min_ = sys.float_info.max
        ts2_star = 0.0
        for ts2 in messages['lidar_2']:
          if min_ > abs(ts0-ts2):
            min_ = min(min_, abs(ts0-ts2))
            ts2_star = ts2
        dict_['lidar_2'] = ts2_star
        
        lst.append(dict_)

      i += 1

  return lst

# 3 topics, difffernt frequency, in sync
def unit_test_1():
    messages = {
        "lidar_0": [
            1585712295.624838,
            1585712296.624838,
            1585712297.624838,
        ],
        'lidar_1': [
            1585712295.124838,
            1585712295.624838,
            1585712296.124838,
            1585712296.624838,
            1585712297.124838,
            1585712297.624838
        ],
        'lidar_2': [
            1585712294.954838,
            1585712295.284838,
            1585712295.624838,
            1585712295.954838,
            1585712296.284838,
            1585712296.624838,
            1585712296.954838,
            1585712297.284838,
            1585712297.624838,
        ]
    }

    expected = [
        {
            'lidar_0': messages['lidar_0'][0],
            'lidar_1': messages['lidar_1'][1],
            'lidar_2': messages['lidar_2'][2]
        },
        {
            'lidar_0': messages['lidar_0'][1],
            'lidar_1': messages['lidar_1'][3],
            'lidar_2': messages['lidar_2'][5]
        },
        {
            'lidar_0': messages['lidar_0'][2],
            'lidar_1': messages['lidar_1'][5],
            'lidar_2': messages['lidar_2'][8]
        }
    ]

    return messages, expected


# 3 topics, same frequency, lidar 0 started early
def unit_test_2():
    messages = {
        "lidar_0": [
            1585712294.624838,
            1585712295.624838,
            1585712296.624838
        ],
        'lidar_1': [
            1585712295.524838,
            1585712296.524838,
            1585712297.524838,
        ],
        'lidar_2': [
            1585712295.724838,
            1585712296.724838,
            1585712297.724838,
        ]
    }

    expected = [
        {
            'lidar_0': messages['lidar_0'][1],
            'lidar_1': messages['lidar_1'][0],
            'lidar_2': messages['lidar_2'][0]
        },
        {
            'lidar_0': messages['lidar_0'][2],
            'lidar_1': messages['lidar_1'][1],
            'lidar_2': messages['lidar_2'][1]
        }
    ]

    return messages, expected

# 3 topics, 2 in sync, the others not
def unit_test_3():
    messages = {
        "lidar_0": [
            1585712295.124838,
            1585712296.124838,
            1585712297.124838,
        ],
        'lidar_1': [
            1585712295.624838,
            1585712296.624838,
            1585712297.624838,
        ],
        'lidar_2': [
            1585712295.724838,
            1585712296.724838,
            1585712297.724838,
        ]
    }

    expected = [
        {
            'lidar_0': messages['lidar_0'][1],
            'lidar_1': messages['lidar_1'][0],
            'lidar_2': messages['lidar_2'][0]
        },
        {
            'lidar_0': messages['lidar_0'][2],
            'lidar_1': messages['lidar_1'][1],
            'lidar_2': messages['lidar_2'][1]
        }
    ]

    return messages, expected

# compare results to expected output
def compare_output(output1, output2):
    if len(output1) != len(output2):
        return False

    for index, message1 in enumerate(output1):
        message2 = output2[index]

        if len(message1.keys()) != len(message2.keys()):
            return False

        for topic in message1:
            if topic not in message2:
                return False

            if message1[topic] != message2[topic]:
                return False

    return True

if __name__ == "__main__":
    unit_tests = []
    unit_tests.append(unit_test_1())
    unit_tests.append(unit_test_2())
    unit_tests.append(unit_test_3())

    for index, unit_test in enumerate(unit_tests):
        synced_messages = sync_msgs(unit_test[0])
        success = compare_output(unit_test[1], synced_messages)

        print("unit_test " + str(index) + " " + str(success) )
