# Based on section 9.2 AIS Data Cleaning from the MobilityDataScience book
# and https://github.com/mahmsakr/MobilityDataScienceClass/tree/main/Mobility%20Data%20Cleaning
from sqlalchemy import create_engine, text
import json
import zipfile
import os
import geopandas as gpd
import pandas as pd
import numpy as np
from utils import get_csv_from_zip

script_dir = os.path.dirname(os.path.abspath(__file__))
output_file= os.path.join(script_dir, ".", "trajectories_mf1.json")
config_path = os.path.join(script_dir, "..", "config.json")
with open(config_path, "r") as file:
    config = json.load(file)


database_url = (
    f"postgresql://{config['DB_USER']}:{config['DB_PASS']}@"
    f"{config['DB_HOST']}:{config['DB_PORT']}/{config['DB_NAME']}"
)

# Create the SQLAlchemy engine
engine = create_engine(database_url)
zip_path = os.path.join(script_dir, "aisdk-2024-08-07.zip")
data_csv_path = get_csv_from_zip(zip_path,script_dir)
data_csv_path=os.path.abspath(data_csv_path)
print(data_csv_path)
#update this based on whether you're running your db from docker or local/ this is a docker version, otherwise comment it out
container_csv_path = "/tmp/aisdk.csv"
container_name = "mobilitydb"  # Your container name
docker_cmd = f"docker cp {data_csv_path} {container_name}:{container_csv_path}"
os.system(docker_cmd)
data_csv_path= container_csv_path

# Data collection and 9.3 Cleaning Static Attribute +9.4 Voyage related Attribbutes:
try:
    init_sql= os.path.join(script_dir, ".", "init.sql")
    with open(init_sql, "r") as sql_file:
        sql_query = sql_file.read()

    stmt = text(sql_query).bindparams(data_csv_path=data_csv_path)

    with engine.connect() as conn:
    
        with conn.begin():
            conn.execute(stmt)
            print(f"Successfully loaded data from {data_csv_path}")

except Exception as e:
    print(f"Error loading data: {e}")
    raise

def export_json_from_view(engine, output_file=output_file):
    query = "SELECT json_data FROM ships_json ORDER BY mmsi;"
    
    try:
    
        df = pd.read_sql(query, engine)
        
        if df.empty:
            print("No data found in ships_json view")
            return []
        
     
        json_ready = df['json_data'].tolist()
   
        with open(output_file, "w") as f:
            json.dump(json_ready, f, indent=2, default=str)
        
        print(f"Successfully exported {len(json_ready)} ais vessels to {output_file}")
        return json_ready
        
    except Exception as e:
        print(f"Error exporting JSON: {e}")
        raise


if __name__ == "__main__":

    
    #to JSON
    export_json_from_view(engine, output_file=output_file)
   
    
    # DROP VIEW IF EXISTS ships_json CASCADE;
    # DROP TABLE IF EXISTS Ships CASCADE;

    drop_tables_sql = """
        DROP TABLE IF EXISTS AISInputFiltered CASCADE;
        DROP TABLE IF EXISTS AISInput CASCADE;
    """
    try:
        with engine.connect() as conn:
            with conn.begin():
                conn.execute(text(drop_tables_sql))
                #  Ships, ships_json
        print("dropped ables (AISInput, AISInputFiltered).")
    except Exception as e:
        print(f"Error during cleanup: {e}")
