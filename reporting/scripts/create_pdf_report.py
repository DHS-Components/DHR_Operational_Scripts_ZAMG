#!/usr/bin/env python3

import sys
import os
# insert path to be able to load the files in the lib directory
sys.path.insert(0, os.path.dirname(__file__) + "/../lib")

# for easier date handling
import calendar, time
from datetime import timedelta, date, datetime
# to get and change path to current directory
from os import chdir, path
# for running pdflatex shell command
from subprocess import check_call
# to access postgresql database
import psycopg2
# for nice helptext and argument parsing
import argparse

# in python >3.6 dicts are ordered
TIMEDIFF_COSTMOD_TABLE = {}
TIMEDIFF_COSTMOD_TABLE[14400] = 100
TIMEDIFF_COSTMOD_TABLE[43200] = 95
TIMEDIFF_COSTMOD_TABLE[259200] = 85
PERCENTAGE_COSTMOD_TABLE = {}
PERCENTAGE_COSTMOD_TABLE[100] = [98, 100]
PERCENTAGE_COSTMOD_TABLE[97.5] = [95, 98]
PERCENTAGE_COSTMOD_TABLE[95] = [85, 95]
PERCENTAGE_COSTMOD_TABLE[90] = [50, 85]
PERCENTAGE_COSTMOD_TABLE[85] = [0, 50]

from product import products
from secret import db_secrets
from helper import strfdelta

# returns necessary data (avg time diff for each product & count of availability checks for website & database)
# to use for replacing the placeholder in the report.tex template
def get_report_data(start_date, end_date):
    time_diffs = {}
    
    # connect to postgresql database where all the data is stored in two tables,
    # namely time_diff and availability_checks
    conn = psycopg2.connect(host = db_secrets['LOGDB']['host'],
                            database = db_secrets['LOGDB']['database'],
                            user = db_secrets['LOGDB']['user'],
                            password = db_secrets['LOGDB']['password'],
                            port = "5432")

    cur = conn.cursor()

    # get time difference for products
    template_query_avg_time = "SELECT AVG(time_diff) from time_diff\
                               WHERE product_name = '{product_name}'\
                               AND timestamp BETWEEN '{start_date}' AND '{end_date}';"

    # get avg time diff for each product as defined in the product_definitions.py file
    for product_name in products.keys():
        query_avg_time = str.format(template_query_avg_time, product_name=product_name, start_date=start_date, end_date=end_date)

        cur.execute(query_avg_time)
        avg_time_diff = cur.fetchone()[0]

        time_diffs[product_name] = { 'time_diff': avg_time_diff,
                                     'percentage': [v for k, v in TIMEDIFF_COSTMOD_TABLE.items() if avg_time_diff.seconds < k][0] }
    # get the overall statistics of all products
    overall_avg_time_diff = sum([v['time_diff'] for _, v in time_diffs.items()], timedelta()) / len(time_diffs)
    time_diffs['overall'] = { 'time_diff': overall_avg_time_diff,
                              'percentage': sum([v['percentage'] for _, v in time_diffs.items()]) / len(time_diffs),
                              'cost_modulation': [v for k, v in TIMEDIFF_COSTMOD_TABLE.items() if overall_avg_time_diff.seconds < k][0] }


    # get availability checks (successful and failed) for website and database = 4 queries
    # either have one query and do logic in python or
    # do several queries and outsource logic to SQL (as done here)
    query_website_checks_successful = str.format("SELECT count(uuid) from availability_checks\
                                                  WHERE timestamp BETWEEN '{start_date}' AND '{end_date}'\
                                                  AND website_available = 't';", start_date=start_date, end_date=end_date)
    cur.execute(query_website_checks_successful)
    website_checks_successful = cur.fetchone()[0]

    query_website_checks_failed = str.format("SELECT count(uuid) from availability_checks\
                                              WHERE timestamp BETWEEN '{start_date}' AND '{end_date}'\
                                              AND website_available = 'f';", start_date=start_date, end_date=end_date)
    cur.execute(query_website_checks_failed)
    website_checks_failed = cur.fetchone()[0]

    query_database_checks_successful = str.format("SELECT count(uuid) from availability_checks\
                                        WHERE timestamp BETWEEN '{start_date}' AND '{end_date}'\
                                        AND database_available = 't';", start_date=start_date, end_date=end_date)
    cur.execute(query_database_checks_successful)
    database_checks_successful = cur.fetchone()[0]

    query_database_checks_failed = str.format("SELECT count(uuid) from availability_checks\
                                    WHERE timestamp BETWEEN '{start_date}' AND '{end_date}'\
                                    AND database_available = 'f';", start_date=start_date, end_date=end_date)
    cur.execute(query_database_checks_failed)
    database_checks_failed = cur.fetchone()[0]

    conn.close()

    # put in availability check data in dict
    website_checks_percentage = website_checks_successful / (website_checks_successful + website_checks_failed) * 100
    database_checks_percentage = database_checks_successful / (database_checks_successful + database_checks_failed) * 100
    overall_percentage = (website_checks_percentage + database_checks_percentage) / 2

    availability_checks = { 'website_checks_total': website_checks_successful + website_checks_failed,
                            'website_checks_successful': website_checks_successful,
                            'website_checks_failed': website_checks_failed,
                            'website_checks_percentage': website_checks_percentage,
                            'database_checks_total': database_checks_successful + database_checks_failed,
                            'database_checks_successful': database_checks_successful,
                            'database_checks_failed': database_checks_failed,
                            'database_checks_percentage': database_checks_percentage,
                            'overall_percentage': overall_percentage,
                            'overall_cost_modulation': [k for k, v  in PERCENTAGE_COSTMOD_TABLE.items() if v[0] < overall_percentage <= v[1]][0] }

    return time_diffs, availability_checks

