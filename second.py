import numpy as np

def hex_int(x):
    return int(x,16)

nums = np.array(['e2', '3f', '2a', '23'])
hexes = np.vectorize(hex_int)(nums)
print(hexes)