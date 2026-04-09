#!/usr/bin/env python
"""
Script to create a PostgreSQL database and ingest UNGDC diplomatic speeches.
"""
import psycopg2
import pandas as pd
from psycopg2 import sql

# Database configuration
DB_NAME = "ungdc_db"
DB_USER = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"

# CSV file path
CSV_FILE = "data/ungdc_1946-2022.csv"

def create_database():
    """Create the database if it doesn't exist."""
    try:
        # Connect to the default postgres database
        conn = psycopg2.connect(
            dbname="postgres",
            user=DB_USER,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Check if the database already exists
        cursor.execute(sql.SQL("SELECT 1 FROM pg_database WHERE datname = {};").format(
            sql.Literal(DB_NAME)))
        exists = cursor.fetchone()

        if not exists:
            print(f"Creating database '{DB_NAME}'...")
            cursor.execute(sql.SQL("CREATE DATABASE {};").format(
                sql.Identifier(DB_NAME)))
            print(f"Database '{DB_NAME}' created successfully.")
        else:
            print(f"Database '{DB_NAME}' already exists.")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error creating database: {e}")
        raise

def create_tables():
    """Create the documents table."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()

        # Create documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id VARCHAR(50) PRIMARY KEY,
                iso VARCHAR(10),
                session INTEGER,
                year INTEGER,
                text TEXT,
                un_region VARCHAR(50)
            );
        """
        )
        print("Table 'documents' created successfully.")

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error creating tables: {e}")
        raise

def ingest_data():
    """Ingest data from CSV into the documents table."""
    try:
        # Read CSV file
        df = pd.read_csv(CSV_FILE)
        print(f"Read {len(df)} records from {CSV_FILE}.")

        # Connect to the database
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()

        # Insert data into documents table
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO documents (doc_id, iso, session, year, text, un_region)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (doc_id) DO NOTHING;
            """, (row['doc_id'], row['iso'], row['session'], row['year'], row['text'], row['UN_REGION']))

        conn.commit()
        print(f"Ingested {len(df)} records into 'documents' table.")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error ingesting data: {e}")
        raise

def main():
    """Main function to create database, tables, and ingest data."""
    try:
        print("Starting database setup...")
        create_database()
        create_tables()
        ingest_data()
        print("Database setup completed successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()