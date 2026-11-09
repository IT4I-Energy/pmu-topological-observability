import OptPlacementPMU, pickle as p, random, numpy as np, Graph
from yaml import load, dump



with open('Grids/branchcase118.pickle','rb') as f:
   branch=p.load(f)


N=118



G=Graph.Graph(N,branch)
   
OptPlacement=OptPlacementPMU.OptPlacementPMU(N,branch)



PMUconfigPPA=OptPlacement.PPA()
n_pmu=PMUconfigPPA.getnPMU()
print(n_pmu)
pmu1=PMUconfigPPA.getPMUnodes()
#print(pmu1)

PMUconfigmin=OptPlacement.ILS()
n_pmu=PMUconfigmin.getnPMU()
print(n_pmu)
pmu1=PMUconfigmin.getPMUnodes()
print(pmu1)

PMUconfigmin.export()

G.representation(PMUconfigmin)
