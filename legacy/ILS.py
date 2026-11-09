
import PMUconfiguration, Graph, Graph_zeroinjection

class ILS():
    def __init__(self,T,M,N):
        self.T=T
        self.M=M
        self.N=N

    def locsearch(self,G,PMUconfig):
        """local search starting from given PMU configuration"""
        obs=0
        j=0        
        
        
        while (j<self.T):
                
                pmu=PMUconfig.getPMUnodes()
                
                PMUconfig,i=G.perturb(PMUconfig)
                if (i==1000): break
                PMUconfig=G.removeextra(PMUconfig)
               
                j=j+1
        return PMUconfig

    
    def IteratedLocalSearch(self,G,PMUconfig,npmu):
        obs=0
        npmu=2

 
        PMUconfigmin=PMUconfiguration.PMUconfiguration(self.N)
        PMUconfigmin=PMUconfigmin.copyPMUconfig(PMUconfig)
        nmin=PMUconfig.getnPMU()
        
        for i in range(0,self.M):
            #while (obs==0):
                
                PMUconfig=self.locsearch(G,PMUconfig)
                
                n=PMUconfig.getnPMU()
                
                if (n<nmin):
                    PMUconfigmin=PMUconfigmin.copyPMUconfig(PMUconfig)
                    nmin=PMUconfigmin.getnPMU()
                    print('nmin=',nmin)
                o=G.isobs(PMUconfig)    
                print('i=',i,'n=',n,'nmin=',nmin,'obs=',o)
                PMUconfig=G.randomadditionPMUs(PMUconfig,npmu)

        return PMUconfigmin
