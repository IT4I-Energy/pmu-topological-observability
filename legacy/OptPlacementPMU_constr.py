import Graph_constraint, PMUconfiguration_constr, pickle as p, ILS_constr


class OptPlacementPMU_constr:
    def __init__(self,N,branch):
         self.g=Graph_constraint.Graph_constraint(N,branch)

    def getinfo(self):
         n=self.g.getN()
         A=self.g.getA()
    
         ed=self.g.endnodes()
         return n,A,ed
    
    def PPA(self, nImeas):
         """PMU placement using PPA algorithm. Current measurements are chosen depending on the importance of the adjacent node"""
         """Priority is given to non-observed nodes"""
         
         n,A,ed=self.getinfo()
         """PageRAnk"""

         PMUconfig=PMUconfiguration_constr.PMUconfiguration_constr(n,nImeas)

         """Implementing PageRank Placement Algorithm for PMU placement"""
         obsvec=PMUconfig.PPA1(self.g,nImeas)
         I_measurements=PMUconfig.getImes()
         print(I_measurements)
         print(obsvec)
         
         PMUconfig.PPA2(self.g,nImeas,obsvec)

         #print(PMUconfigfin.getImes())
         
         n=PMUconfig.getnPMU()
         print(n)
         pmu1=PMUconfig.getPMUnodes()
         print(pmu1)
         
         return PMUconfig


    def ILS(self,nImes):
         """Iterated Local search starting from PMU configuration obtained by PPA"""

         n,A,ed=self.getinfo()
         
         PMUconfig=self.PPA(1)

         #ILS1=ILS.ILS(10,10,n)
         #ILS1=ILS.ILS(10,30,n)
         ILS1=ILS_constr.ILS_constr(20,30,n)
         PMUconfig=ILS1.locsearch(self.g,PMUconfig,nImes)
         PMUconfigmin=ILS1.IteratedLocalSearch(self.g,PMUconfig,2)
         n_min=PMUconfigmin.getnPMU()
         print(n_min)
         return PMUconfigmin
