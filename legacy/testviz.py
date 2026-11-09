import Graph, PMUconfiguration
import pickle as p
import PMUconfiguration

with open('Grids/branchcase14.pickle','rb') as f:
   branch=p.load(f)


N=118



G=Graph.Graph(N,branch)

pmuconfig=PMUconfiguration.PMUconfiguration(N)
pmuconfig.fromfile('pmuIEEE118')
   
G.representation(pmuconfig)
