# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

# To publish :
# python3 -m pip install --upgrade build twine
# python3 -m build
# python3 -m twine upload --repository pypi dist/*

setup(
            name='eesrep',
            version='0.1.3',
            description='EESREP is a component based energy system optimisation python module.',
            long_description='EESREP is a component based energy system optimisation python module.',
            author='CEA',
            maintainer="Thibault Moulignier",
            author_email='Thibault.Moulignier@cea.fr',
            packages=find_packages(),
            package_data={'eesrep': ['components/*.py', 'solver_interface/*.py']},
            url="https://github.com/tmoulignier/EESREP",
            keywords="optimization, modelling, energy, system",
            python_requires=">=3.6, <4",
            install_requires=["pandas", 
                              "numpy",
                              "matplotlib"],
            project_urls={  # Optional
                  "Bug Reports": "https://github.com/tmoulignier/EESREP/issues",
                  "Doc": "https://eesrep.readthedocs.io/en/latest//index.html",
                  "Source": "https://github.com/tmoulignier/EESREP",
            },
            extras_require={
                  'docs-requirements-txt': [
                        'sphinx',
                        'sphinx_rtd_theme',
                        'myst_parser',
                        'numpydoc',
                        'nbsphinx',
                        'ipython',
                        'jupyter',
                        'docplex',
                        'cplex',
                        'mip',
                        'pyomo',
                        'pandoc'
                  ]
            }
      )
