#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
import itertools
import igraph
import sys
import collections
import datetime
import random


# In[2]:


G = igraph.Graph.Read_GraphML(f = 'networks/AM-TE-16-10.graphml')


# In[3]:


period = 'raw_am'


# In[4]:


od_data = pd.read_csv('TTS OD/LICO_TTS.csv')
od_data['origin'] = od_data['origin'] + 1000
od_data['destination'] = od_data['destination'] + 1000
od_data


# In[5]:


stop_times_od = pd.read_csv('networks/AM-TE-16-10.csv')[['INT_ID_o', 'INT_ID_d', 'route_short_name', 'node_o', 'node_d']]
stop_times_od = stop_times_od.rename(columns = {'route_short_name':'route'})
stop_times_od


# In[6]:


stop_times_od[['INT_ID_o', 'INT_ID_d', 'route']].drop_duplicates()


# In[7]:


bc_weighted = pd.read_csv('BC Results Notebooks/bc_weighted_edge.csv')
bc_weighted = bc_weighted[bc_weighted['type'] == period].sort_values(by = 'weighted', ascending = False
                                                                    ).reset_index().drop(columns = 'index')
bc_weighted


# In[8]:


node_data = od_data[od_data['type'] == period][['origin', 'destination']].copy()
node_data['origin'] = node_data['origin'].astype(str)
node_data['destination'] = node_data['destination'].astype(str)

#node_data['o_node'] = node_data['origin'] + '-0' + rand_time[5]
#for limit testing
node_data['o_node'] = node_data['origin'] + '-0-7-59'

node_data['d_node'] = node_data['destination'] + '-0-99-99'
node_data = node_data.reset_index()
node_data


# In[23]:


len(bc_weighted)


# In[68]:


get_ipython().run_cell_magic('time', '', "\nG_copy = G.copy()\nnode_key_table = []\n\nfor i in G_copy.vs:\n    node_key_table.append([i.index,  i['id']])\nnode_df_new = pd.DataFrame.from_records(node_key_table, columns = ['index', 'node_id'])\n\nnode_df_new['INT_ID'] = node_df_new['node_id'].str.split('-', expand = True)[0].astype(int)\n\niteration = 300\nfor index, row in bc_weighted.iterrows():\n    G_copy = G.copy()\n    \n    node_key_table = []\n\n    removed_edge = ((iteration-300) * 20)+1600\n    \n    if removed_edge > len(bc_weighted):\n        removed_edge = len(bc_weighted)\n    \n    edge_pairs = bc_weighted.head(removed_edge).merge(stop_times_od).merge(node_df_new[['node_id', 'index']], left_on = ['node_o'], right_on = 'node_id')\n\n    edge_pairs = edge_pairs.rename(columns = {'index': 'index_o'})\n    edge_pairs = edge_pairs.drop(columns = ['node_id'])\n    edge_pairs = edge_pairs.merge(node_df_new[['node_id', 'index']], left_on = ['node_d'], right_on = 'node_id')\n    edge_pairs = edge_pairs.rename(columns = {'index': 'index_d'})\n    edge_pairs = edge_pairs.drop(columns = ['node_id'])\n\n    del_edge = G.get_eids(edge_pairs[['index_o', 'index_d']].values.tolist(), directed = True)\n    G_copy.delete_edges(del_edge)\n    \n#     for i in G_copy.vs:\n#         node_key_table.append([i.index,  i['id']])\n#     node_df_new = pd.DataFrame.from_records(node_key_table, columns = ['index', 'node_id'])\n\n#     node_df_new['INT_ID'] = node_df_new['node_id'].str.split('-', expand = True)[0].astype(int)\n\n    o_list_new = list(node_df_new[node_df_new['node_id'].isin(node_data['o_node'])]['index'])\n    d_list_new = list(node_df_new[node_df_new['node_id'].isin(node_data['d_node'])]['index'])\n    \n    out_all = G_copy.shortest_paths(o_list_new, d_list_new, weights = 'cost',  mode = 'out')\n    table = []\n    for i in range(len(o_list_new)):\n        temp_lst = out_all[i]\n        for j in range(len(d_list_new)):\n            table.append([o_list_new[i], d_list_new[j], temp_lst[j], iteration])\n            \n    temp_df = pd.DataFrame.from_records(table, columns = ['index_o', 'index_d', 'travel_time', 'iteration'])\n    temp_df = temp_df.merge(node_df_new[['node_id', 'index', 'INT_ID']], left_on = ['index_o'], right_on = ['index'])\n    temp_df = temp_df.rename(columns = {'node_id':'o_node', 'INT_ID':'origin'})[['o_node', 'index_d', 'origin','travel_time', 'iteration']]\n    temp_df = temp_df.merge(node_df_new[['node_id', 'index','INT_ID']], left_on = ['index_d'], right_on = ['index'])\n    temp_df = temp_df.rename(columns = {'node_id':'d_node','INT_ID':'destination'})[['o_node', 'd_node', 'origin','destination','travel_time', 'iteration']]\n    temp_df = temp_df.merge(node_data[['o_node', 'd_node']])\n    temp_df = temp_df[temp_df['origin'] != temp_df['destination']]\n    \n    if iteration == 300:\n        importance_df = temp_df.copy()\n    else:\n        importance_df = importance_df.append(temp_df)\n    iteration = iteration + 1\n    \n    if iteration%10 == 0:\n        print(iteration, G_copy.vcount(), G_copy.ecount())\n    \n    if iteration == 320:\n        break")


