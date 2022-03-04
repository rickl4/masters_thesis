import pandas as pd
import numpy as np
import os
import argparse

root = '/Volumes/Data2/RST/notebook/'


parser = argparse.ArgumentParser(description = 'Get Paths')
parser.add_argument('-n', '--number', help = 'bin number')
parser.add_argument('-p', '--period', help = 'period')

args = parser.parse_args()
num_str = args.number
period = args.period
trial = int(num_str)

path_cost = pd.read_csv(period + '_segment-cost.csv')
walk_links = pd.read_csv(root + 'GIS/int_tts_walk_time.csv')
walk_links['duration'] = round(walk_links['duration']/60).astype(int)
walk_links['gta06'] = walk_links['gta06'] + 1000

walk_o = walk_links.rename(columns = {'gta06': 'INT_ID_o', 'INT_ID':'INT_ID_d', 'duration':'cost'})
walk_d = walk_links.rename(columns = {'gta06': 'INT_ID_d', 'INT_ID':'INT_ID_o', 'duration':'cost'})

walk = walk_o.append(walk_d).copy()
walk['walk'] = True

cost = path_cost.drop(columns = ['std'])
cost['walk'] = False
cost = cost.append(walk)

list_dir = os.listdir(period + '/' + str(trial))

file_list = []
for file in list_dir:
    if file.split('_')[0] != 'int-path':
        continue
    file_list.append(file)

table = []
i = 0

for file in file_list:
    origin = file.split('_')[1]
    dest = file.split('_')[2].split('.')[0]
     
    try:
        df_o = pd.read_csv(period + '/' + str(trial) + '/' + file)
        
    except:
        print(trial, origin, dest)
        table.append([period, trial, origin, dest, 1, 0, 0, 0])
        continue
    
    
    if len(df_o) == 0:
        table.append([period, trial, origin, dest, 1, 0, 0, 0])
        continue
    
    df_o['sequence'] = df_o.groupby('path').cumcount()
    # creating links from int list
    df_d = df_o.copy()
    df_d['sequence'] = df_d['sequence'] - 1
    df_d = df_d[df_d['sequence'] >= 0]
    df_o = df_o.rename(columns = {'INT_ID':'INT_ID_o'})
    df_d = df_d.rename(columns = {'INT_ID':'INT_ID_d'})
    path_edges = df_o.merge(df_d).sort_values(by = ['path', 'sequence'])

    path_edges = path_edges.merge(cost, how = 'left')

    # all walking
    walk_path = path_edges.groupby('path').count()[['sequence']].copy()
    walk_path['walk_links'] = path_edges.groupby('path')['walk'].sum()

    walk_path_num = len(walk_path[walk_path['sequence'] == walk_path['walk_links']])

    # unique edges
    edges = path_edges[['INT_ID_o', 'INT_ID_d', 'cost', 'walk']].drop_duplicates().copy()


    edges = edges[edges['walk'] == False]
    # cost adjustments
    edges['cost'] = edges['cost'].fillna(0.5)

    edges['cost'] = np.where(edges['cost'] == 0, 0.5, edges['cost'])
    
    if walk_path_num > 0:
        n_routes = (path_edges['path'].max() + 1) - walk_path_num + 1
    else:
        n_routes = path_edges['path'].max() + 1

    if len(edges) == 0:
        # walking 
        table.append([period, trial, origin, dest, 1, n_routes, walk_path_num, n_routes])
        continue

    num = 0 
    denom = 0
    gamma = 0
        
    
    if n_routes == 1:
        gamma = 1
    else:
        for index, row in edges.iterrows():

            int_o = row['INT_ID_o']
            int_d = row['INT_ID_d']

            link_cost = row['cost']
            n_a = len(path_edges[(path_edges['INT_ID_o'] == int_o) & (path_edges['INT_ID_d'] == int_d)])

            iteration = (np.log(n_a) * link_cost) 
            denom = denom + np.log(n_routes) * link_cost
            num = num + iteration
        try:
            gamma = 1 - num/denom
        except:
            print(origin, dest)

            break
    if walk_path_num > 0:

        eff_paths = 1 + 1 + gamma * (n_routes - 1 - 1)

    else:

        eff_paths = 1 + gamma * (n_routes - 1)
    
    if i%500 == 0:
        print(i)
    
    i = i + 1
    
    if n_routes == 0:
        table.append([period, trial, origin, dest, 1, n_routes, 0, 0])
    else:
        table.append([period, trial, origin, dest, gamma, n_routes, walk_path_num, eff_paths])

df = pd.DataFrame.from_records(table, columns = ['period', 'trial', 'origin', 'destination', 'gamma', 'paths', 'walk_paths', 'eff_paths'])

df.to_csv('Path Cleaned/All/' + period + '_' + str(trial) + '_all-paths.csv', index = False)