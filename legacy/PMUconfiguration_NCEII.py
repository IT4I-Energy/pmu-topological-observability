from PMUconfiguration import PMUconfiguration
import numpy as np
import random

class PMUconfiguration_NCEII(PMUconfiguration):


   def getlistDTS(self):
      DTS=list()
      for i in range(0,60):
         DTS.append(i)
      return DTS
         
   def __init__(self,N):
        self.PMUvec=np.zeros(N)
        self.DTSnod=self.getlistDTS()

   def getDTS(self):
      return self.DTSnod

   def getnPMU(self):
        """return number of PMUs in configuration"""
        s=int(sum(self.PMUvec))
        return s

   
   def PPA1(self):
        """first part of PageRank Placement Algorithm:"""
        """placement of a PMU at buses with DTS"""
        n=len(self.DTSnod)
        
        for i in range(0,n):
            p=self.DTSnod[i]
            self.addPMU(p)
       

   def getobjectivefunction(self):
              #returns objective function depending on number of PMUs outside set of DTS buses
              f=0
              pmu=self.getPMUnodes()
              dts=self.getDTS()
              
              for p in pmu:
                     if p in dts:
                            f=f+1
                     else:
                            f=f+10
              return f

        