# In[70]:


od_data = od_data[od_data['type'] == period]
total_trips = od_data['total'].sum()
total_trips


# In[57]:


two = importance_df[importance_df['iteration']>250][['o_node', 'd_node', 'origin', 'destination', 'travel_time', 'iteration']]


# In[58]:


one


# In[59]:


two


# In[71]:


importance_df = importance_df.merge(od_data)
importance_df['ge'] =  (1/importance_df['travel_time'])*(importance_df['total']/total_trips)


# In[33]:


baseline_ge = importance_df[importance_df['iteration']==0]['ge'].sum()
baseline_ge


# In[72]:


(importance_df.groupby('iteration').sum()['ge']*100/baseline_ge).plot()


# In[30]:


importance_df.groupby('iteration').sum()['travel_time'].plot()


# In[31]:


importance_df.groupby('iteration').sum()


# # Individual Iterations

# In[371]:


G_copy = G.copy()


# In[372]:


bc_weighted


# In[373]:


edge_pairs = bc_weighted.head(2000).merge(stop_times_od).merge(node_df[['node_id', 'index']], left_on = ['node_o'], right_on = 'node_id')
edge_pairs


# In[374]:


# edge_pairs = stop_times_od.merge(node_df[['node_id', 'index']], left_on = ['node_o'], right_on = 'node_id')
# edge_pairs


# In[375]:



edge_pairs = edge_pairs.rename(columns = {'index': 'index_o'})
edge_pairs = edge_pairs.drop(columns = ['node_id'])
edge_pairs = edge_pairs.merge(node_df[['node_id', 'index']], left_on = ['node_d'], right_on = 'node_id')
edge_pairs = edge_pairs.rename(columns = {'index': 'index_d'})
edge_pairs = edge_pairs.drop(columns = ['node_id'])
edge_pairs


# In[376]:


G_copy.vcount(), G_copy.ecount()


# In[377]:


del_edge = G.get_eids(edge_pairs[['index_o', 'index_d']].values.tolist(), directed = True)


# In[378]:


G_copy.delete_edges(del_edge)


# In[379]:


G_copy.vcount(), G_copy.ecount()


# In[380]:


# G_copy.delete_vertices(19800)


# In[381]:


get_ipython().run_cell_magic('time', '', "node_key_table = []\n\nfor i in G_copy.vs:\n    node_key_table.append([i.index,  i['id']])\nnode_df_new = pd.DataFrame.from_records(node_key_table, columns = ['index', 'node_id'])\n\nnode_df_new['INT_ID'] = node_df_new['node_id'].str.split('-', expand = True)[0]\n\no_list_new = list(node_df_new[node_df_new['node_id'].isin(node_data['o_node'])]['index'])\nd_list_new = list(node_df_new[node_df_new['node_id'].isin(node_data['d_node'])]['index'])")


# In[ ]:


