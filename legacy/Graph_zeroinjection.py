from Graph import Graph
import numpy as np
import graphviz
import PMUconfiguration_zeroinj

class Graph_zeroinjection(Graph):
     """overloading of methods for Graphs with zero injections"""

     def __init__(self,N,branch,bus,gen):
         self.N=N
         self.branch=branch
         self.bus=bus
         self.gen=gen
                
     def get_zeroinj(self):
         """get zero injections """
         b=len(self.bus)

         g=len(self.gen)

         gbus=list()
         for i in range(0,g):
             gbus.append(int(self.gen[i][0]))


         zero_injections=list()
         for i in range(0,b):
             v=int(self.bus[i][0])
             type=self.bus[i][1]
             Pd=self.bus[i][2]
             Qd=self.bus[i][3]

             if (Pd==0) and (Qd==0):
                 if v not in gbus:
                     zero_injections.append(v)
                     
         return zero_injections

     

     def obsadjnodes(self,adjnodes,obsvec):
          for i in adjnodes:
              if (obsvec[i-1]==0):
                   return 0
          return 1
          
     def getnobservedadjnodes(self,i,adjnodes,obsvec):
          n_obs=0
          nadjnodes=len(adjnodes)
          
          for i in adjnodes:
              if (obsvec[i-1]==1):
                   n_obs=n_obs+1
          #print('n_obs=',n_obs)
          #print('nadjnodes=',nadjnodes)
          if (n_obs>=nadjnodes-1):
               return 1
          else:
               return 0

          
     def constraints_zeroinjections(self, obsvec, zero_injections):
         """implementation of additional tests for observability for zero
injection buses: """
         """
              if all nodes adjacent to a zero injection node are ob-
served, then it is also observed."""
         for i in zero_injections:
               adjnodes=self.get_adjacentnodes(i-1)
               b=self.obsadjnodes(adjnodes,obsvec)
               if (b==1):
                    obsvec[i-1]=1
         """
              if all the adjacent nodes except one are observed, and the 
zero injection node is also observed, then the remaining adjacent node is also observed."""
         for i in zero_injections:
               if (obsvec[i-1]==1):
                    adjnodes=self.get_adjacentnodes(i-1)
                    #print('adjnodes=',adjnodes)
                    n_adjnodes=len(adjnodes)
                    b=self.getnobservedadjnodes(i,adjnodes,obsvec)
                   
                    if (b==1):
                         for i in adjnodes:
                              obsvec[i]=1
         return obsvec
                         
                 
     def observability(self,PMUconfig):
                """determines if PMU configuration makes system observable"""
                """returns binary vector (1 if node is observable, 0 otherwise)"""
                A=self.getA()
                
                """obsvec:observability vector"""
                obsvec=np.zeros(self.N)
                PMUvec=PMUconfig.getPMUconfig()
                lg=len(PMUvec)
                for i in range(0,lg):
                       b_pmu=PMUvec[i]
                       if (b_pmu==1):
                               obsvec[i]=1
                               for j in range (0,lg):
                                       if (A[i][j]==1):
                                               obsvec[j]=1

                zero_injections=self.get_zeroinj()
                #print('before constraint obsvec node 2:',obsvec[2])
                obsvec=self.constraints_zeroinjections(obsvec, zero_injections)
                #print('after constraint obsvec node 2:', obsvec[2])
                return obsvec    

     def isobs(self,PMUconfig):
        """checks if all nodes are observable"""
        obsvec=self.observability(PMUconfig)
        l=len(obsvec)

        for i in range(0,l):
            if obsvec[i]==0:
                return 0
        return 1

     def perturb(self,PMUconfig):
                """get different observable PMU configuration """
                """variables obs (observability) i (iteration)"""
                obs=0
                i=0
                """PMUconfig0: initial PMU configuration"""
                v0=PMUconfig.getPMUconfig()
                n=len(v0)
                PMUconfig0=PMUconfiguration_zeroinj.PMUconfiguration(n)
                PMUconfig0.setPMUconfig(v0)
                
                """info PMUconfig and graph"""
                A=self.getA()
                endnodes=self.endnodes()
                pmu=PMUconfig.getPMUnodes()

                PMUconfig2=PMUconfiguration_zeroinj.PMUconfiguration(n)
                

                while (obs==0)&(i<1000):
                                                
                        v=PMUconfig.shuffle_zeroinj(endnodes,A)
                        PMUconfig2.setPMUconfig(v)

                                                
                        obs=self.isobs(PMUconfig2)
                        if (obs==1) :
                                PMUconfig=PMUconfig.copyPMUconfig(PMUconfig2)
                                
                                return PMUconfig, i
                        
                        i=i+1

                return PMUconfig0, i


    
     def representation(self,PMUconfig):#,Obsvec):
                """representation of power system with green nodes if pmu is present, cyan nodes if node is a zero-injection node, yellow if it is observed by a pmu"""
                g = graphviz.Graph(engine='fdp')
                n=self.N
                zeroinj=self.get_zeroinj()
                vecPMU=PMUconfig.getPMUconfig()
                
                for i in range(0,n):
                        
                        u=vecPMU[i]
                        
                        if (u==1):
                                #set green color for nodes with pmu
                                g.node(str(i),style='filled',fillcolor='green')
                                #get adjacent nodes to pmu#
                                adjPMU=self. get_adjacentnodes(i)
                                #set yellow for nodes adjacent to pmu
                                for k in adjPMU:
                                      if (k+1 not in zeroinj):
                                           g.node(str(k),style='filled',fillcolor='yellow')
                                
                        elif (i+1 in zeroinj):
                                g.node(str(i),style='filled',fillcolor='cyan')
                              
                        else:
                                g.node(str(i))
                                
                for el in self.branch:
                        i=int(el[0])
                        j=int(el[1])
                        g.edge(str(i),str(j))
                filename='Figure/IEEE'+str(self.N)+'_zeroinj'
                g.render(filename)

     
