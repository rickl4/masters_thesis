
from subprocess import call
import multiprocessing
import argparse

parser = argparse.ArgumentParser(description = 'Get Paths')
parser.add_argument('-p', '--period', help = 'period')

args = parser.parse_args()
period = args.period

def bc_process(num, per):
    
    call(['python',
          '/Volumes/Data2/RST/notebook/paths/shortest-paths_eval_single.py', '-n', str(num), '-p', per])


if __name__ == '__main__':

        

    param = []
    
    for i in range(0,6,1):
        param.append((i, period))

    pool = multiprocessing.Pool(processes = 6)
    pool.starmap(bc_process, param)
    pool.close()
