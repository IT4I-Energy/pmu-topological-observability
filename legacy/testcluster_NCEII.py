
import Graph_zeroinjectionNCEII

import getinfoNCEII as gi


branch,zero_injections=gi.getinfoNCEII()

N=233


G=Graph_zeroinjectionNCEII.Graph_zeroinjectionNCEII(N,branch,zero_injections)

clusters=G.getClustersZeroInjections(zero_injections)
clusters.displayclusters()
