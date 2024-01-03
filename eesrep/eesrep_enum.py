"""Custom ENUMs used by EESREP"""
from enum import Enum


class TimeSerieType(Enum):
    """Time serie type enum, mostly used to decide how data are aggregated with different time step lengths.
    
        - Intensive : the time serie is averaged 
        - Extensive : the time serie is integrated
    """
    INTENSIVE = 1
    EXTENSIVE = 2
