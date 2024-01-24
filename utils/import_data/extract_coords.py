import numpy as np


def extract_coords(x):
    coords = x.split("+")[1].strip()
    if not len(coords) == 2:
        return np.nan, np.nan
    if not coords[0] in ["A", "B", "C", "D"]:
        return np.nan, np.nan
    if not coords[1] in ["1", "2", "3", "4"]:
        return np.nan, np.nan

    return ord(coords[0]) - ord("A"), int(coords[1]) - 1
