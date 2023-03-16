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
