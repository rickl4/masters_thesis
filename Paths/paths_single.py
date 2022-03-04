
import pandas as pd
import numpy as np
import itertools
import igraph
import sys
import collections
import datetime
import random
import argparse
import itertools



parser = argparse.ArgumentParser(description = 'Get Paths')
parser.add_argument('-n', '--number', help = 'bin number')
parser.add_argument('-p', '--period', help = 'path to graph')


args = parser.parse_args()
num_str = args.number
period = args.period
trial = int(num_str)


root = '/Volumes/Data2/RST/notebook/'
#root = 'D:/RST/notebook/'
#root = 'C:/Users/Rick/Documents/RST/notebook/'

G_tt = igraph.Graph.Read_GraphML(f = root + 'networks/' + period +'-TE-16-8.graphml')


od_data = pd.read_csv(root + 'TTS OD/LICO_TTS.csv')
od_data['origin'] = od_data['origin'] + 1000
od_data['destination'] = od_data['destination'] + 1000

if period == 'EM':
    depart_hour = '-4-'
    tts_type = 'raw_em'
elif period == 'AM':
    depart_hour = '-7-'
    tts_type = 'raw_am'
elif period =='PM':
    depart_hour = '-17-'
    tts_type = 'raw_pm'
elif period =='MD':
    depart_hour = '-11-'
    tts_type = 'raw_md'
elif period =='EV':
    depart_hour = '-20-'
    tts_type = 'raw_ev'

rand_time = []

for i in range(6):
    minute = random.randint(0,9)
    minute = minute + i*10
    rand_time.append(depart_hour + str(minute))
rand_time[0]

node_key_table = []

for i in G_tt.vs:
    node_key_table.append([i.index,  i['id']])
node_df = pd.DataFrame.from_records(node_key_table, columns = ['index', 'node_id'])



node_df['INT_ID'] = node_df['node_id'].str.split('-', expand = True)[0]
node_df['node_time'] = node_df['node_id'].str.split(
    '-', expand = True)[0] + '-' + node_df['node_id'].str.split(
    '-', expand = True)[2] + '-' + node_df['node_id'].str.split('-', expand = True)[3]
node_dict = node_df[['INT_ID']].to_dict()['INT_ID']
time_dict = node_df[['node_time']].to_dict()['node_time']



node_data = od_data[od_data['type'] == 'raw_' + period.lower()][['origin', 'destination']].copy()
node_data['origin'] = node_data['origin'].astype(str)
node_data['destination'] = node_data['destination'].astype(str)
node_data['o_node'] = node_data['origin'] + '-0' + rand_time[trial]
node_data['d_node'] = node_data['destination'] + '-0-99-99'



o_list = list(node_df[node_df['node_id'].isin(node_data['o_node'])]['index'])
d_list = list(node_df[node_df['node_id'].isin(node_data['d_node'])]['index'])

out_all = G_tt.shortest_paths(o_list, d_list, weights = 'cost',  mode = 'out')



table = []
for i in range(len(o_list)):
    temp_lst = out_all[i]
    for j in range(len(d_list)):
        table.append([o_list[i], d_list[j], temp_lst[j]])



base_time_df = pd.DataFrame.from_records(table, columns = ['o_id', 'd_id', 'base_time'])
base_time_df = base_time_df.merge(node_df, left_on = ['o_id'], right_on = 'index', how = 'left').rename(
    columns = {'node_id':'o_node'})[['o_node','d_id','base_time']].merge(
    node_df, left_on = ['d_id'], right_on = 'index', how = 'left').rename(
    columns = {'node_id':'d_node'})[['o_node','d_node','base_time']]
node_data = node_data.merge(base_time_df, how = 'left')


node_data.sort_values(by = 'base_time')


# removing np.inf

node_data = node_data[node_data['base_time'] != np.inf]
node_data.sort_values(by = 'base_time')


