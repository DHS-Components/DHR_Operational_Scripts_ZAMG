# Overview

## setup

The setup of the DHuS software stack is automated via Ansible and can be found in the setup/ folder. All customizable options can be found in the playbooks in setup/roles/ansible-dhus/vars.

### How to

1. In the ansible-dhus role change all uppercase variable values according to your needs.  
   You may also removed entries from the products list as necessary, but keep the structure of each product!  
   We suggest that you put the passwords encrypted via vault into the YAML files.  
   For example, if you want to add an encrypted variable named **admin_password**, you can do this via the following command:  
   ```ansible-vault encrypt_string 'VERY_LONG_AND_SECURE_PASSWORD' --name 'admin_password' --vault-password-file PATH_TO_VAULT_PASSWORD_FILE```

2. Once everything is configured, run the setup.yml playbook on the server/VM of your choice via the following command:  
   ```ansible-playbook setup.yml --vault-password-file PATH_TO_VAULT_PASSWORD_FILE```  
    The installation process should be finished after a few minutes without any errors.

3. You are now able to start and enable the dhus software via systemd:  
    ```systemctl enable dhus && systemctl start dhus```

## reporting

This takes care of creating the reporting documents. It is done via python3 scripts, some cronjobs and a postgresql docker container.

### How to

1. Set your postgres user password in the ```env``` file. Also populate the ```lib/secrets.py``` file with your configuration/passwords.  
   Also set your ```service_desk_id``` in the ```upload_report_to_jira_servicedesk.py``` file.

2. Start up the local postgresql docker container. This is used to save the logging data.  
   Start via: ```docker-compose up -d```

3. Create cronjobs for gathering logs. Those two cronjobs gather checks for database and website and the time difference of your products to the currently configured backends where you sync your products from.  
   Example cronjobs:
   ```bash
   # get product data every 10 mins
   */10 * * * * /PATH_TO_DIR/scripts/products_timediff.py --write-db >> /var/logs/timediff.log 2>&1
   */10 * * * * /PATH_TO_DIR/scripts/website_database_checks.py >> /var/logs/availability_checks.log 2>&1
   ```

4. Create cronjobs for creating the weekly/monthly reports.  
   For example:
   ```bash
   ## CREATION PDF REPORTS
   ## overwrite log file as the pdflatex command creates a lot of output
   # create monthly pdf report
   10 5 1 * * /PATH_TO_DIR/scripts/create_pdf_report.py M >> /var/logs/pdf_reports.log 2>&1
   # create weekly pdf report
   5 5 * * 1 /PATH_TO_DIR/scripts/create_pdf_report.py W > /var/logs/pdf_reports.log 2>&1
   
   ## CREATION EXCEL REPORTS
   # create monthly excel report
   5 5 1 * * /PATH_TO_DIR/scripts/create_excel_report.py M >> /var/logs/excel_report.log 2>&1
   # create weekly excel report
   10 5 * * 1 /PATH_TO_DIR/scripts/create_excel_report.py W >> /var/logs/excel_report.log 2>&1
   ```

5. Create a cronjob for uploading the weekly/monthly excel file upload to Jira ServiceDesk.
   ```bash
   ## UPLOAD EXCEL REPORTS
   # upload monthly excel report to Jira Service Desk
   30 6 1 * * /PATH_TO_DIR/scripts/upload_report_to_jira_servicedesk.py M >> /var/logs/upload-jira.log 2>&1
   # upload weekly excel report to Jira Service Desk
   20 6 * * 1 /PATH_TO_DIR/scripts/upload_report_to_jira_servicedesk.py W >> /var/logs/upload-jira.log 2>&1
   ```