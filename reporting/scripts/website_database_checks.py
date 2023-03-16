#!/usr/bin/env python3

import sys
import os
# insert path to be able to load the files in the lib directory
sys.path.insert(0, os.path.dirname(__file__) + "/../lib")

import requests
from datetime import datetime
from requests.auth import HTTPBasicAuth
import psycopg2

from secret import web_secrets, db_secrets

def database_check():
    try:
        # connect to our frontend to get latest available product
        conn = psycopg2.connect(host = db_secrets['FE']['host'],
                                database = db_secrets['FE']['database'],
                                user = db_secrets['FE']['user'],
                                password = db_secrets['FE']['password'],
                                port = "5432")

        # get product info from our frontend
        query = "SELECT uuid, created FROM products ORDER BY created DESC LIMIT 1"
        cur = conn.cursor()
        cur.execute(query)
        info = cur.fetchone()
        conn.close()

        return info[0], True, ""
    except Exception as e:
        return "", False, str(e)

def website_check(uuid):
    try:
        host = "YOUR_FRONTEND_FQDN"
        url = str.format("https://" + host + "/dhus/odata/v1/Products('{uuid}')", uuid=uuid)
        
        response = requests.get(url=url, auth=HTTPBasicAuth(username=web_secrets[host]['user'], password=web_secrets[host]['password']))
        
        if response.status_code == 200 and uuid in response.text:
            return True, ""
        else:
            return False, response.text
    except:
        return False, "Web request couldn't be made."

# check availabilities and therefore get all necessary variables 
uuid, database_availability, error_db = database_check()
website_availability, error_web = website_check(uuid)

# combine db and web errors if necessary
if error_db or error_web: error = error_db + "|" + error_web
else: error = ""

# connect to log db
conn = psycopg2.connect(host = db_secrets['LOGDB']['host'],
                        database = db_secrets['LOGDB']['database'],
                        user = db_secrets['LOGDB']['user'],
                        password = db_secrets['LOGDB']['password'],
                        port = "5432")

cur = conn.cursor()
#cur.execute("DROP TABLE IF EXISTS availability_checks")
cur.execute("CREATE TABLE IF NOT EXISTS availability_checks(uuid CHAR(36) PRIMARY KEY NOT NULL,\
                                                            website_available BOOLEAN NOT NULL,\
                                                            database_available BOOLEAN NOT NULL,\
                                                            timestamp TIMESTAMP,\
                                                            error TEXT)")
conn.commit()

# throws error if uuid already exists. we can safely ignore that case
try:
    cur.execute(str.format("INSERT INTO availability_checks (uuid, website_available, database_available, timestamp, error) \
                            VALUES ('{uuid}', '{website_available}', {database_available}, '{timestamp}', '{error}')",
                            uuid=uuid,
                            website_available=website_availability,
                            database_available=database_availability,
                            timestamp=datetime.now(),
                            error=error))
    conn.commit()
except psycopg2.errors.UniqueViolation: pass

conn.close()