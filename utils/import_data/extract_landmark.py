import io
import xml.etree.ElementTree as ET

import pandas as pd

from utils.decode_raw_content import decode_raw_content

DXL_LANDMARK_GEO_NAME = "DxLandmarkGeo.xml"
VERTICES_PATH_FROM_ROOT = "DIFBody/Volumes/Volume/Vertices"
FACES_PATH_FROM_ROOT = "DIFBody/Volumes/Volume/Polygons"


def extract_landmark(filenames, contents):
    if DXL_LANDMARK_GEO_NAME not in filenames:
        raise Exception("No DxLandmarkGeo.xml file uploaded")

    landmark_content = contents[filenames.index(DXL_LANDMARK_GEO_NAME)]
    landmark_string = decode_raw_content(landmark_content)

    return extract(landmark_string)


def extract_local_landmark(paths):
    landmark_path = None
    for path in paths:
        if path.endswith(DXL_LANDMARK_GEO_NAME):
            landmark_path = path
            break

    if landmark_path is None:
        raise Exception("No DxLandmarkGeo.xml file selected")

    with open(landmark_path, "r") as f:
        landmark_string = f.read()
        return extract(landmark_string)


def extract(landmark_string):
    print(f"Processing {DXL_LANDMARK_GEO_NAME}")

    landmark_xml = ET.fromstring(landmark_string)

    vertices_text = landmark_xml.find(VERTICES_PATH_FROM_ROOT).text
    faces_text = landmark_xml.find(FACES_PATH_FROM_ROOT).text

    vertices = pd.read_csv(io.StringIO(vertices_text), sep=" ", header=None)
    faces = pd.read_csv(io.StringIO(faces_text), sep=" ", header=None)

    vertices = vertices.dropna(axis=1, how="all").dropna(axis=0, how="all")
    faces = faces.dropna(axis=1, how="all").dropna(axis=0, how="all")

    faces = faces.astype(int)
    vertices.columns = ["x", "y", "z"]
    faces.columns = ["v1", "v2", "v3"]
    faces = faces - 1

    print(f"Found {len(vertices)} vertices and {len(faces)} faces")
    return vertices, faces