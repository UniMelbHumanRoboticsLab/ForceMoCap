import numpy as np
import pandas as pd
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
print(sys.path)

data = pd.read_csv(os.path.join(os.path.dirname(__file__), './bounds.csv') )
print(data.max(axis=0)) # will return max value of each column)
print(data.min(axis=0)) # will return max value of each column)