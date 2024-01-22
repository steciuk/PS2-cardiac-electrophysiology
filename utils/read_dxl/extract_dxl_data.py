import re
from io import StringIO

import pandas as pd

from utils.decode_raw_content import decode_raw_content

DXL_RE = re.compile(r"DxL_(\d+).csv")
FILE_OF_FILES_RE = re.compile(r"(\d+)\sof\s(\d+)")


def extract_dxl_data(filenames, contents):
    # Find all DxL files
    dxl_files = {}
    for file, content in zip(filenames, contents):
        match = DXL_RE.match(file)
        if match:
            dxl_files[int(match.group(1))] = content

    if len(dxl_files) == 0:
        raise Exception("No DxL files uploaded")

    # Sort files by their number
    dxl_files = list(dict(sorted(dxl_files.items(), key=lambda item: item[0])).values())

    # Read all DxL files
    data = []
    meta = []
    signals = {}

    seen_files = set()
    expected_num_files = None

    for file in dxl_files:
        file = decode_raw_content(file)
        lines = file.split("\n")

        files_match = FILE_OF_FILES_RE.search(lines[13])
        if expected_num_files is None:
            expected_num_files = int(files_match.group(2))
        else:
            assert expected_num_files == int(files_match.group(2))

        num_file = int(files_match.group(1))
        assert num_file not in seen_files
        seen_files.add(num_file)

        print(f"Processing DxL file {num_file} of {expected_num_files}")

        meta_lines = lines[0:11]

        file_meta = {}
        for line in meta_lines:
            key, value = line.strip().split(" : ")
            file_meta[key] = value

        meta.append(file_meta)

        data_lines = lines[46:74]
        df_data = pd.read_csv(
            StringIO("".join(data_lines)), sep=",", index_col=0, header=None
        )
        df_data = df_data.transpose()
        df_data.columns = [column[:-1] for column in df_data.columns]
        data.append(df_data)

        signal_lines = lines[81:]
        start = 0
        blocks = []
        for i, line in enumerate(signal_lines[1:]):
            if not line.startswith(","):
                blocks.append(signal_lines[start:i])
                start = i

        blocks = blocks[:5]

        for block in blocks:
            df = pd.read_csv(StringIO("\n".join(block)), sep=",")
            first_column = df.columns[0]
            if first_column not in signals:
                signals[first_column[:-1]] = []

            df = df.drop(columns=[first_column])
            signals[first_column[:-1]].append(df)

    data = pd.concat(data)
    data = data.reset_index(drop=True)

    signals = {k: pd.concat(v, axis=1) for k, v in signals.items()}

    return meta, data, signals
