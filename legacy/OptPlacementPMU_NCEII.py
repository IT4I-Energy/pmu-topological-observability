import Graph_NCEII, PMUconfiguration_NCEII, pickle as p, ILS_NCEII


class OptPlacementPMU_NCEII:
    def __init__(self,N,branch):
         self.g=Graph_NCEII.Graph_NCEII(N,branch)
         
         
    def getinfo(self):
         n=self.g.getN()
         A=self.g.getA()
    
         ed=self.g.endnodes()
         return n,A,ed

    def PPA(self,en):
         
         n,A,ed=self.getinfo()
         """PageRAnk"""

         PMUconfig=PMUconfiguration_NCEII.PMUconfiguration_NCEII(n)

         """Implementing PageRank Placement Algorithm for PMU placement"""
         PMUconfig.PPA1()
         pmu=PMUconfig.getPMUnodes()
         print('PPA-1st ')
         print(pmu)
         pr=self.g.pageRank()
         PMUconfig.PPA2(self.g,pr)
         

         return PMUconfig

    def ILS(self):
         """Iterated Local search starting from PMU configuration obtained by PPA"""

         n,A,en=self.getinfo()
         
         PMUconfig=self.PPA(en)
         pmuppa=PMUconfig.getPMUnodes()
         nppa=len(pmuppa)
         print('nppa=',nppa)
         #ILS1=ILS.ILS(10,10,n)
         #ILS1=ILS.ILS(10,30,n)
         ILS1=ILS_NCEII.ILS_NCEII(20,50,n)
         PMUconfig=ILS1.locsearch(self.g,PMUconfig)
         PMUconfigmin=ILS1.IteratedLocalSearch(self.g,PMUconfig,2)
         n_min=PMUconfigmin.getnPMU()
         print(n_min)
         return PMUconfigmin
     
    
