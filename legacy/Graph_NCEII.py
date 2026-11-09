from Graph import Graph
import numpy as np
import graphviz, random
import PMUconfiguration_NCEII

class Graph_NCEII(Graph):
     """overloading of methods for Graph of NCIEE"""

     def perturb(self,PMUconfig):
                """get different observable PMU configuration """
                """variables obs (observability) i (iteration)"""
                obs=0
                i=0
                """PMUconfig0: initial PMU configuration"""
                v0=PMUconfig.getPMUconfig()
                n=len(v0)
                PMUconfig0=PMUconfiguration_NCEII.PMUconfiguration_NCEII(n)
                PMUconfig0.setPMUconfig(v0)
                
                """info PMUconfig and graph"""
                A=self.getA()
                endnodes=self.endnodes()
                pmu=PMUconfig.getPMUnodes()

                PMUconfig2=PMUconfiguration_NCEII.PMUconfiguration_NCEII(n)
                

                while (obs==0)&(i<1000):
                                                
                        v=PMUconfig.shuffle(endnodes,A)
                        PMUconfig2.setPMUconfig(v[0])

                                                
                        obs=self.isobs(PMUconfig2)
                        if (obs==1) :
                                PMUconfig=PMUconfig.copyPMUconfig(PMUconfig2)
                                
                                return PMUconfig, i
                        
                        i=i+1

                return PMUconfig0, i

     
     def representation(self,PMUconfig):#,Obsvec):
                """representation of power system with colored nodes if pmu is present"""
                g = graphviz.Graph()
                n=self.N
                #zeroinj=self.get_zeroinj()
                vecPMU=PMUconfig.getPMUconfig()
                
                for i in range(0,n):
                        #j=i-1
                        u=vecPMU[i]
                        if (u==1):
                                g.node(str(i),style='filled',fillcolor='green')
                 #       elif (i+1 in zeroinj):
                  #              g.node(str(i),style='filled',fillcolor='cyan')
                              
                        else:
                                g.node(str(i))
                                
                for el in self.branch:
                        i=int(el[0])
                        j=int(el[1])
                        g.edge(str(i),str(j))
                filename='IEEE'+str(self.N)+'_NCEII_new'
                g.render(filename)


     def randomadditionPMUs(self,PMUconfig,npmus):
                A=self.getA()
                endnodes=self.endnodes()
                nodes=PMUconfig.getcandidates(endnodes)

                for i in range(0,npmus):
                        p=random.choice(nodes)
                        PMUconfig.addPMU(p)

                        nodes.remove(p)

                return PMUconfig
                        
                
