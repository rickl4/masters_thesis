# -*- coding: utf-8 -*-
"""
Created on Wed Aug 11 11:52:38 2021

@author: Rick
"""

import pandas as pd
import igraph
import datetime
import random
import argparse
import csv


parser = argparse.ArgumentParser(description = 'Get Paths')
parser.add_argument('-n', '--number', help = 'bin number')
parser.add_argument('-p', '--period', help = 'path to graph')



args = parser.parse_args()
num_str = args.number
per = args.period
num_int = int(num_str)

print('running')
iteration_start = datetime.datetime.now()
G = igraph.Graph.Read_GraphML(f = '/Volumes/Data2/RST/notebook/networks/' + per + '-TE-16-8.graphml')

stop_times_od = pd.read_csv('/Volumes/Data2/RST/notebook/networks/' + per + '-TE-16-8.csv')[['INT_ID_o', 'INT_ID_d', 'route_short_name', 'node_o', 'node_d']]
stop_times_od = stop_times_od.rename(columns = {'route_short_name':'route'})



od_data = pd.read_csv('/Volumes/Data2/RST/notebook/TTS OD/TTS_TYPE.csv')
od_data['destination'] = od_data['destination'] + 1000
od_data['origin'] = od_data['origin'] + 1000


if per == 'EM':
    depart_hour = '-4-'
    tts_type = 'raw_em'
if per == 'AM':
    depart_hour = '-7-'
    tts_type = 'raw_am'
elif per =='PM':
    depart_hour = '-17-'
    tts_type = 'raw_pm'
elif per =='MD':
    depart_hour = '-11-'
    tts_type = 'raw_md'
elif per =='EV':
    depart_hour = '-20-'
    tts_type = 'raw_ev'

bc_weighted = pd.read_csv('/Volumes/Data2/RST/notebook/BC Results Notebooks/bc_mode_edge.csv')
bc_weighted = bc_weighted[bc_weighted['type'] == tts_type].sort_values(by = 'weighted', ascending = False
                                                                    ).reset_index().drop(columns = 'index')



minute = random.randint(0,9)
minute = minute + num_int * 10
rand_time = depart_hour + str(minute)


node_data = od_data[od_data['type'] == tts_type][['origin', 'destination']].copy()
node_data['origin'] = node_data['origin'].astype(str)
node_data['destination'] = node_data['destination'].astype(str)

node_data['o_node'] = node_data['origin'] + '-0' + rand_time


node_data['d_node'] = node_data['destination'] + '-0-99-99'
node_data = node_data.reset_index()



G_copy = G.copy()

node_key_table = []

for i in G_copy.vs:
    node_key_table.append([i.index,  i['id']])
node_df_new = pd.DataFrame.from_records(node_key_table, columns = ['index', 'node_id'])

node_df_new['INT_ID'] = node_df_new['node_id'].str.split('-', expand = True)[0].astype(int)

def travel_time_calc(mode):
    
    removed_edge = 0
    iteration = 0
    
    bc_mode = bc_weighted[bc_weighted['edge_type'] == mode].copy()
    
    while removed_edge <= len(bc_mode):
        
        
        G_copy = G.copy()
        
        if iteration == 0:
            removed_edge = 0
        elif iteration <= 25:
            removed_edge = removed_edge + 1
            
        elif 25 < iteration <= 50:
            removed_edge = removed_edge + 5
            
        elif 50 < iteration <= 75:
            removed_edge = removed_edge + 10
            
        elif 75 < iteration <= 100:
            removed_edge = removed_edge + 25
        elif 100 < iteration <= 150:
            removed_edge = removed_edge + 50 
        else:
            removed_edge = removed_edge + 100
        
        edge_pairs = bc_mode.head(removed_edge).merge(stop_times_od).merge(node_df_new[['node_id', 'index']], left_on = ['node_o'], right_on = 'node_id')
    
        edge_pairs = edge_pairs.rename(columns = {'index': 'index_o'})
        edge_pairs = edge_pairs.drop(columns = ['node_id'])
        edge_pairs = edge_pairs.merge(node_df_new[['node_id', 'index']], left_on = ['node_d'], right_on = 'node_id')
        edge_pairs = edge_pairs.rename(columns = {'index': 'index_d'})
        edge_pairs = edge_pairs.drop(columns = ['node_id'])
    
        del_edge = G.get_eids(edge_pairs[['index_o', 'index_d']].values.tolist(), directed = True)
        G_copy.delete_edges(del_edge)
        
        o_list_new = list(node_df_new[node_df_new['node_id'].isin(node_data['o_node'])]['index'])
        d_list_new = list(node_df_new[node_df_new['node_id'].isin(node_data['d_node'])]['index'])
        
        out_all = G_copy.shortest_paths(o_list_new, d_list_new, weights = 'cost',  mode = 'out')
        table = []
        for i in range(len(o_list_new)):
            temp_lst = out_all[i]
            for j in range(len(d_list_new)):
                table.append([o_list_new[i], d_list_new[j], temp_lst[j], iteration, mode])
                
        temp_df = pd.DataFrame.from_records(table, columns = ['index_o', 'index_d', 'travel_time', 'iteration', 'edge_type'])
        temp_df = temp_df.merge(node_df_new[['node_id', 'index', 'INT_ID']], left_on = ['index_o'], right_on = ['index'])
        temp_df = temp_df.rename(columns = {'node_id':'o_node', 'INT_ID':'origin'})[['o_node', 'index_d', 'origin','travel_time', 'iteration','edge_type']]
        temp_df = temp_df.merge(node_df_new[['node_id', 'index','INT_ID']], left_on = ['index_d'], right_on = ['index'])
        temp_df = temp_df.rename(columns = {'node_id':'d_node','INT_ID':'destination'})[['o_node', 'd_node', 'origin','destination','travel_time', 'iteration','edge_type']]
        temp_df = temp_df.merge(node_data[['o_node', 'd_node']])
        temp_df = temp_df[temp_df['origin'] != temp_df['destination']]
        
        if iteration == 0:
            importance_df = temp_df.copy()
        else:
            importance_df = importance_df.append(temp_df)
    
        
        if iteration%10 == 0:
            elapsed = datetime.datetime.now() - iteration_start
            with open(per + '/' + num_str + '-ge-mode-log.txt', 'a', newline='') as f:
                writer = csv.writer(f, delimiter=',')
                writer.writerow([str(elapsed), str(iteration), str(removed_edge), str(G_copy.ecount()), mode])
                
        if iteration%50 == 0:
            importance_df.to_csv(per + '/' + num_str + '-GE-' + per + '-mode-' + mode + '-raw.csv', index = False)
            
        iteration = iteration + 1
        
            
    end = datetime.datetime.now() - iteration_start
    print(end)
    
    importance_df.to_csv(per + '/' + num_str + '-GE-' + per + '-mode-' + mode + '-raw.csv', index = False)

mode_list = list(bc_weighted['edge_type'].drop_duplicates())

for mode in mode_list:
    
    # if mode in ['Streetcar Route', 'Inner Subway Station', 'Outer Subway Station']:
    #     continue

    # if mode in ['Bus Route', 'Frequent Bus Route']:
    #     continue
    
    travel_time_calc(mode)


