export PROFILING_PYTHON="./../Python-3.7.9"

$PROFILING_PYTHON/local_files/bin/kernprof -l $1
$PROFILING_PYTHON/python -m line_profiler $1.lprof > profiling