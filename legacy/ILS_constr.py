from ILS import ILS
import Graph_constraint, PMUconfiguration_constr, random

class ILS_constr(ILS):

    def __init__(self,T,M,N,nImes):
        super().__init__(T,M,N)
        self.nImes=nImes
        
    def locsearch(self,G,PMUconfig):
        """local search starting from given PMU configuration"""
        obs=0
        j=0        
        
        
        while (j<self.T):
               
                pmu=PMUconfig.getPMUnodes()
                n=PMUconfig.getnPMU()
                #print(n)
                
                PMUconfig,i=G.perturb(PMUconfig,self.nImes)
                if (i==1000): break
                PMUconfig=G.removeextra(PMUconfig)
               
                j=j+1
                
        return PMUconfig

    def locsearch2(self,G,PMUconfig,nImes):
        """local search starting from given PMU configuration"""
        obs=0
        j=0        
        
        
        while (j<self.T):
                
                pmu=PMUconfig.getPMUnodes()
                Imes=PMUconfig.getImes()
                n=PMUconfig.getnPMU()
                print(pmu)
                p=random.choice(pmu)
                PMUconfig, o=G.changebrmeasurement(PMUconfig,p,nImes)
                Imes=PMUconfig.getImes()
                print('Imes=',Imes)
                #if (l==20): break
                PMUconfig=G.removeextra(PMUconfig)
               
                j=j+1
                
        return PMUconfig

    def IteratedLocalSearch(self,G,PMUconfig,npmu):
        obs=0
        npmu=2
        nImes=PMUconfig.getnImes()
 
        PMUconfigmin=PMUconfiguration_constr.PMUconfiguration_constr(self.N,nImes)
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
                o=G.isobs_constr(PMUconfig)    
                print('i=',i,'n=',n,'nmin=',nmin,'obs=',o)
                PMUconfig=G.randomadditionPMUs(PMUconfig,nImes,npmu)

        return PMUconfigmin
