import base64
import os
import pandas as pd
import io
from utils.decode_raw_content import decode_raw_content

from utils.read_dxl.read_landmark import read_landmark

DXL_LANDMARK_GEO_NAME = "DxLandmarkGeo.xml"


def read_DxL(filenames, contents):
    if filenames is None:
        raise Exception("No files uploaded")

    if DXL_LANDMARK_GEO_NAME not in filenames:
        raise Exception("No DxLandmarkGeo.xml file uploaded")

    landmark_content = contents[filenames.index(DXL_LANDMARK_GEO_NAME)]
    landmark_string = decode_raw_content(landmark_content)

    vertices, faces = read_landmark(landmark_string)

    return vertices, faces
