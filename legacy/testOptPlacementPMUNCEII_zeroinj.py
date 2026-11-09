import PMUconfiguration_zeroinj_NCEII, OptPlacementPMU_zeroinjNCEII, pickle as p, random, numpy as np, Graph_zeroinjectionNCEII, getinfoNCEII as gi
import yaml
from yaml import load, dump





with open('Results/pmuIEEE233.yaml','r') as f:
   pmu=yaml.safe_load(f)

N=233
branch, zero_injections=gi.getinfoNCEII()



G=Graph_zeroinjectionNCEII.Graph_zeroinjectionNCEII(N,branch,zero_injections)
   
OptPlacement_zeroinj=OptPlacementPMU_zeroinjNCEII.OptPlacementPMU_zeroinjNCEII(N,branch,zero_injections)


PMUconfig0=PMUconfiguration_zeroinj_NCEII.PMUconfiguration_zeroinj_NCEII(N)
#PMUconfig0=PMUconfiguration.PMUconfiguration(N)

PMUconfig0.setPMUvec(pmu)
print(pmu)
print(PMUconfig0.getPMUnodes())

#vec2=PMUconfig0.shuffle()
PMUconfigmin=OptPlacement_zeroinj.ILS(PMUconfig0)
n_pmu=PMUconfigmin.getnPMU()
print(n_pmu)
pmu1=PMUconfigmin.getPMUnodes()
print(pmu1)

#PMUconfigmin.export()

G.representation(PMUconfigmin)

with open('Results/pmuIEEE233_zeroinj.yaml', 'w') as file:
    dump(pmu1,file)



"""
vec=np.zeros((N))
pmu=[1,8,10,12]

for n in pmu:
   vec[n]=1

PMUconfig=PMUconfiguration.PMUconfiguration(N)
PMUconfig.setPMUconfig(vec)
print('pmu=',pmu)
obsvec=G.observability(PMUconfig)
print(obsvec)

ILS1=ILS.ILS(10,60,n)
PMUconfig=ILS1.locsearch(G,PMUconfig)
pmus=PMUconfig.getPMUnodes()
print(pmus)


PMUconfigPPA=OptPlacement_zeroinj.PPA()
n_pmu=PMUconfigPPA.getnPMU()
print(n_pmu)
pmu1=PMUconfigPPA.getPMUnodes()
print(pmu1)
"""
