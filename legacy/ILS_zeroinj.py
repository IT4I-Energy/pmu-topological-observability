from ILS import ILS
import Graph_zeroinjection, PMUconfiguration_zeroinj

class ILS_zeroinj(ILS):
    def locsearch(self,G,PMUconfig):
        """local search starting from given PMU configuration"""
        obs=0
        j=0        
        
        
        while (j<self.T):
               
                pmu=PMUconfig.getPMUnodes()
                n=PMUconfig.getnPMU()
                #print(n)
                
                PMUconfig,i=G.perturb(PMUconfig)
                if (i==1000): break
                PMUconfig=G.removeextra(PMUconfig)
               
                j=j+1
                
        return PMUconfig
