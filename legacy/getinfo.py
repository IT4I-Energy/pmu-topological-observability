from LoadFlow.rtsout14 import rtsout14
from LoadFlow.rtsout57 import rtsout57
from LoadFlow.rtsout118 import rtsout118

import numpy as np
import pickle as p


branch=rtsout14()['branch']
bus=rtsout14()['bus']
gen=rtsout14()['gen']

m=len(branch)

branchinfo14=np.zeros((m,2))

for i in range(0,m):
    branchinfo14[i][0]=branch[i][0]-1
    branchinfo14[i][1]=branch[i][1]-1

with open('Grids/branchcase14.pickle','wb') as f:
    p.dump(branchinfo14,f)

with open('Grids/buscase14.pickle','wb') as f:
    p.dump(bus,f)

with open('Grids/gencase14.pickle','wb') as f:
    p.dump(gen,f)

    
branch=rtsout57()['branch']
bus=rtsout57()['bus']
gen=rtsout57()['gen']

m=len(branch)
branchinfo57=np.zeros((m,2))

for i in range(0,m):
    branchinfo57[i][0]=branch[i][0]-1
    branchinfo57[i][1]=branch[i][1]-1


with open('Grids/branchcase57.pickle','wb') as f:
    p.dump(branchinfo57,f)

with open('Grids/buscase57.pickle','wb') as f:
    p.dump(bus,f)

with open('Grids/gencase57.pickle','wb') as f:
    p.dump(gen,f)

    
branch=rtsout118()['branch']
bus=rtsout118()['bus']
gen=rtsout118()['gen']


m=len(branch)

branchinfo118=np.zeros((m,2))

for i in range(0,m):
    branchinfo118[i][0]=branch[i][0]-1
    branchinfo118[i][1]=branch[i][1]-1


with open('Grids/branchcase118.pickle','wb') as f:
    p.dump(branchinfo118,f)

with open('Grids/buscase118.pickle','wb') as f:
    p.dump(bus,f)

with open('Grids/gencase118.pickle','wb') as f:
    p.dump(gen,f)
    
    


