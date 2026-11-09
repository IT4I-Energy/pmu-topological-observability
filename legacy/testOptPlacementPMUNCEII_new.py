import OptPlacementPMU_NCEII, pickle as p, random, numpy as np, Graph_NCEII, PMUconfiguration_NCEII
from yaml import load, dump
import getinfoNCEII as gi


branch,bus=gi.getinfoNCEII()

N=233
#print('b=',branch)


G=Graph_NCEII.Graph_NCEII(N,branch)

OptPlacement=OptPlacementPMU_NCEII.OptPlacementPMU_NCEII(N,branch)
n,A,ed=OptPlacement.getinfo()
print('N=',n)


PMUconfigPPA=OptPlacement.PPA()
n_pmuppa=PMUconfigPPA.getnPMU()
print('n_pmuppa=',n_pmuppa)
pmuvec=PMUconfigPPA.getPMUconfig()
print(len(pmuvec))

v=PMUconfigPPA.getPMUconfig()
print(v[1])
#print(pmuvec)
PMUconfig1=PMUconfiguration_NCEII.PMUconfiguration(N)
PMUconfig1.setPMUconfig(v)

pmu1=PMUconfigPPA.getPMUnodes()
print(pmu1)
PMUconfigmin=OptPlacement.ILS()

#n_pmu=PMUconfigmin.getnPMU()
#print(n_pmu)
#pmu1=PMUconfigmin.getPMUnodes()
#print(pmu1)

#PMUconfigmin.export()

#G.representation(PMUconfigmin)

