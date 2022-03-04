# -*- coding: utf-8 -*-
"""
Created on Wed Aug 11 11:51:47 2021

@author: Rick
"""

from subprocess import call
import multiprocessing
import argparse

parser = argparse.ArgumentParser(description = 'Get Paths')
parser.add_argument('-p', '--period', help = 'period')

args = parser.parse_args()
per = args.period

def bc_process(num, per):
    
    call(['python',
          '/Volumes/Data2/RST/notebook/paths/paths_single.py', '--number', str(num), '--period', per])


if __name__ == '__main__':

        
    # param = []


    # for i in range(6):
    #     param.append((i, per))

    # pool = multiprocessing.Pool(processes = 6)
    # pool.starmap(bc_process, param)
    # pool.close()
    
    
    '''
    only running 3 processes at a time due to memory
    '''
    param = []
    
    for i in range(0,3,1):
        param.append((i, per))

    pool = multiprocessing.Pool(processes = 3)
    pool.starmap(bc_process, param)
    pool.close()
    
    param = []
    
    for i in range(3,6,1):
        param.append((i, per))

    pool = multiprocessing.Pool(processes = 3)
    pool.starmap(bc_process, param)
    pool.close()