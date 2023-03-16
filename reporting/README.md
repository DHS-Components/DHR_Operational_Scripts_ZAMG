# DHR

This structure should contain all necessary files to be able to run the reporting of the DataHub Relay infrastructure.

## Dependencies

* docker-compose
* python >3.6
* pip packages
  * atlassian-python-api
  * openpyxl
  * psycopg2

## Scripts

* For creating logging metrics
  ```
  products_timediff.py
  website_database_checks.py
  ```
* For creating pdf/excel reports
  ```
  create_excel_report.py
  create_pdf_report.py 
  ```
* For uploading reports to Jira ServiceDesk
  ```
  upload_report_to_jira_servicedesk.py
  ```
* For checking product counts
  ```
  products_counts.py
  ```