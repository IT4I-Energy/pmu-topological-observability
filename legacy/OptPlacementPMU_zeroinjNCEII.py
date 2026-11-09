from OptPlacementPMU_zeroinj import OptPlacementPMU_zeroinj
import Graph_zeroinjectionNCEII


class OptPlacementPMU_zeroinjNCEII(OptPlacementPMU_zeroinj):
    def __init__(self,N,branch,zero_injections):
         self.g=Graph_zeroinjectionNCEII.Graph_zeroinjectionNCEII(N,branch,zero_injections)
         

   
