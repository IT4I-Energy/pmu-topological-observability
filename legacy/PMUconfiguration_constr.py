from PMUconfiguration import PMUconfiguration
import numpy as np
import random
from yaml import safe_load
import re

class PMUconfiguration_constr(PMUconfiguration):

    def __init__(self,N,nImes):
        self.PMUvec=np.zeros(N)
        self.Imes=list()
        self.nImes=nImes

    def getnImes(self):
        return self.nImes

    def getImes(self):
        return self.Imes

    def addImes2(self,Imes):
        for e in Imes:
            self.Imes.append((e[0],e[1]))

    def addPMU2(self,i,nImes,G):
        """add PMU at node i"""
        self.PMUvec[i]=1
        adjnodes=G.get_adjacentnodes(i)

        nadj=len(adjnodes)
        Imes=list()
        
        if (nImes<=nadj):
            nodesImes=random.sample(adjnodes,nImes)
            for k in range(0,nImes):
                Imes.append([i,adjnodes[k]])
        
        elif (nImes>nadj):
            nodesImes=random.sample(adjnodes,nadj)
            for k in range(0,nadj):
                Imes.append([i,adjnodes[k]])
         
        
        
        
        
        self.addImes2(Imes)

    """        
    def setPMUconfig(self,PMUconfig):
        
        v=self.getPMUconfig()
        Imes=self.getImes()
        l=len(v)
        
        #for i in range(0,l):
        #    self.PMUvec[i]=v[i]
        self.PMUvec=[e for e in v]

        for e in Imes:
            self.Imes.append(e[0], e[1])
    """                         

    def setPMUconfigv(self,v):
        """set PMUvec"""
        l=len(v)
        self.PMUvec=[e for e in v]
        """for i in range(0,l):
            self.PMUvec[i]=v[i]
        """

    def setPMUconfigI(self,Imes):
        self.Imes=list()
        for e in Imes:
            self.Imes.append((e[0], e[1]))

        
    def copyPMUconfig(self,PMUconfig):
        """copy PMUconfig"""
        v=PMUconfig.getPMUconfig()
        Imes=PMUconfig.getImes()
        self.setPMUconfigv(v)
        self.setPMUconfigI(Imes)
        return self
    
    
    def ppa1_addmes(self,g,nImeas,obsvec):
          """add measurements to pmu at end node if nImeas>1"""
          Node_PR, n, A=g.gettopology()
        
          adjnode=self.Imes[0][1]  
          startnode=self.Imes[0][0]          
          if (nImeas>1):
              
              adjnodespr=list()
              for k in range(0,n):
                  if (A[startnode][k]==1):
                      adjnodespr.append(Node_PR[k])
              lg=len(adjnodespr)
              adjnodespr.sort(key=lambda x:x[1],reverse=True)
              id=0

              toadd=nImeas-1
              for l in range(0,toadd):
                  if (l<lg):
                      k=adjnodespr[id][0]
                      #if (k!=startnode):                      
                      self.Imes.append([startnode,k])
                      obsvec[k]=1
                  id=id+1
                  
          return obsvec
    
    
    def PPA1(self,g,nImeas):
          """first part of PageRank Placement Algorithm:"""
          """placement of a PMU at adjacent node of nodes with only one neighbour"""
          Node_PR, n, A=g.gettopology()

          obsvec=np.zeros(n)
        
          for i in range(0,n):
              sum=0
              for j in range(0,n):
                  sum=sum+A[i][j]
             
              if (sum==1):
                  for j in range(0,n):
                      if (A[i][j]==1):
                          self.addPMU(j)
                          self.Imes.append([j,i])
                          obsvec[i]=1
                          obsvec[j]=1
          obsvec=self.ppa1_addmes(g,nImeas,obsvec)
          return obsvec

          
    def addImes(self,j,AdjNode_PR,obs,obsvec,nImeas,g):
        
        nmeas=0
        #if (nImeas==nmeas):
        #    return obsvec,I_measurements
        
        nAdj=len(AdjNode_PR)
        brmes=list()
        k=0
        
        for a in AdjNode_PR:
            i=a[0]
            if (nmeas<nImeas):

                #print('i=',i)
            
                if (obsvec[i]==0):
                    #print('measurement ',j,'-',i)
                    self.Imes.append([j,i])
                    brmes.append(i)
                    obsvec[i]=1
                    nmeas=nmeas+1
        obsvec=self.ppa1_addmes(g,nImeas,obsvec)
                
        if (nmeas<nImeas):
            k=0
            for a in AdjNode_PR:
                i=a[0]
                if (i not in brmes):
                    #print('2')
                    self.Imes.append([j,i])
                    brmes.append(i)
                    obsvec[i]=1
                    nmeas=nmeas+1
                if (nmeas==nImeas):break
                k=k+1
            
        return self
                
            
    def selectbranches(self,pr,A,j,obsvec,nImeas,g):
        """select branches for PMU current measurements"""
        nmeas=0
        n=len(A)
        AdjNode_PR=list()
        for k in range(0,n):
            if (A[j][k]==1):
                AdjNode_PR.append([k,pr[k]])

        AdjNode_PR.sort(key=lambda x:x[1],reverse=True)
        #print('node ',j)
        #print(AdjNode_PR)

        PMUconfig=self.addImes(j,AdjNode_PR,0,obsvec,nImeas,g)
       

        return PMUconfig


    
    def PPA2(self,g,nImeas,obsvec):
        """second part of PageRank Placement Algorithm:"""
        """placement of PMUs at most important nodes"""
        
        A=g.getA()
        n=g.getN()
        """pr: PageRank classification of nodes"""
        pr=g.pageRank()
        """sorting of pagerank list of nodes in descending order"""
        lg=len(pr)
        Node_PR=list()
        for i in range(0,lg):
               Node_PR.append([i,pr[i]])
               
        Node_PR.sort(key=lambda x:x[1],reverse=True)
      
        """Placement of PMUs"""
        
        for a in Node_PR:
            i=a[0]
            if (obsvec[i]==0):
                self.addPMU(i)
                #print('i=',i)
                obsvec[i]=1
                """selection of branches for current measurements"""
                PMUconfig=self.selectbranches(pr,A,i,obsvec,nImeas,g)

            o=g.isobs_constr(self)
            #o=g.isobs(obsvec)
            #print('o=',o)
            if (o==1):
                #print('obsvec=',obsvec)
                return obsvec 
        return PMUconfig

    def shuffle_constr(self,g,nImes):        
            l=0
            vec=self.getPMUconfig()
            endnodes=g.endnodes()
            A=g.getA()
            l=len(vec)

            vec2=np.zeros(l)
            vec2=[e for e in vec]
            """
            for i in range(0,l):
                vec2[i]=vec[i]
            """
            nodes=self.getcandidates(endnodes)
            chpmu=list()
            
            while len(chpmu)==0:
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

            N=g.getN()
            PMUconfig2=PMUconfiguration_constr(N,nImes)
            PMUconfig2.setPMUconfigv(vec2)

            Imes2=g.selbranches(self,p)
            """add current measurements from j"""
            adjnodes=g.get_adjacentnodes(j)

            nadj=len(adjnodes)
            
            if (nImes<=nadj):
                nodesImes=random.sample(adjnodes,nImes)
            elif (nImes>nadj):
                nodesImes=random.sample(adjnodes,nadj)
                
            lg=len(nodesImes)
            for k in range(0,lg):
                     s=[j,nodesImes[k]]
                     Imes2.append(s)

            PMUconfig2.setPMUconfigI(Imes2)
            
            
            return PMUconfig2, j
        
    def getPMUmes(self):
            pmus=self.getPMUnodes()
            Imeasurements=self.getImes()
            measurements=list()

            return pmus, Imeasurements

        
    def fromfile(self,file1,file2):
        filename1='Results/'+file1
        filename2='Results/'+file2
        
        with open(filename1,'r') as f:
            
            pos=safe_load(f)
            for i in pos:
                self.addPMU(i)

        with open(filename2,'r') as g:
            lines_all=g.readlines()

        Imes=list()
        br=list()
        nl=len(lines_all)
        i=0
        #for line in lines_all:
        #for i in range(0,nl):
        while (i<nl):
            line=lines_all[i]
            digits_line=re.findall(r'\d+',line)
            if (len(digits_line)!=0):
                
                r=int(digits_line[0])
                i=i+1
                line=lines_all[i]
                digits_line=re.findall(r'\d+',line)
                s=int(digits_line[0])
                Imes.append([r,s])
            i=i+1
                #br.append(digits_line)
#                if (len(br)==2):
#                   
#                    Imes.append([br[0],br[1]])
#                    #self.addImes2([br[0],br[1]])
#                    br=list()

        self.addImes2(Imes)
            
            
        