# uses the data from the get_report_data function and writes it into a string which
# holds the content of the tex file and returns it
def get_report_content(time_diffs, availability_checks):
    # get content of the report template file
    report_content = open('report.tex', 'r').read()

    # calculate overall performance stats
    overall_performance = (availability_checks['overall_percentage'] + time_diffs['overall']['percentage']) / 2
    overall_cost_modulation = [k for k, v  in PERCENTAGE_COSTMOD_TABLE.items() if v[0] < overall_performance <= v[1]][0]

    # overall stats
    report_content = report_content.replace("placeholder_kpi1_percentage", str.format("{0:.2f}", availability_checks['overall_percentage']))
    report_content = report_content.replace("placeholder_kpi2_percentage", str.format("{0:.2f}", time_diffs['overall']['percentage']))
    report_content = report_content.replace("placeholder_overall_performance", str.format("{0:.2f}", overall_performance))
    report_content = report_content.replace("placeholder_overall_cost_modulation", str.format("{0:.2f}", overall_cost_modulation))

    # kpi 1 stats
    report_content = report_content.replace("placeholder_website_checks_successful", str(availability_checks['website_checks_successful']))
    report_content = report_content.replace("placeholder_website_checks_percentage", str.format("{0:.2f}", availability_checks['website_checks_percentage']))
    report_content = report_content.replace("placeholder_website_checks", str(availability_checks['website_checks_total']))

    report_content = report_content.replace("placeholder_database_checks_successful", str(availability_checks['database_checks_successful']))
    report_content = report_content.replace("placeholder_database_checks_percentage", str.format("{0:.2f}", availability_checks['database_checks_percentage']))
    report_content = report_content.replace("placeholder_database_checks", str(availability_checks['database_checks_total']))

    report_content = report_content.replace("placeholder_kpi1_percentage", str.format("{0:.2f}", availability_checks['overall_percentage']))
    report_content = report_content.replace("placeholder_kpi1_cost_modulation", str.format("{0:.2f}", availability_checks['overall_cost_modulation']))

    # kpi 2 stats
    report_content = report_content.replace("placeholder_s1_time_diff", strfdelta(time_diffs['S1']['time_diff']))
    report_content = report_content.replace("placeholder_s1_percentage", str(time_diffs['S1']['percentage']))
    report_content = report_content.replace("placeholder_s1slc_time_diff", strfdelta(time_diffs['S1-SLC']['time_diff']))
    report_content = report_content.replace("placeholder_s1slc_percentage", str(time_diffs['S1-SLC']['percentage']))
    report_content = report_content.replace("placeholder_s2al1c_time_diff", strfdelta(time_diffs['S2A-L1C']['time_diff']))
    report_content = report_content.replace("placeholder_s2al1c_percentage", str(time_diffs['S2A-L1C']['percentage']))
    report_content = report_content.replace("placeholder_s2bl1c_time_diff", strfdelta(time_diffs['S2B-L1C']['time_diff']))
    report_content = report_content.replace("placeholder_s2bl1c_percentage", str(time_diffs['S2B-L1C']['percentage']))
    report_content = report_content.replace("placeholder_s2al2a_time_diff", strfdelta(time_diffs['S2A-L2A']['time_diff']))
    report_content = report_content.replace("placeholder_s2al2a_percentage", str(time_diffs['S2A-L2A']['percentage']))
    report_content = report_content.replace("placeholder_s2bl2a_time_diff", strfdelta(time_diffs['S2B-L2A']['time_diff']))
    report_content = report_content.replace("placeholder_s2bl2a_percentage", str(time_diffs['S2B-L2A']['percentage']))
    report_content = report_content.replace("placeholder_s3_time_diff", strfdelta(time_diffs['S3']['time_diff']))
    report_content = report_content.replace("placeholder_s3_percentage", str(time_diffs['S3']['percentage']))
    report_content = report_content.replace("placeholder_s5_time_diff", strfdelta(time_diffs['S5']['time_diff']))
    report_content = report_content.replace("placeholder_s5_percentage", str(time_diffs['S5']['percentage']))

    # this is different for each DHR as the data for each product gets pulled from other DHRs
    report_content = report_content.replace("placeholder_colhub1_time_diff", strfdelta(time_diffs['S2A-L1C']['time_diff']))
    report_content = report_content.replace("placeholder_colhub2_time_diff", strfdelta(time_diffs['S2B-L2A']['time_diff']))
    report_content = report_content.replace("placeholder_colhub3_time_diff", strfdelta(time_diffs['S3']['time_diff']))
    report_content = report_content.replace("placeholder_grnet_time_diff", strfdelta((time_diffs['S2B-L1C']['time_diff'] + time_diffs['S5']['time_diff']) / 2))
    report_content = report_content.replace("placeholder_cesnet_time_diff", strfdelta(time_diffs['S2A-L2A']['time_diff']))
    report_content = report_content.replace("placeholder_metno_time_diff", strfdelta((time_diffs['S1']['time_diff'] + time_diffs['S1-SLC']['time_diff']) / 2))

    report_content = report_content.replace("placeholder_average_percentage", str.format("{0:.2f}", time_diffs['overall']['percentage']))

    report_content = report_content.replace("placeholder_kpi2_time_diff", strfdelta(time_diffs['overall']['time_diff']))
    report_content = report_content.replace("placeholder_kpi2_cost_modulation", str.format("{0:.2f}", time_diffs['overall']['cost_modulation']))

    return report_content


