import Graph_constraint, PMUconfiguration_constr
import pickle as p


with open('Grids/branchcase118.pickle','rb') as f:
   branch=p.load(f)


N=118
nImes=4


G=Graph_constraint.Graph_constraint(N,branch)

pmuconfig=PMUconfiguration_constr.PMUconfiguration_constr(N,nImes)
pmuconfig.fromfile('pmuIEEE118_4.yml','ImesIEEE118_4.yml')

#Imes=pmuconfig.getImes()
#print(Imes)

G.representation(pmuconfig)
