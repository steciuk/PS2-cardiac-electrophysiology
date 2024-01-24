# PS2 Cardiac Electrophysiology

Python, Dash and Plotly app for analyzing cardiac electrophysiology data.

## How to run
Install dependencies:
```bash
pip install -r requirements.txt
```
Run the app:
```bash
python main.py
```
Open web browser and go to the address shown in the terminal (http://127.0.0.1:8050/) to view the app.

## Compatible formats

### Geometry data
Geometry data should be in `.xml` file named `DxLandmarkGeo.xml` with the following structure:
```xml
<DIF>
    <DIFBody>
        <Volume>
            <Vertices>
                ...
                -34.1004  26.8820  224.2449 
                -33.5852  26.7199  224.6685 
                -34.0837  26.3541  224.4417 
                ...
            </Vertices>
            <Polygons>
                ...
                6 4 7
                2 8 3
                1 4 5
                ...
        </Volume>
    </DIFBody>
</DIF>
```

where each line in `<Vertices>` contains the x, y and z coordinates of a vertex, and each line in `<Polygons>` contains the indices of the vertices that make up a polygon.

### Recording data
Recording data should be in `.csv` files named `DxL_*.csv` where `*` is the number of the recording. Each file should contain the following structure: