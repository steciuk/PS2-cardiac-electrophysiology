import xml.etree.ElementTree as ET
import pandas as pd
import io

VERTICES_PATH_FROM_ROOT = "DIFBody/Volumes/Volume/Vertices"
FACES_PATH_FROM_ROOT = "DIFBody/Volumes/Volume/Polygons"


def read_landmark(content: str):
    landmark_xml = ET.fromstring(content)

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

    return vertices, faces
