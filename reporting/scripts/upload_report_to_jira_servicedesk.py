#!/usr/bin/env python3

import sys
import os
from atlassian import ServiceDesk
from datetime import datetime
import argparse
# insert path to be able to load the files in the lib directory
sys.path.insert(0, os.path.dirname(__file__) + "/../lib")
# needed imports from lib folder specified above
from secret import atlassian


# define argument parser
parser = argparse.ArgumentParser(prog = 'upload_report_to_jira_servicedesk.py',
                                 description = 'Uploads weekly and monthly reports to the Jira Service Desk')
parser.add_argument('timespan', type=str, help='W for weekly report, M for monthly report')

# get arguments
ARG = parser.parse_args()

service_desk = ServiceDesk(
    url='https://serco-copernicus.atlassian.net',
    username=atlassian['servicedesk']['username'],
    password=atlassian['servicedesk']['api_token'],
    cloud=True)

# ID for your DHR project
service_desk_id = 00 # put in YOUR id of the DHR project
# ID for the "Report" request type
request_type_id = 154

# set summary according to timespan
if ARG.timespan == 'W':
    # get last week
    week = datetime.now().isocalendar()[1] - 1 if datetime.now().isocalendar()[1] != 1 else 52
    year = datetime.now().year if week != 52 else datetime.now().year - 1

    summary = "{year} Week {week}".format(year=year, week=week)
    filepath = os.path.dirname(__file__) + "/../reports/excel_reports/{year}-w{week:02.0f}_report.xlsx".format(year=year, week=week)
elif ARG.timespan == 'M':
    # get last month
    month = datetime.now().month - 1 if datetime.now().month != 1 else 12
    year = datetime.now().year if month != 12 else datetime.now().year - 1

    summary = "{year} Month {month}".format(year=year, month=month)
    filepath = os.path.dirname(__file__) + "/../reports/excel_reports/{year}-m{month:02.0f}_report.xlsx".format(year=year, month=month)
else:
    print("Wrong timespan given. Exiting.")
    exit(os.EX_USAGE)

if not os.path.exists(filepath):
    print("Report file does not exists. Exiting.")
    exit(79) # 79 == os.EX_NOTFOUND but os.EX_NOTFOUND does not exist on GNU/Linux

# figured out correct formatting of request_info by debugging the atlassian-python-api & atlassian pip packages
# because it doesn't give you specific error messages by default
request_info = {
    "summary": summary,
    "customfield_10138": { "value": "Routine" }
}

# check if report was already uploaded
requests = service_desk.get_my_customer_requests()
ticket_names = []
for request in requests:
    ticket_names.append(request['requestFieldValues'][0]['value'])

if summary in ticket_names:
    print("Ticket already exists. Exiting")
    exit(os.EX_CANTCREAT)

# first upload attachment to see if there are any errors before creating the report ticket
temp_attachment_id = service_desk.attach_temporary_file(service_desk_id, filepath)
# create the report ticket
request = service_desk.create_customer_request(service_desk_id, request_type_id, request_info)
# attach the already uploaded file to the report
service_desk.add_attachment(request["issueKey"], temp_attachment_id)