node_data['buffer_length'] = np.where(node_data['base_time'] < 30, 5, 5 + (5/90 * (node_data['base_time'] - 30)))
node_data['buffer_length'] = np.where(node_data['base_time'] < 120, node_data['buffer_length'], 10)



node_data['cutoff_time'] = node_data['buffer_length'] + node_data['base_time']


node_data['arrival_time'] = (node_data['o_node'].str.split('-', expand = True)[3].astype(float) + node_data['cutoff_time']).astype(int)


node_data['arrival_hour'] = (node_data['arrival_time']/60).astype(int) + int(depart_hour.split('-')[1])

node_data['arrival_hour'] = np.where(node_data['arrival_hour'] >=24, node_data['arrival_hour']-24, node_data['arrival_hour'])
node_data['arrival_minute'] = node_data['arrival_time'] - (node_data['arrival_hour'] - int(depart_hour.split('-')[1]))*60


node_data['constrained_node'] = node_data['destination'].astype(str) + '-9999-' + node_data['arrival_hour'].astype(
    str) + '-' + node_data['arrival_minute'].astype(int).astype(str)

node_data.to_csv(period + '/' + str(trial) + '/od_travel_times-' + period + '-' + str(trial) + '.csv', index = False)

del G_tt
del node_df

G = igraph.Graph.Read_GraphML(f = root + 'networks/' + period + '-TE-16-5-constrained.graphml')


del node_key_table

node_key_table = []

for i in G.vs:
    node_key_table.append([i.index,  i['id']])
node_df_new = pd.DataFrame.from_records(node_key_table, columns = ['index', 'node_id'])

del node_key_table


node_df_new['INT_ID'] = node_df_new['node_id'].str.split('-', expand = True)[0]
node_df_new['route'] = node_df_new['node_id'].str.split('-', expand = True)[1]


node_df_new['route_int'] = node_df_new['INT_ID'] + '-' + node_df_new['route']



node_dict_new = node_df_new[['INT_ID']].to_dict()['INT_ID']
route_dict_new = node_df_new[['INT_ID', 'route']].to_dict()['route']



node_data[node_data['cutoff_time'] < 170].sort_values(by = 'cutoff_time').tail()


for index, row in node_data.iterrows():

    origin = row['o_node']
    dest = row['constrained_node']

    o = G.vs.select(id_eq = origin)[0]
    d = G.vs.select(id_eq = dest)[0]
    
    
    o_str = row['origin']
    d_str = row['destination']



    out = G.get_all_shortest_paths(o, d, weights = 'cost',  mode = 'out')
    print(period, trial, o_str, d_str, len(out))
    
    table = []
    route_table = []
    
    for path in out:
        temp_list = list(dict.fromkeys(list(map(node_dict_new.get, path))))
        route_list = list(dict.fromkeys(list(map(route_dict_new.get, path))))

        table.append(temp_list)
        route_table.append(route_list)

    
    route_table.sort()
    route_table_sort = list(x for x,_ in itertools.groupby(route_table))


    table.sort()
    table_sort = list(x for x,_ in itertools.groupby(table))



    route_df = pd.DataFrame(pd.Series(route_table_sort), columns = ['route']).reset_index().rename(
        columns = {'index':'path'}).explode('route')
    route_df['route'] = route_df['route'].astype(int)
    route_df = route_df[~route_df['route'].isin([0,9999])]
    route_df.to_csv(period + '/' + str(trial) + '/route-path_'+ o_str + '_' + d_str + '.csv', index = False)
    

        
    table_df = pd.DataFrame(pd.Series(table_sort), columns = ['INT_ID']).reset_index().rename(
        columns = {'index':'path'}).explode('INT_ID')
    table_df.to_csv(period + '/' + str(trial) + '/int-path_'+ o_str + '_' + d_str + '.csv', index = False)



    del table_df
    del route_df
    del table
    del route_table
    del out
    del table_sort
    del route_table_sort



