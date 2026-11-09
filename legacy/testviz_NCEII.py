import Graph, PMUconfiguration
import pickle as p
import PMUconfiguration_NCEII
import getinfoNCEII as gi


branch=gi.getinfoNCEII()


N=233



G=Graph.Graph(N,branch)

pmuconfig=PMUconfiguration.PMUconfiguration(N)
pmuconfig.fromfile('pmuIEEE233.yaml')
   
G.representation(pmuconfig)
