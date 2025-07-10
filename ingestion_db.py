import psycopg2
from sqlalchemy import create_engine
import pandas as pd
import os
import logging
import time

logging.basicConfig(filename = "logs/inventory_db.log",
                    level = logging.DEBUG,
                    format = "%(asctime)s - %(levelname)s - %(message)s" ,
                    filemode = "a")

username = "postgres"
password = "986877"
host = "localhost"
port = "5432"
database = "inventory"

# Create a connection string
engine = create_engine(f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}")

'''This function will ingest the dataframes into tables
    if_exists = 'append' if you want to append the incomming data to the table'''
def ingest_db(df,table_name,engine):
    df.to_sql(table_name,con = engine, if_exists = 'replace', index = False)
    
'''This function will load CSV files as dataframes and ingest into db'''
def load_raw_data():
    start = time.time()
    for file in os.listdir('data'):
        if '.csv' in file:
            df = pd.read_csv('data/'+file)
            logging.info(f'ingesting {file} in database')
            ingest_db(df, file[:-4], engine)
    end = time.time()
    total_time = end-start/60
    logging.info('--------------------Ingestion Completed--------------------')
    logging.info(f'Total time taken for Ingestion {total_time} minutes')

if __name__ == '__main__':
    load_raw_data()