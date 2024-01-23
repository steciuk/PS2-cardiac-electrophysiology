import base64
import io
import os
import re
import tkinter as tk
from tkinter import filedialog

import pandas as pd

from utils.read_dxl.extract_dxl_data import extract_dxl_data, extract_local_dxl_data
from utils.read_dxl.extract_landmark import extract_landmark, extract_local_landmark

DXL_RE = re.compile(r"DxL_(\d+).csv")


def read_DxL_project(filenames, contents):
    if filenames is None or len(filenames) == 0:
        raise Exception("No files uploaded")

    vertices, faces = extract_landmark(filenames, contents)
    meta, data, signals = extract_dxl_data(filenames, contents)

    return {
        "vertices": vertices,
        "faces": faces,
        "meta": meta,
        "data": data,
        "signals": signals,
    }


def read_local_DxL_project():
    root = tk.Tk()
    root.withdraw()

    paths = filedialog.askopenfilenames()
    root.destroy()

    if len(paths) == 0:
        raise Exception("No files selected")

    vertices, faces = extract_local_landmark(paths)
    meta, data, signals = extract_local_dxl_data(paths)

    return {
        "vertices": vertices,
        "faces": faces,
        "meta": meta,
        "data": data,
        "signals": signals,
    }
