"""
Created on Mon May 20 12:22:30 2024

Python package to repreent an UL model compatibel with ISB representation and
the OpenSIM MoBL-ARMS model (https://simtk.org/projects/upexdyn).
Package contains class and functions to define an UL model using the robotics
toolbox representation, manipulate the model, define deweighting algorithms and
interface to load, write and analyse OpenSIM file formats of the OpenSIM MoBl ARMS
model.

@author: vcrocher - Unimelb
"""
from setuptools import setup
setup(
    name='isbulmodel',
    version='0.1.0',
    description='Package to create and manipulate a simple UL model (5 or 7 DoFs)',
    author='Vincent Crocher',
    author_email='vcrocher@unimelb.edu.au',
    packages=['isbulmodel'],
    install_requires=['numpy',
                      'pandas',
                      'spatialmath-python',
                      'roboticstoolbox-python',
                      'matplotlib'
                      ],
)
