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
          '/Volumes/Data2/RST/notebook/paths/paths_single_shortest.py', '--number', str(num), '--period', per, '-s', '1001'])


if __name__ == '__main__':

        
    param = []


    for i in range(6):
        param.append((i, per))

    pool = multiprocessing.Pool(processes = 6)
    pool.starmap(bc_process, param)
    pool.close()
    
