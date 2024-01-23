import os
import re
from io import StringIO

import pandas as pd

from utils.decode_raw_content import decode_raw_content

DXL_RE = re.compile(r"DxL_(\d+).csv")
FILE_OF_FILES_RE = re.compile(r"(\d+)\sof\s(\d+)")


def extract_local_dxl_data(paths):
    # Find all DxL files
    dxl_files = {}

    for path in paths:
        filename = path.split("/")[-1]
        if DXL_RE.match(filename):
            dxl_files[int(DXL_RE.match(filename).group(1))] = path

    def reader(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    return extract(dxl_files, reader)


def extract_dxl_data(filenames, contents):
    # Find all DxL files
    dxl_files = {}
    for file, content in zip(filenames, contents):
        match = DXL_RE.match(file)
        if match:
            dxl_files[int(match.group(1))] = content

    def reader(content):
        return decode_raw_content(content)

    return extract(dxl_files, reader)


def extract(dxls, reader):
    if len(dxls) == 0:
        raise Exception("No DxL files uploaded")

    # Sort by number
    dxls = list(dict(sorted(dxls.items(), key=lambda item: item[0])).values())

    data_table = []
    meta = []
    signals = {}

    seen_files = set()
    expected_num_files = None

    for file in dxls:
        file = reader(file)

        header, data = file.split("Begin data\n", 1)

        header = header.split("\n")
        files_match = FILE_OF_FILES_RE.search(header[13])
        if expected_num_files is None:
            expected_num_files = int(files_match.group(2))
        else:
            assert expected_num_files == int(files_match.group(2))

        num_file = int(files_match.group(1))
        assert num_file not in seen_files
        seen_files.add(num_file)

        print(f"Processing DxL file {num_file} of {expected_num_files}")

        meta_lines = header[0:11]

        file_meta = {}
        for line in meta_lines:
            key, value = line.strip().split(" : ")
            file_meta[key] = value

        meta.append(file_meta)

        data_blocks = data.split("\n\n")
        data_lines, signal_blocks = data_blocks[0][:-6], data_blocks[1:]

        df_data = pd.read_csv(StringIO(data_lines), sep=",", index_col=0, header=None)
        df_data = df_data.transpose()
        df_data.columns = [column[:-1] for column in df_data.columns]
        data_table.append(df_data)

        signal_blocks = signal_blocks[:5]
        signal_blocks[-1] = signal_blocks[-1].rstrip(
            "FFT spectrum is available for FFT maps only"
        )

        for block in signal_blocks:
            df = pd.read_csv(StringIO(block), sep=",")
            first_column = df.columns[0]
            if first_column not in signals:
                signals[first_column[:-1]] = []

            df = df.drop(columns=[first_column])
            signals[first_column[:-1]].append(df)

    data_table = pd.concat(data_table)
    data_table = data_table.reset_index(drop=True)

    signals = {k: pd.concat(v, axis=1) for k, v in signals.items()}

    return meta, data_table, signals
