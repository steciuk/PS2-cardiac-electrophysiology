import base64
import io
import os
import re

import pandas as pd

from utils.read_dxl.extract_dxl_data import extract_dxl_data
from utils.read_dxl.extract_landmark import extract_landmark

DXL_RE = re.compile(r"DxL_(\d+).csv")


def read_DxL_project(filenames, contents):
    if filenames is None or len(filenames) == 0:
        raise Exception("No files uploaded")

    print(os.path.dirname(filenames[0]))

    vertices, faces = extract_landmark(filenames, contents)
    meta, data, signals = extract_dxl_data(filenames, contents)

    return vertices, faces, meta, data, signals
