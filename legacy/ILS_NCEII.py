from ILS import ILS
import PMUconfiguration_NCEII, Graph_NCEII

class ILS_NCEII(ILS):

 
       def IteratedLocalSearch(self,G,PMUconfig,npmu):
              obs=0
              npmu=2

 
              PMUconfigmin=PMUconfiguration_NCEII.PMUconfiguration_NCEII(self.N)
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
