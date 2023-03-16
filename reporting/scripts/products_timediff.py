#!/usr/bin/env python3

import sys
import os
# insert path to be able to load the files in the lib directory
sys.path.insert(0, os.path.dirname(__file__) + "/../lib")

import re
import argparse
import requests
from requests.auth import HTTPBasicAuth
from dateutil import parser as dateparse
from datetime import datetime
import psycopg2

# needed imports from lib folder specified above
from product import products
from secret import web_secrets, db_secrets
from helper import strfdelta


def get_latest_product_info(product_name):
    # connect to our frontend to get latest available product
    conn = psycopg2.connect(host = db_secrets['FE']['host'],
                            database = db_secrets['FE']['database'],
                            user = db_secrets['FE']['user'],
                            password = db_secrets['FE']['password'],
                            port = "5432")

    # get product info from our frontend
    query = "SELECT uuid, created, origin FROM products WHERE"
    for identifier in products[product_name]["names"]:
        # make sure to use a specific identifier and NOT the general ones (e.g. 'S1A_')
        if len(identifier) > 4:
            identifier = identifier.replace("..", "%")
            if not query.endswith("WHERE"): query += " OR"
            query += str.format(" identifier LIKE '%{identifier}%'", identifier=identifier)
    query += " ORDER BY created DESC LIMIT 1"

    cur = conn.cursor()
    cur.execute(query)
    info = cur.fetchone()
    result_frontend = {'uuid': info[0], 'created': info[1], 'origin': info[2]}
    conn.close()

    # use info from frontend to get correct remote backend from our backend
    conn = psycopg2.connect(host = db_secrets[product_name]['host'],
                            database = db_secrets[product_name]['database'],
                            user = db_secrets[product_name]['user'],
                            password = db_secrets[product_name]['password'],
                            port = "5432")
    cur = conn.cursor()
    cur.execute(str.format("SELECT uuid, created, origin FROM products WHERE uuid = '{uuid}' ORDER BY created DESC LIMIT 1", uuid=result_frontend['uuid']))
    info = cur.fetchone()
    result_backend = {'uuid': info[0], 'created': info[1], 'origin': info[2]}
    conn.close()

    # now get remote backend creation time
    host_remote = result_backend['origin'].split('/')[2]
    response = requests.get(url=str.replace(result_backend['origin'], "$value", "CreationDate"),
                            auth=HTTPBasicAuth(username=web_secrets[host_remote]['user'], password=web_secrets[host_remote]['password']))

    # and finally gather all info into an data object to return
    if response.status_code == 200:
        remote_time = re.search(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,6})?", response.text).group(0)
        
        return { 'uuid': result_frontend['uuid'],
                 'product_name': product_name,
                 'time_diff': result_frontend['created'] - dateparse.parse(remote_time),
                 'remote_backend': result_backend['origin'].split('/')[2],
                 'timestamp': datetime.now(),
                 'error': '' }
    else:
        return { 'uuid': result_frontend['uuid'],
                 'product_name': product_name,
                 'time_diff': '',
                 'remote_backend': result_backend['origin'].split('/')[2],
                 'timestamp': datetime.now(),
                 'error': 'remote backend not available' }

def write_time_diff_to_db():
    conn = psycopg2.connect(host = db_secrets['LOGDB']['host'],
                            database = db_secrets['LOGDB']['database'],
                            user = db_secrets['LOGDB']['user'],
                            password = db_secrets['LOGDB']['password'],
                            port = "5432")

    cur = conn.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS time_diff(uuid CHAR(36) PRIMARY KEY NOT NULL,\
                                                    product_name VARCHAR(8) NOT NULL,\
                                                    time_diff TIME,\
                                                    remote_backend VARCHAR(64),\
                                                    timestamp TIMESTAMP,\
                                                    error TEXT)")
    conn.commit()

    for product_name in products.keys():
        product_results = get_latest_product_info(product_name)
        
        # if there is no new product we get an exception when committing the same uuid again
        # therefore we just ignore it
        try:
            if product_results['time_diff']:
                query = "INSERT INTO time_diff (uuid, product_name, time_diff, remote_backend, timestamp, error) \
                        VALUES ('{uuid}', '{product_name}', '{time_diff}', '{remote_backend}', '{timestamp}', '{error}')"
            else:
                query = "INSERT INTO time_diff (uuid, product_name, time_diff, remote_backend, timestamp, error) \
                        VALUES ('{uuid}', '{product_name}', {time_diff}, '{remote_backend}', '{timestamp}', '{error}')"
            
            cur.execute(str.format(query,
                                uuid=product_results['uuid'],
                                product_name=product_results['product_name'],
                                time_diff=product_results['time_diff'] if product_results['time_diff'] else "NULL",
                                remote_backend=product_results['remote_backend'],
                                timestamp=product_results['timestamp'],
                                error=product_results['error']))
        except Exception as e: pass

        conn.commit()
        
    conn.close()

parser = argparse.ArgumentParser(description=('Checks the given product of all DHRs'))
parser.add_argument('-w', '--write-db',
                        help="Results will be written to the log database.", action="store_true")
parser.add_argument('-l', '--latest',
                        help="Get latest time difference of all products.", action="store_true")

args = parser.parse_args()

# write to db
if args.write_db:
    write_time_diff_to_db()
# print out latest timediff of products
if args.latest:
    for product_name in products.keys():
        product_results = get_latest_product_info(product_name)
        print("{0:8s} {1:9s} {2}".format(product_name, strfdelta(product_results['time_diff']), product_results['remote_backend']))
# print out help if no arguments were given
if len(sys.argv) == 1:
    parser.print_help()