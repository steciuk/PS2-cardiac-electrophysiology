import xml.etree.ElementTree as ET
import pandas as pd
import io
from scipy.spatial import Delaunay

from utils.decode_raw_content import decode_raw_content


VERTICES_PATH_FROM_ROOT = "DIFBody/Volumes/Volume/Vertices"
FACES_PATH_FROM_ROOT = "DIFBody/Volumes/Volume/Polygons"


def read_landmark(content):
    landmark_string = decode_raw_content(content)
    landmark_xml = ET.fromstring(landmark_string)

    vertices_text = landmark_xml.find(VERTICES_PATH_FROM_ROOT).text
    faces_text = landmark_xml.find(FACES_PATH_FROM_ROOT).text

    vertices_cords = pd.read_csv(io.StringIO(vertices_text), sep=" ", header=None)
    vertices_creating_faces = pd.read_csv(io.StringIO(faces_text), sep=" ", header=None)

    vertices_cords = vertices_cords.dropna(axis=1, how="all")
    vertices_cords.columns = ["id", "x", "y", "z"]
    vertices_creating_faces = vertices_creating_faces.dropna(axis=1, how="all").astype(
        int
    )
    vertices_creating_faces.columns = ["id", "v1", "v2", "v3"]

    # create df of all faces from vertices_cords and vertices_creating_faces
    # faces = pd.DataFrame()
    # faces["v1"] = vertices_cords.iloc[vertices_creating_faces["v1"]]["id"].values
    # faces["v2"] = vertices_cords.iloc[vertices_creating_faces["v2"]]["id"].values
    # faces["v3"] = vertices_cords.iloc[vertices_creating_faces["v3"]]["id"].values
