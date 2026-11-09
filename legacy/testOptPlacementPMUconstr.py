import OptPlacementPMU_constr, pickle as p, random, numpy as np, Graph_constraint, ILS_constr,  PMUconfiguration_constr
from yaml import load, dump

with open('Grids/branchcase14.pickle','rb') as f:
   branch=p.load(f)




N=14
print('b=',branch)


G=Graph_constraint.Graph_constraint(N,branch)
   
OptPlacement=OptPlacementPMU_constr.OptPlacementPMU_constr(N,branch)
nImes=1

PMUconfig=OptPlacement.PPA(nImes)
PMUconfigmin=PMUconfiguration_constr.PMUconfiguration_constr(N,nImes)
PMUconfigmin.copyPMUconfig(PMUconfig)

I_measurements=PMUconfig.getImes()
print('I_measurements=',I_measurements)

n_pmu=PMUconfig.getnPMU()
print(n_pmu)
pmu=PMUconfig.getPMUnodes()
print('pmu=')
print(pmu)

Imes=PMUconfig.getImes()
print('Imes=',Imes)
ILS=ILS_constr.ILS_constr(30,30,N,nImes)
npmu=2
PMUconfigmin=ILS.IteratedLocalSearch(G,PMUconfig,npmu)

G.representation(PMUconfigmin)

pmumes=PMUconfigmin.getPMUmes()

with open('Results/pmuIEEE14_1.yml', 'w') as file:
    dump(pmumes,file)
"""
k=0
while (k<30):
   i=0
   
   while (i<20):
      PMUconfig=G.perturb(PMUconfig,nImes)
      PMUconfig=G.removeextra(PMUconfig)
      i=i+1
   PMUconfig=G.randomadditionPMUs(PMUconfig,nImes,2)
   k=k+1

pmu=PMUconfig.getnPMU()

print('npmu=',npmu) 
"""

o=0
"""
obs=0
i=0
while (obs==0)&(i<1000):
   PMUconfig2,j=PMUconfig.shuffle_constr(G,nImes)
   pmu=PMUconfig.getPMUnodes()
   npmu0=len(pmu)
   k=0
   while (o==0) and (k<100):
         p=random.choice(pmu)
         #print('p=',p)
         PMUconfig3,o=G.changebrmeasurement(PMUconfig2,p,nImes)
         k=k+1
         print('o=',o)

   obs=G.isobs_constr(PMUconfig3)
   if (obs==1):
      print('ok')
      PMUconfig=PMUconfig.copyPMUconfig(PMUconfig3)
   i=i+1
   
PMUconfig=G.removeextra(PMUconfig3)
"""

"""
for i in range(0,20):
   PMUconfig=G.perturb(PMUconfig,nImes)
   #PMUconfig=G.removeextra(PMUconfig)
   #npmu=PMUconfig.getnPMU()
   #print(npmu)
   o=G.isobs_constr(PMUconfig)
   print(o)



for k in range(0,1):
  #p=random.choice(pmu)
   for i in range(0,60):

      #PMUconfigPPA_constr,j=PMUconfigPPA_constr.shuffle_constr(G,nImes)
      PMUconfig,j=PMUconfig.shuffle_constr(G,nImes)
      pmu=PMUconfig.getPMUnodes()
      npmu0=len(pmu)
      
      o=0
      k=0
      while (o==0) and (k<100):
         p=random.choice(pmu)
         #print('p=',p)
         PMUconfig,o=G.changebrmeasurement(PMUconfig,p,nImes)
         k=k+1
         
      PMUconfig=G.removeextra(PMUconfig)
      v=PMUconfig.getPMUconfig()
      npmu=PMUconfig.getnPMU()
      Imes3=PMUconfig.getImes()
      if (npmu<npmu0):
         
         PMUconfigmin.setPMUconfigv(v)
         PMUconfigmin.setPMUconfigI(Imes3)
         


Imesmin=PMUconfigmin.getImes()
npmumin=PMUconfigmin.getnPMU()
pmu=PMUconfigmin.getPMUnodes()
print('npmu=',npmumin)
print('Imes=',Imesmin)
print('pmu=',pmu)
print('o=',o)   
#ILS1=ILS_constr.ILS_constr(20,30,N)
#PMUconfig=ILS1.locsearch2(G,PMUconfigPPA_constr,nImes)

#G.representation(PMUconfig,1)

PMUconfigmin=OptPlacement.ILS(nImes)
n_pmu=PMUconfigmin.getnPMU()
print(n_pmu)
pmu1=PMUconfigmin.getPMUnodes()
print(pmu1)



PMUconfigPPA=OptPlacement.PPA()
n_pmu=PMUconfigPPA.getnPMU()
print(n_pmu)
pmu1=PMUconfigPPA.getPMUnodes()
print(pmu1)

"""

