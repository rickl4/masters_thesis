# -*- coding: utf-8 -*-
"""
Created on Wed Aug 11 11:51:47 2021

@author: Rick
"""

from subprocess import call
import multiprocessing


def bc_process(num, per):
    
    call(['python',
          '/Volumes/Data2/RST/notebook/GE/ge_single.py', '--number', str(num), '--period', per])


if __name__ == '__main__':

        
    for per in [ 'AM', 'PM', 'EM', 'MD', 'EV']:
        param = []


        for i in range(6):
            param.append((i, per))

        pool = multiprocessing.Pool(processes = 6)
        pool.starmap(bc_process, param)
        pool.close()