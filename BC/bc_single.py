


import pandas as pd
import itertools
import igraph
import collections
import datetime
import random
import argparse
import numpy as np


parser = argparse.ArgumentParser(description = 'Get Paths')
parser.add_argument('-n', '--number', help = 'bin number')
parser.add_argument('-p', '--period', help = 'path to graph')



args = parser.parse_args()
num_str = args.number
per = args.period
num_int = int(num_str)

print('running')

G = igraph.Graph.Read_GraphML(f = '/Volumes/Data2/RST/notebook/networks/' + per + '-TE-16-8.graphml')


G_orig = G.copy()


stop_times_od = pd.read_csv('/Volumes/Data2/RST/notebook/networks/' + per + '-TE-16-8.csv')





od_data = pd.read_csv('/Volumes/Data2/RST/notebook/TTS OD/LICO_TTS.csv')
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



minute = random.randint(0,9)
minute = minute + num_int * 10
rand_time = depart_hour + str(minute)


node_key_table = []

for i in G.vs:
    node_key_table.append([i.index,  i['id']])
node_df = pd.DataFrame.from_records(node_key_table, columns = ['index', 'node_id'])


node_df['INT_ID'] = node_df['node_id'].str.split('-', expand = True)[0]
node_df['node_time'] = node_df['node_id'].str.split('-', expand = True)[0] + '-' + node_df['node_id'].str.split('-', expand = True)[2] + '-' + node_df['node_id'].str.split('-', expand = True)[3]
node_dict = node_df[['INT_ID']].to_dict()['INT_ID']
time_dict = node_df[['node_time']].to_dict()['node_time']


node_data = od_data[od_data['type'] == tts_type][['origin', 'destination']].copy()
node_data['origin'] = node_data['origin'].astype(str)
node_data['destination'] = node_data['destination'].astype(str)
node_data['o_node'] = node_data['origin'] + '-0' + rand_time
node_data['d_node'] = node_data['destination'] + '-0-99-99'

od_list = node_data[['o_node', 'd_node']].values.tolist()



j = 0

iteration_start = datetime.datetime.now()
    
for pair in od_list:

    o_node = pair[0]
    d_node = pair[1]
    try:
        out = G.get_all_shortest_paths(G.vs.select(id_eq = pair[0])[0], 
                                       G.vs.select(id_eq = pair[1])[0], weights = 'cost',  mode = 'out')
    
    
        table = []
        time_table = []
        for path in out:
            temp_list = list(set(map(node_dict.get, path)))
            time_list = list(set(map(time_dict.get, path)))
            table.append(temp_list)
            time_table.append(time_list)
    
        node_path = list(itertools.chain.from_iterable(table))
        time_path = list(itertools.chain.from_iterable(time_table))
    
        single_path = collections.Counter(node_path)
        single_time_path = collections.Counter(time_path)
    
        single_path = {k: v / len(out) for k, v in dict(single_path).items()}
        single_time_path = {k: v / len(out) for k, v in dict(single_time_path).items()}
    
        single_df = pd.DataFrame(single_path.items(), columns = ['INT_ID', 'bc_single'])
        single_time_df = pd.DataFrame(single_time_path.items(), columns = ['node_id', 'tv_bc_single'])
    
        single_df['o_node_time'] = o_node
        single_df['d_node_time'] = d_node
    
        single_time_df['o_node_time'] = o_node
        single_time_df['d_node_time'] = d_node
        
        # edge BC
        edge_list = []
        for path in out:
            flag_start = 0
            for node in path:
                if flag_start == 0:
                    flag_start = flag_start + 1
                    from_node = node
                    continue
                to_node = node
                edge_list.append([o_node, d_node, from_node, to_node])
                from_node = to_node
        total_paths = len(out)
        edge_df = pd.DataFrame.from_records(edge_list, columns = ['o_node_time', 'd_node_time', 'index_from', 'index_to'])
    
        edge_df = edge_df.merge(node_df, left_on = ['index_from'], right_on = ['index'])
        edge_df = edge_df.rename(columns = {'INT_ID':'INT_ID_o', 'node_id':'node_o'})
        edge_df = edge_df.drop(columns = ['index'])
        edge_df = edge_df.merge(node_df, left_on = ['index_to'], right_on = ['index'])
        edge_df = edge_df.rename(columns = {'INT_ID':'INT_ID_d', 'node_id':'node_d'})
        edge_df['route_o'] = edge_df['node_o'].str.split('-', expand = True)[1]
        edge_df['route_d'] = edge_df['node_d'].str.split('-', expand = True)[1]
    
        edge_df['route'] = np.where(edge_df['route_o'] == edge_df['route_d'], edge_df['route_o'], np.nan)
        edge_df['route'] = edge_df['route'].astype(float)
        edge_df['route'] = np.where(edge_df['route']!=0, edge_df['route'], np.nan)
    
        edge_df = edge_df.drop(columns = ['index', 'route_o', 'route_d'])
        
        edge_df = edge_df[['o_node_time', 'd_node_time', 'INT_ID_o', 'INT_ID_d', 'route']]
        edge_df['bc_single'] = True
        edge_df = edge_df.groupby(['o_node_time', 'd_node_time', 'INT_ID_o', 'INT_ID_d', 'route']).count().reset_index()
        edge_df['bc_single'] = edge_df['bc_single']/len(out)
    
        if j == 0:
            bc_df = single_df 
            tvbc_df = single_time_df
            edge_df_all = edge_df
        else:
            bc_df = bc_df.append(single_df)
            tvbc_df = tvbc_df.append(single_time_df)
            edge_df_all = edge_df_all.append(edge_df) 
        
    except:
        print(pair)
        continue
    j = j + 1
    
    if j%50 == 0:
        print(j)
    
