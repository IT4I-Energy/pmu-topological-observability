import OptPlacementPMU, pickle as p, random, numpy as np, Graph,
PMUconfiguration_NCEII

from yaml import load, dump
import getinfoNCEII as gi


branch=gi.getinfoNCEII()

N=233
#print('b=',branch)


G=Graph.Graph(N,branch)
pmu_ip=G.getPDS()
n_pmu=sum(pmu_ip)
print('n_pmu=',n_pmu)
#print(pmu_ip)
#PMUconfigmin=PMUconfiguration.PMUconfiguration(N)
#PMUconfigmin.setPMUconfig(pmu_ip)

OptPlacement=OptPlacementPMU.OptPlacementPMU(N,branch)
n,A,ed=OptPlacement.getinfo()
print('N=',n)

PMUconfig=PMUconfiguration_NCIEE.PMUconfiguration_NCIEE()
print(PMUconfig.getDTS())

PMUconfigPPA=OptPlacement.PPA()
n_pmuppa=PMUconfigPPA.getnPMU()
print('n_pmuppa=',n_pmuppa)
pmuvec=PMUconfigPPA.getPMUconfig()
print(len(pmuvec))


pmu1=PMUconfigPPA.getPMUnodes()
#print(pmu1)
PMUconfigmin=OptPlacement.ILS()

n_pmu=PMUconfigmin.getnPMU()
print(n_pmu)
pmu1=PMUconfigmin.getPMUnodes()
print(pmu1)

PMUconfigmin.export()

G.representation(PMUconfigmin)

