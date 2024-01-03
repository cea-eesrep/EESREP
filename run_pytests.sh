#!/usr/bin/env bash

python_path=/volatile/catB/CPLEX/Python-3.7.9/python

if [ -f ".coverage" ]
then
    rm .coverage
fi

export PATH=$PATH:/home/trilogy/CPLEX/cplex/bin/x86-64_linux/

for solver in "CPLEX" "DOCPLEX" "pyomo" 
do
    export EESREP_SOLVER=$solver
    printf "\033[0;36mRunning tests for solver $EESREP_SOLVER \033[0m \n"
    if [ -f ".coverage" ]
    then
        $python_path -m pytest $(dirname "$0")/tests --cov=eesrep --cov-append --cov-report html --tb=no -W ignore::DeprecationWarning
    else
        $python_path -m pytest $(dirname "$0")/tests --cov=eesrep --cov-report html --tb=no -W ignore::DeprecationWarning
    fi
    
    $python_path -m pytest --nbmake tutorials
done

cp -R htmlcov ~