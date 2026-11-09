import numpy as np, random
from scipy.optimize import LinearConstraint, milp
import PMUconfiguration, PMUconfiguration_zeroinj
import graphviz, pageRank


class Graph:

        def __init__(self,N,branch):
                self.N=N
                self.branch=branch

                
        def representation(self,PMUconfig):#,Obsvec):
                """representation of power system with colored nodes if pmu is present"""
                g = graphviz.Graph(engine='fdp')
                n=self.N

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
                        g.edge(str(i),str(j))
                filename='Figure/IEEE'+str(self.N)
                g.render(filename)

        def representationtest(self,PMUconfig):#,Obsvec):
                """representation of power system with green nodes if pmu is present, cyan nodes if node is a zero-injection node, yellow if it is observed by a pmu"""
                g = graphviz.Graph()
                n=self.N
               
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
                                           g.node(str(k),style='filled',fillcolor='yellow')
                                
                        
                              
                        else:
                                g.node(str(i))
                                
                for el in self.branch:
                        i=int(el[0])
                        j=int(el[1])
                        g.edge(str(i),str(j))
                filename='Figure/IEEEtest'+str(self.N)
                g.render(filename)

     
        
        
        def getN(self):
                return self.N
        
        def getA(self):
                """get adjacency matrix"""
                m=len(self.branch)
                
                n=self.N

                A=np.zeros((n,n))
                
                for el in self.branch:
                        
                        i=int(el[0])
                        j=int(el[1])
                       
                        A[i][j]=1
                        A[j][i]=1

                return A

        def get_adjacentnodes(self,i):
                """get adjacent nodes to node i"""
                adjnodes=list()
                A=self.getA()
                n=len(A)
         
                for j in range(0,n):
                        if (A[i][j]==1):
                                adjnodes.append(j)
                     
                return adjnodes
        
        def getAdj(self,A):
             n=self.N
             print(n)
             Adj=np.zeros((n,n))
             
             
             for k in range(0,n):
                c=0
                for j in range(0,n):
                        if (A[k][j]==1):
                                Adj[k][c]=j
                                c=c+1
                        
             return Adj
                     
        def pageRank(self):
                A=self.getA()
                pr=pageRank.pageRank(A)
                return pr

        def gettopology(self):
                
                A=self.getA()
                n=self.getN()
                """pr: PageRank classification of nodes"""
                pr=self.pageRank()
                """sorting of pagerank list of nodes in descending order"""
                lg=len(pr)
                Node_PR=list()
                for i in range(0,lg):
                        Node_PR.append([i,pr[i]])

                return Node_PR, n, A
                
        def getPDS(self):
                """get vector giving power dominating set - optimal PMU configuration"""
                """implementation of the integer linear programming formulation"""
                """minimisation of number of PMUs while guaranteeing that each node is observed"""
                """minimise sum of compents of X vector with the constraint (A+I).X>=1"""
                """, where X is the binary vector where X_i=1 if a PMU is placed at the node and 0 otherwise"""
                """A is the incidence matrix"""
                """I is the unity matrix"""
                
                A=self.getA()
                I=np.identity(self.N)

                B=A+I

                c=np.ones((self.N))

                b_l=np.ones((self.N))
                b_u=np.full_like(b_l, np.inf, dtype=float)

                constraints = LinearConstraint(B, b_l, b_u)


                integrality=np.ones_like(c)
                res=milp(c=c,constraints=constraints,integrality=integrality)
                
                
                pos=np.nonzero(res.x)

                return res.x
     
    
        def observability(self,PMUconfig):
                """determines if PMU coonfiguration makes system observable"""
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
                return obsvec

        def observability2(self,PMUvec):
                """determines if PMU coonfiguration makes system observable"""
                """returns binary vector (1 if node is observable, 0 otherwise)"""
                A=self.getA()
                """obsvec:observability vector"""
                obsvec=np.zeros(self.N)

                lg=len(PMUvec)
                for i in range(0,lg):
                       b_pmu=PMUvec[i]
                       if (b_pmu==1):
                               obsvec[i]=1
                               for j in range (0,lg):
                                       if (A[i][j]==1):
                                               obsvec[j]=1
                return obsvec

        
        def isobs(self,PMUconfig):
                """checks if all nodes are observable"""
                obsvec=self.observability(PMUconfig)
                l=len(obsvec)
                for i in range(0,l):
                        if obsvec[i]==0:
                                return 0
                return 1

        def isobs2(self,pmu):
                """checks if all nodes are observable"""
                obsvec=self.observability2(pmu)
                l=len(obsvec)
                for i in range(0,l):
                        if obsvec[i]==0:
                                return 0
                return 1
        """
        def isobs_constr(self,obsvec):
                l=len(obsvec)
                for i in range(0,l):
                        if obsvec[i]==0:
                                return 0
                return 1
        """
        
        def endnodes(self):
                """get list of endnodes in graph (nodes with only one neighbour)"""
                endnodes=list()
                n=self.N
                A=self.getA()
                for i in range(0,n):
                        sum=0
                        for j in range(0,n):
                                sum=sum+A[i][j]
             
                        if (sum==1):
                                endnodes.append(i)
                
                return endnodes

        def removeextra(self,PMUconfig):
                """test if a pmu can be removed while keeping observability."""
                vecPMU=PMUconfig.getPMUconfig()

                N=len(vecPMU)

                for i in range(1,N):
                        if (vecPMU[i]==1):
                                vecPMU[i]=0
                                PMUconfig.setPMUconfig(vecPMU)
                                obs=self.isobs(PMUconfig)
                                if (obs==1):
                                        return PMUconfig
                                else:
                                        vecPMU[i]=1
                return PMUconfig
                                
        def perturb(self,PMUconfig):
                """get different observable PMU configuration """
                """variables obs (observability) i (iteration)"""
                obs=0
                i=0
                """PMUconfig0: initial PMU configuration"""
                v0=PMUconfig.getPMUconfig()
                n=len(v0)
                PMUconfig0=PMUconfiguration.PMUconfiguration(n)
                PMUconfig0.setPMUconfig(v0)
                
                """info PMUconfig and graph"""
                A=self.getA()
                endnodes=self.endnodes()
                pmu=PMUconfig.getPMUnodes()

                PMUconfig2=PMUconfiguration.PMUconfiguration(n)
                

                while (obs==0)&(i<1000):
                                                
                        v=PMUconfig.shuffle(endnodes,A)
                        PMUconfig2.setPMUconfig(v[0])

                                                
                        obs=self.isobs(PMUconfig2)
                        if (obs==1) :
                                PMUconfig=PMUconfig.copyPMUconfig(PMUconfig2)
                                
                                return PMUconfig, i
                        
                        i=i+1

                return PMUconfig0, i


        def randomadditionPMUs(self,PMUconfig,npmus):
                A=self.getA()
                endnodes=self.endnodes()
                nodes=PMUconfig.getcandidates(endnodes)

                for i in range(0,npmus):
                        p=random.choice(nodes)
                        PMUconfig.addPMU(p)

                        nodes.remove(p)

                return PMUconfig
                        
                


