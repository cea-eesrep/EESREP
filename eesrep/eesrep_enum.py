"""Custom ENUMs used by EESREP"""
from enum import Enum


class TimeSerieType(Enum):
    """Time serie type enum, mostly used to decide how data are aggregated with different time step lengths.
    
        - Intensive : the time serie is averaged 
        - Extensive : the time serie is integrated
    """
    INTENSIVE = 1
    EXTENSIVE = 2

class SolverOption(Enum):
    METHOD="method"
    MILP_GAP="gap"
    PRINT_LOG="print_log"
    THREADS="threads"
    TIME_LIMIT="time_limit"
    WRITE_PROBLEM="write_problem"
    INTERMEDIATE_RESULTS_PATH="path_intermediary_results"