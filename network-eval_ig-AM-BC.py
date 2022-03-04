import pandas as pd
import numpy as np
import itertools
import igraph
import sys
import collections
import datetime
import random
import concurrent.futures



G_orig = igraph.Graph.Read_GraphML(f = 'networks/AM-TE-16.graphml')


stop_times_od = pd.read_csv('networks/AM-TE-16.csv')

stop_times_od.head()

od_data = pd.read_csv('TTS OD/LICO_TTS.csv')
od_data['origin'] = od_data['origin'] + 1000
od_data['destination'] = od_data['destination'] + 1000


depart_hour = '-7-'
rand_time = []

for i in range(6):
    minute = random.randint(0,9)
    minute = minute + i*10
    rand_time.append(depart_hour + str(minute))


node_key_table = []

for i in G_orig.vs:
    node_key_table.append([i.index,  i['id']])
node_df = pd.DataFrame.from_records(node_key_table, columns = ['index', 'node_id'])



node_df['INT_ID'] = node_df['node_id'].str.split('-', expand = True)[0]



node_df['node_time'] = node_df['node_id'].str.split('-', expand = True)[0] + '-' + node_df['node_id'].str.split('-', expand = True)[2] + '-' + node_df['node_id'].str.split('-', expand = True)[3]
node_dict = node_df[['INT_ID']].to_dict()['INT_ID']
time_dict = node_df[['node_time']].to_dict()['node_time']

od_list = []
for period in range(6):
    
    node_data = od_data[od_data['type'] == 'raw_am'][['origin', 'destination']].copy()
    node_data['origin'] = node_data['origin'].astype(str)
    node_data['destination'] = node_data['destination'].astype(str)
    node_data['o_node'] = node_data['origin'] + '-0' + rand_time[period]
    node_data['d_node'] = node_data['destination'] + '-0-99-99'

    od_list.append(node_data[['o_node', 'd_node']].values.tolist())


param = []
for i in range(6):
    param.append((i, od_list[i], G_orig.copy()))


def bc_shortest_paths(param):

    j = 0
    thread = param[0]
    od_list_subprocess = param[1]
    G_subprocess = param[2]
    
    for pair in od_list_subprocess:

        o_node = pair[0]
        d_node = pair[1]

        out = G_subprocess.get_all_shortest_paths(G_subprocess.vs.select(id_eq = pair[0])[0], 
                                       G_subprocess.vs.select(id_eq = pair[1])[0], weights = 'cost',  mode = 'out')

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
        single_time_df = pd.DataFrame(single_time_path.items(), columns = ['node_time', 'tv_bc_single'])

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
        edge_df = pd.DataFrame.from_records(edge_list, columns = ['o_node_time', 'd_node_time', 'index_from', 'index_to'])

        edge_df = edge_df.merge(node_df, left_on = ['index_from'], right_on = ['index'])
        edge_df = edge_df.rename(columns = {'INT_ID':'INT_ID_o', 'node_id':'node_o'})
        edge_df = edge_df.drop(columns = ['index'])
        edge_df = edge_df.merge(node_df, left_on = ['index_to'], right_on = ['index'])
        edge_df = edge_df.rename(columns = {'INT_ID':'INT_ID_d', 'node_id':'node_d'})
        edge_df = edge_df.drop(columns = ['index'])

        edge_df = edge_df[['o_node_time', 'd_node_time', 'node_o', 'node_d', 'INT_ID_o', 'INT_ID_d']]
        edge_df['bc_single'] = True
        edge_df = edge_df.groupby(['o_node_time', 'd_node_time', 'node_o', 'node_d', 'INT_ID_o', 'INT_ID_d']).count().reset_index()
        edge_df['bc_single'] = edge_df['bc_single']/len(out)

        if j == 0:
            bc_df = single_df 
            tvbc_df = single_time_df
            edge_df_all = edge_df
        else:
            bc_df = bc_df.append(single_df)
            tvbc_df = tvbc_df.append(single_time_df)
            edge_df_all = edge_df_all.append(edge_df) 

        j = j + 1

        if j%100 == 0:
            print(thread, j)

    
    return  [bc_df, tvbc_df, edge_df_all]



iteration_start = datetime.datetime.now()
print(iteration_start)

with concurrent.futures.ThreadPoolExecutor() as executor:
    thread_lst = executor.map(bc_shortest_paths, param)
    result = list(thread_lst)
    
end = datetime.datetime.now() - iteration_start
print(end)

for c in range(6):
    
    if c == 0:
        bc_df = result[c][0]
        edge_df_all = result[c][1]
    else:
        bc_df = bc_df.append(result[c][0])
        edge_df_all = edge_df_all.append(result[c][1])

bc_df['o_node'] = bc_df['o_node_time'].str.split('-', expand = True)[0]
bc_df['d_node'] = bc_df['d_node_time'].str.split('-', expand = True)[0]


key_table = pd.DataFrame.from_records(od_list, columns = ['o_node_time', 'd_node_time'])

key_table['o_node'] = key_table['o_node_time'].str.split('-', expand = True)[0]
key_table['d_node'] = key_table['d_node_time'].str.split('-', expand = True)[0]

key_table['key'] = 0
int_table = bc_df[['INT_ID']].drop_duplicates()
int_table['key'] = 0
key_table = key_table.merge(int_table, how = 'outer')
bc_filled = key_table.merge(bc_df, how = 'left')
bc_filled['bc_single'] = bc_filled['bc_single'].fillna(0)
bc_filled.to_csv('networks/EM/BC-AM_raw.csv', index = False)



bc_avg = bc_filled.groupby(['o_node', 'd_node','INT_ID']).agg({'bc_single':'mean'})
bc_avg = bc_avg[bc_avg['bc_single']>0]
bc_avg = bc_avg.reset_index()
bc_avg.to_csv('networks/EM/BC-AM_avg-time.csv', index = False)



edge_df_filtered = edge_df_all.merge(stop_times_od[['node_o', 'node_d']], how = 'inner').copy()

key_links = edge_df_filtered[['INT_ID_o', 'INT_ID_d']].drop_duplicates().copy()
key_links['key'] = 0


key_pairs = edge_df_filtered[['o_node_time', 'd_node_time']].drop_duplicates().copy()
key_pairs['key'] = 0



key = key_pairs.merge(key_links, how = 'outer')



key = key.merge(edge_df_filtered, how = 'left')




key['bc_single'] = key['bc_single'].fillna(0)



edge_bc_avg = key[['o_node_time', 'd_node_time', 'INT_ID_o', 'INT_ID_d', 'bc_single']].copy()



edge_bc_avg['o_node'] = edge_bc_avg['o_node_time'].str.split('-', expand = True)[0]
edge_bc_avg['d_node'] = edge_bc_avg['d_node_time'].str.split('-', expand = True)[0]




edge_bc_avg.to_csv('networks/EM/BC-AM_edge-raw.csv', index = False)


edge_bc_avg = edge_bc_avg.groupby(['o_node', 'd_node', 'INT_ID_o', 'INT_ID_d']).agg({'bc_single':'mean'})



edge_bc_avg = edge_bc_avg[edge_bc_avg['bc_single']>0]
edge_bc_avg = edge_bc_avg.reset_index()



edge_bc_avg.to_csv('networks/EM/BC-AM_edge-avg-time.csv', index = False)





