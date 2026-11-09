from Graph import Graph
import graphviz
import random, numpy as np
import PMUconfiguration_constr, time

class Graph_constraint(Graph):
    """overloading of methods for Graphs with constraints on PMUs"""
    def test_branch_mes(self,PMUconfig,i,j):
                """test if measurement is made on branch"""
                Imeas=PMUconfig.getImes()
                for e in Imeas:
                     u=int(e[0])
                     v=int(e[1])

                     if ((u==i) and (v==j)) or ((u==j) and (v==i)):
                         
                         return 1
                return 0
        
    
    def representation(self,PMUconfig):#,Obsvec):
                """representation of power system with colored nodes if pmu is present; thick branches if measurements made on branch"""
                g = graphviz.Graph(engine='fdp')
                n=self.N
                nImes=PMUconfig.getnImes()
                vecPMU=PMUconfig.getPMUconfig()
                
                for i in range(0,n):
                        u=vecPMU[i]
                        if (u==1):
                                g.node(str(i),style='filled',fillcolor='green')
                        else:
                                g.node(str(i))
                for el in self.branch:
                        i=int(el[0])
                        j=int(el[1])
                        b=self.test_branch_mes(PMUconfig,i,j)
                        
                        if (b==1):
                              g.edge(str(i),str(j),style='bold')
                        else:
                              g.edge(str(i),str(j))

                filename='Figure/IEEE'+str(self.N)+'_'+str(nImes)
                g.render(filename)
        

    def observability(self,PMUconfig):
        #pmu,Imeas):
        pmu=PMUconfig.getPMUnodes()

        Imeas=PMUconfig.getImes()
        obsvec=np.zeros(self.N)
        for j in pmu:
            obsvec[j]=1
        for el in Imeas:
           adjn=el[1]           
           obsvec[adjn]=1
        
        
        return obsvec
        

        
    def isobs_constr(self,PMUconfig):
        
        obsvec=self.observability(PMUconfig)
        l=len(obsvec)
        for i in range(0,l):
            if obsvec[i]==0:
                return 0
        return 1

    def selbranches(self,PMUconfig,p):
        """get branches from node p"""
        Imeas2=list()
        Imeas=PMUconfig.getImes()
        lg=len(Imeas)
        for j in range(0,lg):
                                u=Imeas[j][0]
                                v=Imeas[j][1]
                                if (u!=p):
                                    s=[u, v]
                                    Imeas2.append(s)

        return Imeas2
        
    def changebrmeasurement(self,PMUconfig,p,nImes):
        """change Imeasurement on branch from p to adjacent node"""
        Imeas=PMUconfig.getImes()
        v=PMUconfig.getPMUconfig()
        adjnodes=self.get_adjacentnodes(p)
        #print('adjnodes=',adjnodes)
        niter=2*len(adjnodes)
        
        for i in range(0,niter):

             nadj=len(adjnodes)
            
             if (nImes<=nadj):
                nodesImes=random.sample(adjnodes,nImes)
             elif (nImes>nadj):
                nodesImes=random.sample(adjnodes,nadj)
            
             
             #return branches other than those starting at p
             nbImeas=len(Imeas)

             #get branches except branches from node p
             Imes2=self.selbranches(PMUconfig,p)
        
                            
             #append branches from p to selected nodes (nodesImes)
             nselmes=len(nodesImes)
             for k in range(0,nselmes):
                     s=[p,nodesImes[k]]
                     Imes2.append(s)

             #print('I=',Imes2)
             
             N=self.getN()
             PMUconfig2=PMUconfiguration_constr.PMUconfiguration_constr(N,nImes)
             PMUconfig2.setPMUconfigv(v)
             PMUconfig2.setPMUconfigI(Imes2)
             o=self.isobs_constr(PMUconfig2)
             
             #print('o=',o)

             if (o==1):
                 return PMUconfig2, o
        
        return PMUconfig, o

    def perturbbranch(self,PMUconfig,nImes):
        o=0
        k=0
        pmu=PMUconfig.getPMUnodes()
        
        while (o==0) and (k<100):
            p=random.choice(pmu)
            
            PMUconfig2,o=self.changebrmeasurement(PMUconfig,p,nImes)
            k=k+1
            
        return PMUconfig2,o

    def perturb(self,PMUconfig,nImes):
                """get observable pmu configuration"""
                obs=0
                i=0

                while (obs==0)&(i<1000):
                         PMUconfig2,j=PMUconfig.shuffle_constr(self,nImes)
                        
                         
                         PMUconfig3,o=self.perturbbranch(PMUconfig2,nImes)
                         
                         
                        #time.sleep(5.0)
                        
                         obs=self.isobs_constr(PMUconfig3)
                        
                         if (obs==1) :
                                PMUconfig=PMUconfig.copyPMUconfig(PMUconfig3)
                                

                                return PMUconfig, i
                        

                            
                        
                         i=i+1

                return PMUconfig,i

    def removeextra(self,PMUconfig):
                """test if a pmu can be removed while keeping observability."""
                vecPMU=PMUconfig.getPMUconfig()
                Imeas0=PMUconfig.getImes()
                nImes=PMUconfig.getnImes()
                N=len(vecPMU)
                PMUconfig2=PMUconfiguration_constr.PMUconfiguration_constr(N,nImes)
                for i in range(1,N):
                        if (vecPMU[i]==1):
                                vecPMU[i]=0
                                PMUconfig2.setPMUconfigv(vecPMU)
                                """branches other than those starting at i"""
                                Imeas2=self.selbranches(PMUconfig,i)
                                PMUconfig2.setPMUconfigI(Imeas2)
                                
                                obs=self.isobs(PMUconfig2)
                                if (obs==1):
                                        return PMUconfig2
                                else:
                                        vecPMU[i]=1
                                        PMUconfig2.setPMUconfigv(vecPMU)
                                        #PMUconfig2.setPMUconfigI(Imeas0)
                return PMUconfig

    def randomadditionPMUs(self,PMUconfig,nImes,npmus):
                A=self.getA()
                endnodes=self.endnodes()
                nodes=PMUconfig.getcandidates(endnodes)

                for i in range(0,npmus):
                        p=random.choice(nodes)
                        PMUconfig.addPMU2(p,nImes,self)
                        
                        nodes.remove(p)

                return PMUconfig
                        
                


