import psycopg2
from sqlalchemy import create_engine
import pandas as pd
import os
import logging
import time
from ingestion_db import ingest_db

logging.basicConfig(
                filename="logs/get_vendor_summary.log" ,
                level=logging.DEBUG ,
                format = "%(asctime)s - %(levelname)s - %(message)s" ,
                filemode = "a")

username = "postgres"
password = "986877"
host = "localhost"
port = "5432"
database = "inventory"

conn = create_engine(f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}")

def create_vendor_summary(conn):
    '''This function will merge the different tables to get the overall vendor summary and adding new columns in the resultant data'''
    vendor_sales_summary = pd.read_sql_query( '''
     WITH freight_summary AS (
            SELECT
                "VendorNumber",
                SUM("Freight") AS "FreightCost"
            FROM vendor_invoice
            GROUP BY "VendorNumber"),
    
     PurchaseSummary AS (
        SELECT
            p."VendorNumber",
            p."VendorName",
            p."Brand",
            p."Description",
            p."PurchasePrice",
            pp."Price" as "ActualPrice",
            pp."Volume",
            SUM(p."Quantity") as "TotalPurchaseQuantity",
            SUM(p."Dollars") as "TotalPurchaseDollars"
        FROM purchases p
        JOIN purchase_prices pp
        ON p."Brand" = pp."Brand"
        where p."PurchasePrice" > 0
        GROUP BY  p."VendorNumber",p."VendorName", p."Brand", p."PurchasePrice",pp."Volume",pp."Price",p."Description"),

         SalesSummary As ( 
            SELECT
                "VendorNo", "Brand",
                SUM("SalesDollars") as "TotalSalesDollars",
                SUM("SalesPrice") as "TotalSalesPrice",
                SUM("SalesQuantity") as "TotalSalesQuantity",
                SUM("ExciseTax") as "TotalExciseTax"
                FROM sales
                GROUP BY "VendorNo","Brand")
        
            SELECT
                ps."VendorNumber",
                ps."VendorName",
                ps."Brand",
                ps."Description",
                ps."PurchasePrice",
                ps."ActualPrice",
                ps."Volume",
                ps."TotalPurchaseQuantity",
                ps."TotalPurchaseDollars",
                ss."TotalSalesQuantity",
                ss."TotalSalesDollars",
                ss."TotalSalesPrice",
                ss."TotalExciseTax",
                fs."FreightCost"
            FROM PurchaseSummary ps
            LEFT JOIN SalesSummary ss
            ON ps."VendorNumber" = ss."VendorNo"
            AND ps."Brand"= ss."Brand"
            LEFT JOIN freight_summary fs
            ON ps."VendorNumber" = fs."VendorNumber"
            ORDER BY ps."TotalPurchaseDollars" DESC''', conn)
    return vendor_sales_summary


def clean_data(df):
    '''this function will clean the data'''
    df['Volume'] = df['Volume'].astype('float')
    df.fillna(0,inplace = True)

    df['VendorName'].str.strip()
    df['Description'].str.strip()

    #creating new columns for better analysis
    df['GrossProfit'] = df['TotalSalesDollars'] - df['TotalPurchaseDollars']
    df['ProfitMargin'] = (df['GrossProfit']/df['TotalSalesDollars'])*100
    df['StockTurnOver'] = df['TotalSalesQuantity']/df['TotalPurchaseQuantity']
    df['SalesPurchaseRatio'] = df['TotalSalesDollars']/df['TotalPurchaseDollars']

    return df

if __name__ == '__main__':
    
    conn = create_engine(f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}")

    logging.info('Creating Vendor Summary Table.....')
    summary_df = create_vendor_summary(conn)
    logging.info(summary_df.head())
    logging.info('Table Creation Completed.....')

    logging.info('Cleaning Data.....')
    clean_df = clean_data(summary_df)
    logging.info(clean_df.head())

    logging.info('Ingesting Data.....')
    ingest_db(clean_df,'vendor_sales_summary',conn)
    logging.info('----------------------------------------Completed------------------------------------------------')
