from enum import Enum

class SolverOption(Enum):
    
    METHOD="method"
    MILP_GAP="gap"
    PRINT_LOG="print_log"
    THREADS="threads"
    TIME_LIMIT="time_limit"
    WRITE_PROBLEM="write_problem"