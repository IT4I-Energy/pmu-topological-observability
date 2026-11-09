import Graph, PMUconfiguration
import pickle as p

with open('Grids/branchcase14.pickle','rb') as f:
   branch=p.load(f)


N=14

ex=Graph.Graph(N,branch)
pc=PMUconfiguration.PMUconfiguration(N)
pc.addPMU(1)

obsvec=ex.observability(pc)
ex.representationtest(pc)


