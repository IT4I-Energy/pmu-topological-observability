from PMUconfiguration import PMUconfiguration
#import Graph_zeroinjection, PMUconfiguration, ILS

class PMUconfiguration_zeroinj(PMUconfiguration):
    def shuffle(self,endnodes,A):        
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
        
        
        print('cand=',j)
        print('chpmu=',chpmu)
        print(vec)
        
        p=random.choice(chpmu) #cha
        #print('from ',p, ' to ',j)
        """move adjacent pmu to random node j"""
        vec2[p]=0
        vec2[j]=1
        
        return vec2
        
    def export(self):
        N=len(self.PMUvec)

        filename='Results/pmuIEEE'+str(N)+'_zeroinj.yaml'
        pmu=self.getPMUnodes()

        with open(filename, 'w') as file:
            dump(pmu,file)

        

        
