
import pandas as pd
import itertools
import igraph
import argparse


parser = argparse.ArgumentParser(description = 'Get Paths')
parser.add_argument('-n', '--number', help = 'bin number')
parser.add_argument('-p', '--period', help = 'period')
parser.add_argument('-s', '--start', help = 'start zone')


args = parser.parse_args()
num_str = args.number
period = args.period
trial = int(num_str)
start = int(args.start)

root = '/Volumes/Data2/RST/notebook/'
#root = 'D:/RST/notebook/'
#root = 'C:/Users/Rick/Documents/RST/notebook/'

G = igraph.Graph.Read_GraphML(f = root + 'networks/' + period + '-TE-16-8.graphml')


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

node_data = pd.read_csv(period + '/' + str(trial) + '/od_travel_times-' + period + '-' + str(trial) + '.csv')

node_data = node_data[node_data['origin'] >= start].copy()


for index, row in node_data.iterrows():

    origin = row['o_node']
    dest = row['d_node']

    o = G.vs.select(id_eq = origin)[0]
    d = G.vs.select(id_eq = dest)[0]
    
    
    o_str = str(row['origin'])
    d_str = str(row['destination'])



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
    route_df.to_csv(period + '/' + str(trial) + '/shortest-route-path_'+ o_str + '_' + d_str + '.csv', index = False)
    

        
    table_df = pd.DataFrame(pd.Series(table_sort), columns = ['INT_ID']).reset_index().rename(
        columns = {'index':'path'}).explode('INT_ID')
    table_df.to_csv(period + '/' + str(trial) + '/shortest-int-path_'+ o_str + '_' + d_str + '.csv', index = False)



    del table_df
    del route_df
    del table
    del route_table
    del out
    del route_table_sort
    del table_sort




