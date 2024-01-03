$solvers = @("CBC", "CPLEX", "DOCPLEX", "pyomo")

if ( Test-Path .coverage -PathType Leaf ) {
    rm .coverage
}

For ($i=0; $i -lt $solvers.Length; $i++) {
    $env:EESREP_SOLVER=$solvers[$i]
    Write-Host "Running tests for solver $env:EESREP_SOLVER" -ForegroundColor Blue
    
    if ( Test-Path .coverage -PathType Leaf ) {
        py7 -m pytest $PSScriptRoot\tests --cov=eesrep --cov-append --cov-report html --tb=no -W ignore::DeprecationWarning
    }
    else{
        py7 -m pytest $PSScriptRoot\tests --cov=eesrep --cov-report html --tb=no -W ignore::DeprecationWarning
    }

    py7 -m pytest --nbmake tutorials
}