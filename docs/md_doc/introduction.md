# Introduction

EESREP is a is a component based energy system optimisation python module developed at CEA (DES/ISAS/DM2S/SERMA).

## Installation

To install EESREP, run:

```
python -m pip install eesrep
```

The EESREP module is compatible with several MILP modeler python module. As it only needs one of them to work, none is installed with EESREP. To get EESREP to work with its built-in interfaces, have installed at least one of the following modules:
- **mip** : Allows using the CBC solver installed with it. The CBC solver installation can however present some difficulties on linux or without the proper compiling tools (more information can be found at https://python-mip.readthedocs.io/en/latest/install.html);
- **docplex** : Official CPLEX modeling module (solver only free for students or with a maximum of 1000 variables and constraints, see https://pypi.org/project/docplex/);
- **pyomo** : Interfaces with several solvers that have to be installed aside of it (see installation instructions at https://pyomo.readthedocs.io/en/stable/installation.html).

## Quick start

Several tutorials are provided with EESREP and are present in the documentation, they are sorted in several categories:
- MILP_i : explains how MILP models work, and explains how to build one from scratch;
- USE_i : explains how EESREP works, and how to set-up an EESREP model;
- DEV_i : explains how to customize your EESREP build and create your own components.

A use case is present in the git repositery along with the test base that provide many use examples (respectively folders use_cases and tests):
https://github.com/tmoulignier/EESREP

Some user-made components are also present in the user_components folder of the repository.