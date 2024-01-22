import base64
import io
import os
import re

import pandas as pd

from utils.decode_raw_content import decode_raw_content
from utils.read_dxl.extract_landmark import extract_landmark

DXL_RE = re.compile(r"DxL_(\d+).csv")


def read_DxL_project(filenames, contents):
    if filenames is None or len(filenames) == 0:
        raise Exception("No files uploaded")

    vertices, faces = extract_landmark(filenames, contents)

    return vertices, faces
