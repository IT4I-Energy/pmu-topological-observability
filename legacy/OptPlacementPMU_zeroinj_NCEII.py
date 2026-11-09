from OptPlacementPMU_NCEII import OptPlacementPMU_NCEII
import Graph_zeroinjection, PMUconfiguration_zeroinj, ILS_zeroinj


class OptPlacementPMU_zeroinj(OptPlacementPMU_NCEII):
    def __init__(self,N,branch,bus,gen):
         self.g=Graph_zeroinjection.Graph_zeroinjection(N,branch,bus,gen)

       
    def ILS(self,PMUconfig):
         """Iterated Local search starting from PMU configuration obtained by PPA"""

         n,A,ed=self.getinfo()
         
        
         #ILS1=ILS.ILS(10,10,n)
         ILS1=ILS_zeroinj.ILS_zeroinj(20,20,n)
         #ILS1=ILS_zeroinj.ILS_zeroinj(1,1,n)
         PMUconfig=ILS1.locsearch(self.g,PMUconfig)
         PMUconfigmin=ILS1.IteratedLocalSearch(self.g,PMUconfig,2)
         n_min=PMUconfigmin.getnPMU()
         print(n_min)
         return PMUconfigmin
