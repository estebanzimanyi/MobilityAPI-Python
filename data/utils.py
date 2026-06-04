
from sqlalchemy import create_engine
import numpy as np
import pandas as pd
import geopandas as gpd
import plotly.io as pio
from io import BytesIO
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, State
import dash
import os
import zipfile



def get_csv_from_zip(zip_path, extract_path="."):
    # Ensure data filder exists
    os.makedirs(extract_path, exist_ok=True)
    csv_files = [f for f in os.listdir(extract_path) if f.endswith(".csv")]
    if csv_files:
        return os.path.join(extract_path, csv_files[0])
# unzio
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
    csv_files = [f for f in os.listdir(extract_path) if f.endswith(".csv")]
    if not csv_files:
        raise Exception(
            "No CSV found in ZIP! Try downloading a different AIS dataset.")
    return os.path.join(extract_path, csv_files[0])

