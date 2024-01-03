set to_profile=%1

C:\Python37\Scripts\kernprof.exe -l %to_profile%
C:\Python37\python -m line_profiler %to_profile%.lprof > profiling