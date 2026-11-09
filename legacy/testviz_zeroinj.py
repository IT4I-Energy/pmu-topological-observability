import Graph_zeroinjection, PMUconfiguration_zeroinj
import pickle as p


with open('Grids/branchcase57.pickle','rb') as f:
   branch=p.load(f)
with open('Grids/buscase57.pickle','rb') as f:
   bus=p.load(f)

with open('Grids/gencase57.pickle','rb') as f:
   gen=p.load(f)

N=57


G=Graph_zeroinjection.Graph_zeroinjection(N,branch,bus,gen)

pmuconfig=PMUconfiguration_zeroinj.PMUconfiguration_zeroinj(N)
pmuconfig.fromfile('pmuIEEE57_zeroinj.yml')
   
G.representation(pmuconfig)
