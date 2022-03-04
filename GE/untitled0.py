# -*- coding: utf-8 -*-
"""
Created on Fri Aug 13 10:14:08 2021

@author: Rick
"""

import csv
i = 1
j = 2
k = '43423'
l = '423'

per = 'EV'
num_str = '3'
with open(per + '/' + num_str + '-ge-log.txt', 'a', newline='') as f:
    writer = csv.writer(f, delimiter=',')
    writer.writerow([str(i), str(j), k, l])

        
        
