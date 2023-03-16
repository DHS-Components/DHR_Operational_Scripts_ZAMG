#!/usr/bin/env python3

import sys
import os
# insert path to be able to load the files in the lib directory
sys.path.insert(0, os.path.dirname(__file__) + "/../lib")

from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth
import argparse
 
# importing
from product import products
from secret import web_secrets

parser = argparse.ArgumentParser(description=('Checks the given product of all DHRs'))
parser.add_argument('product', type=str,
                        help="Product name to check. [S1, S1-SLC, S2A-L1C, S2B-L1C, S2A-L2A, S2B-L2A, S3, S5, All]")
parser.add_argument('-d', '--date', type=str,
                        help="Date to check. Format: YYYY-MM-DD", required=False)
args = parser.parse_args()

# set date to today or to given argument
if args.date: today = args.date
else: today = datetime.today().strftime('%Y-%m-%d')

# loop through all products for each domain
for product_name, product_info in products.items():
    for domain, login in web_secrets.items():
        # need to set auth parameters for get request
        auth = HTTPBasicAuth(login["user"], login["password"])

        # continue loop if not the specified product
        if args.product not in ["All", product_name]: continue

        # get data from odata endpoint
        url = "https://" + domain + "/dhus/odata/v1/Products/$count?$filter=" + product_info["filter"]
        url += " and IngestionDate gt datetime'{today}T00:00:00.000' and IngestionDate lt datetime'{today}T23:59:59.999'".format(today=today)
        response = requests.get(url=url, auth=auth, allow_redirects=True)

        # check if /dhus path was correct otherwise leave it out and try again
        if response.status_code == 404:
            url = "https://" + domain + "/odata/v1/Products/$count?$filter=" + product_info["filter"]
            url += " and IngestionDate gt datetime'{today}T00:00:00.000' and IngestionDate lt datetime'{today}T23:59:59.999'".format(today=today)
            response = requests.get(url=url, auth=auth, allow_redirects=True)

        # in case of invalid output/error or 0 counts for product
        # continue with next product
        if len(response.text) > 10 or (response.text.isdigit() and int(response.text) == 0): continue

        # print out data
        print("{product:7s} {count:5d} {domain}".format(domain=domain, product=product_name, count=int(response.text)))
