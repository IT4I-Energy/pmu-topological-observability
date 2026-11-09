import OptPlacementPMU_NCEII, pickle as p, random, numpy as np, Graph_NCEII
from yaml import load, dump



with open('Grids/branchcase118.pickle','rb') as f:
   branch=p.load(f)


N=118



G=Graph_NCEII.Graph_NCEII(N,branch)
   
OptPlacement=OptPlacementPMU_NCEII.OptPlacementPMU_NCEII(N,branch)

en=G.endnodes()
print('en=',en)

PMUconfigPPA=OptPlacement.PPA(en)
pmu=PMUconfigPPA.getPMUnodes()
print(pmu)

n_pmu=PMUconfigPPA.getnPMU()
print(n_pmu)
pmu1=PMUconfigPPA.getPMUnodes()
print('pmu1=')
print(pmu1)

PMUconfigmin=OptPlacement.ILS()
n_pmu=PMUconfigmin.getnPMU()
print(n_pmu)
pmu1=PMUconfigmin.getPMUnodes()
print(pmu1)

PMUconfigmin.export()

G.representation(PMUconfigmin)
