import Cluster

class ListofClusters:
    def __init__(self):
        self.clusters=list()

    def findCluster(self, i):
        """finds cluster containing node i"""
        pos=0
        for c in self:
            test=c.isinCluster(i)
            if (test==1):
                return c,pos
            pos=pos+1

        return list(),0

    def addCluster(self, c):
        self.clusters.append(c)
        

    def displayclusters(self):
        i=0
        for c in self.clusters:
            print ("cluster ",i)
            c.display()
            i=i+1
    
    
