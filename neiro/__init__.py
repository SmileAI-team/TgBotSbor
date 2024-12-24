from dataclasses import dataclass
from typing import List
import numpy as np


@dataclass
class CariesTooth:
    caries_coord: List[int]
    caries_type: int

@dataclass
class Tooth:
    tooth_array: np.ndarray
    tooth_coord: List[int]


@dataclass
class MouthImage:
    array: np.ndarray
    mouth_type: str
    boxes: List[Tooth]
    caries_coord: List[CariesTooth]