# define argument parser
parser = argparse.ArgumentParser(prog = 'create_pdf_report.py',
                                 description = 'Creates a monthly or weekly report from the postgres database.')
parser.add_argument('timespan', type=str, help='W for weekly report, M for monthly report')

# get arguments
ARG = parser.parse_args()

# generate dates for last week
if ARG.timespan == 'W':
    # get last week
    week = datetime.now().isocalendar()[1] - 1 if datetime.now().isocalendar()[1] != 1 else 52
    year = datetime.now().year if week != 52 else datetime.now().year - 1

    start_date = time.asctime(time.strptime('%d %d 1' % (year, week), '%Y %W %w'))
    start_date = datetime.strptime(start_date, '%a %b %d %H:%M:%S %Y')
    # SQL's BETWEEN is inclusive on start_date but exclusive on end_date - therefore adding +1 day to end_date (and +6 for the week)
    end_date = start_date + timedelta(days=7)

    # set report filename accordingly
    report_filename = "{year}-w{week:02.0f}_report".format(year=year, week=week)
# generate date for last month
elif ARG.timespan == 'M':
    # get last month
    month = datetime.now().month - 1 if datetime.now().month != 1 else 12
    year = datetime.now().year if month != 12 else datetime.now().year - 1

    start_date = datetime.strptime("{0}-{1}-01".format(year, month), "%Y-%m-%d")
    # SQL's BETWEEN is inclusive on start_date but exclusive on end_date - therefore adding +1 day to end_date
    end_date = datetime.strptime("{0}-{1}-{2}".format(year, month, calendar.monthrange(year, month)[1]), "%Y-%m-%d") + timedelta(days=1)

    # set report filename accordingly
    report_filename = "{year}-m{month:02.0f}_report".format(year=year, month=month)
else:
    print("Invalid timespan given. Exiting.")
    exit()


# change to report directory
cur_dir = path.dirname(__file__)
chdir(cur_dir + "/../reports/")

# get necessary data from database
time_diffs, availability_checks = get_report_data(start_date, end_date)

report_file_tex = open(report_filename + ".tex", 'w')
report_file_tex.write(get_report_content(time_diffs, availability_checks))
report_file_tex.close()

# convert to pdf and remove log files
check_call(['pdflatex', report_filename + ".tex"])
check_call(['rm', report_filename + ".tex", report_filename + ".aux", report_filename + ".log"])
if not os.path.exists("pdf_reports/" + report_filename + ".pdf"):
    check_call(['mv', report_filename + ".pdf", "pdf_reports/"])
else:
    print("Report already exists - moving to pdf_reports/" + report_filename + "-new.pdf")
    check_call(['mv', report_filename + ".pdf", "pdf_reports/" + report_filename + "-new.pdf"])