end = datetime.datetime.now() - iteration_start
print(end)


bc_df['o_node'] = bc_df['o_node_time'].str.split('-', expand = True)[0]
bc_df['d_node'] = bc_df['d_node_time'].str.split('-', expand = True)[0]

# key_table = pd.DataFrame.from_records(od_list, columns = ['o_node_time', 'd_node_time'])
# key_table['o_node'] = key_table['o_node_time'].str.split('-', expand = True)[0]
# key_table['d_node'] = key_table['d_node_time'].str.split('-', expand = True)[0]
# key_table['key'] = 0

# int_table = bc_df[['INT_ID']].drop_duplicates()
# int_table['key'] = 0
# key_table = key_table.merge(int_table, how = 'outer')

# bc_filled = key_table.merge(bc_df, how = 'left')
# bc_filled['bc_single'] = bc_filled['bc_single'].fillna(0)
# bc_filled.to_csv(per + '/' + num_str + '-BC-' + per +'_raw.csv', index = False)

bc_df.to_csv(per + '/' + num_str + '-BC-' + per +'_raw.csv', index = False)





edge_df_filtered = edge_df_all[~edge_df_all['route'].isna()]
# key_links = edge_df_filtered[['INT_ID_o', 'INT_ID_d']].drop_duplicates().copy()
# key_links['key'] = 0
# key_pairs = edge_df_filtered[['o_node_time', 'd_node_time']].drop_duplicates().copy()
# key_pairs['key'] = 0

# key = key_pairs.merge(key_links, how = 'outer')
# key = key.merge(edge_df_filtered, how = 'left')
# key['bc_single'] = key['bc_single'].fillna(0)

# edge_bc_avg = key[['o_node_time', 'd_node_time', 'INT_ID_o', 'INT_ID_d', 'bc_single']].copy()
# edge_bc_avg['o_node'] = edge_bc_avg['o_node_time'].str.split('-', expand = True)[0]
# edge_bc_avg['d_node'] = edge_bc_avg['d_node_time'].str.split('-', expand = True)[0]
# edge_bc_avg.to_csv(per + '/' +num_str + '-BC-' + per + '_edge-raw.csv', index = False)
edge_df_filtered.to_csv(per + '/' +num_str + '-BC-' + per + '_edge-raw.csv', index = False)



tvbc_df['o_node'] = tvbc_df['o_node_time'].str.split('-', expand = True)[0]
tvbc_df['d_node'] = tvbc_df['d_node_time'].str.split('-', expand = True)[0]

# tvkey_table = pd.DataFrame.from_records(od_list, columns = ['o_node_time', 'd_node_time'])
# tvkey_table['o_node'] = tvkey_table['o_node_time'].str.split('-', expand = True)[0]
# tvkey_table['d_node'] = tvkey_table['d_node_time'].str.split('-', expand = True)[0]
# tvkey_table['key'] = 0
# tvint_table = tvbc_df[['node_id']].drop_duplicates()
# tvint_table['key'] = 0

# tvkey_table = tvkey_table.merge(tvint_table, how = 'outer')

# tvbc_filled = tvkey_table.merge(tvbc_df, how = 'left')
tvbc_filled = tvbc_df
# tvbc_filled['tv_bc_single'] = tvbc_filled['tv_bc_single'].fillna(0)
tvbc_filled.to_csv(per + '/' + num_str + '-BC-' + per + '_tv-raw.csv', index = False)




