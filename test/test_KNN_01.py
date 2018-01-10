from sklearn.neighbors import NearestNeighbors
from sklearn import datasets
import numpy as np

X = np.array([[-1, -1], [-2, -1], [-3, -2], [1, 1], [2, 1], [3, 2]])

# X = np.array([[0,1],
# 				[0,2],
# 				[0,3],
# 				[0,4],
# 				[0,5],
# 				[0,6]])

nbrs = NearestNeighbors(n_neighbors=2, algorithm='auto').fit(X)

distances, indices = nbrs.kneighbors([[0,0]])

print(indices)