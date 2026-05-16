#dataclass is a decorator
#List is to provide type info
from dataclasses import dataclass
from typing import List

@dataclass
class Landmark:
    x: float
    y: float    
    z: float
    #Quantifying how accurately the landmarks are detected
    visibility: float

PoseFrame = List[Landmark]
PoseSequence = List[PoseFrame]


