# ansible-dhus

This role is used to install **DHuS** and the releases can be accessed under [Releases](https://github.com/SentinelDataHub/dhus-distribution/releases). Moreover, it is designed to configure a new **DHuS** server. It installs **PostgreSQL** as Database, as well as **Apache2** as local proxy, creates all the necessary directories and configures the whole system. When the role has finished, **DHuS** should be ready to use.

## Requirements

* Debian/Ubuntu derived distribution (with systemd)

## Dependencies

* Ansible
* Installs dependencies for DHuS automatically

## Role Variables

### product

Needs to be set before running the role. It can take one of the following values: "s1", "s2a-l1c", "s2b-l1c", "s2-l2a", "s3", "s5", "dhr" & "dhs".  
Those variables point to the product list in the vars/dhus.yml file and can be customized as needed. The setup.yml also needs to be adapted to reflect the configuration.

## Example Playbook

```yaml
---
- name: Set up DHR
  hosts: localhost
  vars_prompt:
    - name: product
      prompt: Which product would you like to install? Choose one of [s1, s2a-l1c, s2b-l1c, s2-l2a, s3, s5, dhr, dhs]
      private: no
  roles:
    - ansible-dhus
```

## ToDo

* use Jinja loop in dhus.xml.j2 template (currently a workaround in tasks/dhus.yml with looping)

## Author Information

* Simon Kropf (simon.kropf@geosphere.at)
* Stefan Buchberger (stefan.buchberger@geosphere.at)