
from subprocess import call
import multiprocessing


def bc_process(num, per):
    
    call(['python',
          '/Volumes/Data2/RST/notebook/BC/bc_single.py', '--number', str(num), '--period', per])


if __name__ == '__main__':

    for per in ['AM', 'MD', 'PM', 'EV']: 
        param = []


        for i in range(6):
            param.append((i, per))

        pool = multiprocessing.Pool(processes = 6)
        pool.starmap(bc_process, param)
        pool.close()
    
    


