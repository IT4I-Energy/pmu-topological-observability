import numpy as np, random
from yaml import load, dump, safe_load

class PMUconfiguration:
    def __init__(self,N):
        self.PMUvec=np.zeros(N)

    def addPMU(self,i):
        """add PMU at node i"""
        self.PMUvec[i]=1

    def setPMUconfig(self,v):
        """set PMUvec"""
        l=len(v)
        for i in range(0,l):
           
            self.PMUvec[i]=v[i]

    def copyPMUconfig(self,PMUconfig):
        """copy PMUconfig"""
        v=PMUconfig.getPMUconfig()
        self.setPMUconfig(v)
        return self

    def getPMUconfig(self):
        """returns binary vector giving nodes with PMUs"""
        return self.PMUvec

    def getPMUvec(self,pmu):
        """get PMUvec from pmu(nodes with pmu)"""
        lg=len(pmu)
        for i in range(0,lg):
            j=pmu[i]
            self.PMUvec[j]=1
        return self.PMUvec

    def setPMUvec(self,pmu):
        v=self.getPMUvec(pmu)
        self.setPMUconfig(v)
        return self
    
    def getnPMU(self):
        """return number of PMUs in configuration"""
        s=int(sum(self.PMUvec))
        return s
    
    def testPMUconfig(self,PMUconfigmin):
        """test if PMUconfig has less number of PMUs than self"""
        n_min=PMUconfigmin.getnPMU()
        n=self.getnPMU()
        if (n<n_min):
            PMUconfigmin.copyPMUconfig(self)
            return self
        else:
            return PMUconfigmin
        
    def getPMUnodes(self):
        """returns nodes with pmu"""
        pmu=list()
        l=len(self.PMUvec)
        for i in range(0,l):
            if (self.PMUvec[i]==1):
                pmu.append(i)
        return pmu

    def PPA1(self,A):
        """first part of PageRank Placement Algorithm:"""
        """placement of a PMU at adjacent node of nodes with only one neighbour"""
        n=len(A)
        
        for i in range(0,n):
            sum=0
            for j in range(0,n):
                sum=sum+A[i][j]
             
            if (sum==1):
                for j in range(0,n):
                    if (A[i][j]==1):
                        self.addPMU(j)
       

    def PPA2(self,g,pr):
        """second part of PageRank Placement Algorithm:"""
        """placement of PMUs at most important nodes"""
        """pr: PageRank classification of nodes"""

        """sorting of pagerank list of nodes in descending order"""
        lg=len(pr)
        Node_PR=list()
        for i in range(0,lg):
            Node_PR.append([i,pr[i]])      

            Node_PR.sort(key=lambda x:x[1],reverse=True)
      
        """Placement of PMUs"""
        obsvec=g.observability(self)
        for a in Node_PR:
            i=a[0]
            if (obsvec[i]==0):
                self.addPMU(i)
            obsvec=g.observability(self)    
            o=g.isobs(self)
            if (o==1):break

    
               
                
    def exchange(self,i,j):
        self.PMUvec[i]=0
        self.PMUvec[j]=1
        

        
    def getcandidates(self,endnodes):
        """get potential nodes for PMU placement - second stage of ILS random addition of PMUs"""
        
        
        l=len(self.PMUvec)
        
        e=len(endnodes)
        """potential nodes"""
        nodes=list(range(0,l))
                
        for i in range(0,e):
            nodes.remove(endnodes[i])
        
        pmu=self.getPMUnodes()
        
        lpmu=len(pmu)
        #print('pmu ',pmu)
        for j in range(0,lpmu):
            #print('remove ',j,' ',pmu[j])
            if (pmu[j] in nodes):
                nodes.remove(pmu[j])
        
        return nodes
        
    def adjacentPMU(self,A,j):
        """get pmus adjacent to a node, which make node observable"""
        pmu=self.getPMUnodes()
        chpmu=list()
        n=len(A)
        
        for k in range(0,n):
            if (A[j][k]==1):
                if k in pmu:
                     chpmu.append(k)
        return chpmu
    
    def shuffle(self,endnodes,A):        
        l=0
        vec=self.getPMUconfig()
        
        l=len(vec)

        vec2=np.zeros(l)
        for i in range(0,l):
            vec2[i]=vec[i]
        
        nodes=self.getcandidates(endnodes)

        
        j=random.choice(nodes)

        chpmu=self.adjacentPMU(A,j)
        """
        print('cand=',j)
        print('chpmu=',chpmu)
        print(vec)
        """
        p=random.choice(chpmu) #cha
        #print('from ',p, ' to ',j)
        """move adjacent pmu to random node j"""
        vec2[p]=0
        vec2[j]=1
        
        return vec2, j
        
       
    def shuffle_zeroinj(self,endnodes,A):        
            l=0
            lg=0
            vec=self.getPMUconfig()
            l=len(vec)

            vec2=np.zeros(l)
            for i in range(0,l):
                vec2[i]=vec[i]
        
            nodes=self.getcandidates(endnodes)

            while(lg==0):
                j=random.choice(nodes)

                chpmu=self.adjacentPMU(A,j)
                lg=len(chpmu)
        
            """    
            print('cand=',j)
            print('chpmu=',chpmu)
            print(vec)
            """
            p=random.choice(chpmu) #cha
            #print('from ',p, ' to ',j)
            """move adjacent pmu to random node j"""
            vec2[p]=0
            vec2[j]=1
        
            return vec2


    def export(self):
            N=len(self.PMUvec)
            filename='Results/pmuIEEE'+str(N)+'.yaml'

            pmu=self.getPMUnodes()

            with open(filename, 'w') as file:
                dump(pmu,file)

    def fromfile(self,file):
        filename='Results/'+file

        with open(filename,'r') as f:
            
            pos=safe_load(f)
            for i in pos:
                self.addPMU(i)

        

            
                       
        
        

