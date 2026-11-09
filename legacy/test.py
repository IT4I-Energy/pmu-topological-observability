import OptPlacementPMU, pickle as p, random, numpy as np, Graph




with open('case118.pickle','rb') as f:
   branch=p.load(f)
N=118
print('b=',branch)


G=Graph.Graph(N,branch)
   
OptPlacement=OptPlacementPMU.OptPlacementPMU(N,branch)

"""
PMUconfigPPA_constr,I_measurements=OptPlacement.PPA_constr(1)
n_pmu=PMUconfigPPA_constr.getnPMU()
print(n_pmu)
pmu1=PMUconfigPPA_constr.getPMUnodes()
print(pmu1)

G. representation_constr('IEEE14_1',PMUconfigPPA_constr,1,I_measurements)
"""

PMUconfigPPA=OptPlacement.PPA()
n_pmu=PMUconfigPPA.getnPMU()
print(n_pmu)
pmu1=PMUconfigPPA.getPMUnodes()
print(pmu1)

PMUconfigmin=OptPlacement.ILS()
n_pmu=PMUconfigmin.getnPMU()
print(n_pmu)
pmu1=PMUconfigmin.getPMUnodes()
print(pmu1)