get_ipython().run_cell_magic('time', '', "\nout_all = G_copy.shortest_paths(o_list_new, d_list_new, weights = 'cost',  mode = 'out')\ntable = []\nfor i in range(len(o_list_new)):\n    temp_lst = out_all[i]\n    for j in range(len(d_list_new)):\n        table.append([o_list_new[i], d_list_new[j], temp_lst[j], iteration])\n\ntemp_df = pd.DataFrame.from_records(table, columns = ['index_o', 'index_d', 'travel_time', 'iteration'])\ntemp_df = temp_df.merge(node_df_new[['node_id', 'index', 'INT_ID']], left_on = ['index_o'], right_on = ['index'])\ntemp_df = temp_df.rename(columns = {'node_id':'o_node', 'INT_ID':'origin'})[['o_node', 'index_d', 'origin','travel_time', 'iteration']]\ntemp_df = temp_df.merge(node_df_new[['node_id', 'index','INT_ID']], left_on = ['index_d'], right_on = ['index'])\ntemp_df = temp_df.rename(columns = {'node_id':'d_node','INT_ID':'destination'})[['o_node', 'd_node', 'origin','destination','travel_time', 'iteration']]\ntemp_df = temp_df.merge(node_data[['o_node', 'd_node']])\ntemp_df['origin'] = temp_df['origin'].astype(int)\ntemp_df['destination'] = temp_df['destination'].astype(int)\ntemp_df = temp_df[temp_df['origin'] != temp_df['destination']]")


# In[ ]:


temp_df


# In[ ]:


temp_df = temp_df.merge(od_data)
temp_df['ge'] =  (1/temp_df['travel_time'])*(temp_df['total']/total_trips)
new_ge = temp_df['ge'].sum()
new_ge


# In[ ]:


new_ge/baseline_ge*100


# In[293]:


temp_df['status'] = True


# In[294]:


check_diff = importance_df.merge(temp_df[['o_node', 'd_node', 'status', 'travel_time']], left_on = ['o_node', 'd_node'],
                                 right_on = ['o_node', 'd_node'],how = 'left')
check_diff['delta'] = check_diff['travel_time_y'] - check_diff['travel_time_x']


# In[295]:


check_diff.sort_values(by = 'delta')


# In[300]:


check_diff[check_diff['travel_time_y'] !=np.inf].sort_values(by = 'travel_time_y').tail(5)


# In[60]:


G_copy = G.copy()
for i in G_copy.vs:
    node_key_table.append([i.index,  i['id']])
node_df_new = pd.DataFrame.from_records(node_key_table, columns = ['index', 'node_id'])
node_df_new['INT_ID'] = node_df_new['node_id'].str.split('-', expand = True)[0].astype(int)


# In[61]:


node_df_new[node_df_new['node_id']=='1624-0-7-59']


# In[66]:


G_copy = G.copy()

edge_pairs = bc_weighted.head(2000).merge(stop_times_od).merge(node_df_new[['node_id', 'index']], left_on = ['node_o'], right_on = 'node_id')

edge_pairs = edge_pairs.rename(columns = {'index': 'index_o'})
edge_pairs = edge_pairs.drop(columns = ['node_id'])
edge_pairs = edge_pairs.merge(node_df_new[['node_id', 'index']], left_on = ['node_d'], right_on = 'node_id')
edge_pairs = edge_pairs.rename(columns = {'index': 'index_d'})
edge_pairs = edge_pairs.drop(columns = ['node_id'])

del_edge = G.get_eids(edge_pairs[['index_o', 'index_d']].values.tolist(), directed = True)
G_copy.delete_edges(del_edge)
node_key_table = []
for i in G_copy.vs:
    node_key_table.append([i.index,  i['id']])
node_df1 = pd.DataFrame.from_records(node_key_table, columns = ['index', 'node_id'])
node_df1['INT_ID'] = node_df1['node_id'].str.split('-', expand = True)[0].astype(int)


# In[67]:


node_df1[node_df1['node_id']=='1624-0-7-59']


# In[261]:


node_df_new[node_df_new['node_id']=='1371-0-99-99']


# In[303]:


check_diff['travel_time_y'] = np.where(check_diff['travel_time_y'] == np.inf, 600, check_diff['travel_time_y'])


# In[304]:


check_diff['travel_time_y'].hist()


# In[ ]:




