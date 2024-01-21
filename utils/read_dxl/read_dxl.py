import base64
import os
import pandas as pd
import io

from utils.read_dxl.read_landmark import read_landmark

DXL_LANDMARK_GEO_NAME = "DxLandmarkGeo.xml"


def read_DxL(filenames, contents):
    if filenames is None:
        raise Exception("No files uploaded")

    if DXL_LANDMARK_GEO_NAME not in filenames:
        raise Exception("No DxLandmarkGeo.xml file uploaded")

    landmark_content = contents[filenames.index(DXL_LANDMARK_GEO_NAME)]

    vertices, faces = read_landmark(landmark_content)

    return vertices, faces
