# Oracle collection for Ansible

[![License: ISC](https://img.shields.io/badge/License-ISC-blue.svg)](https://opensource.org/licenses/ISC)

Primarily a collection of modules for use with an Oracle database(s), written with 0 dependencies in mind.

## Design Principles

- **Keep support for Python 2.6**  
  Enterprise distros are never cutting edge and companies that buy 'Extended Life Cycle Support' mean, just like me, you may have some pretty old versions of python hanging around.
  
- **Keep modules to a minimum**  
  Since a lot of modules are going to be a wrapper around `subprocess()` I prefer to use `ansible.builtin.command` or `ansible.builtin.shell` and provide ways to **enhance** those modules for Oracle usage. 

- **No third party libraries**  
  Limits imposed either by software (no pip), device (firewalls), team (sysadmin says no) or policy (security says no). Or anything else. Means not everyone gets to install `cx_Oracle` or anything they please from pip.

- **Flexibility**  
  It is difficult to know every use case 'any other' person may have in their organisation. I wrote this collection with flexibility in mind, so you can make it fit the way you do things rather than how I do or how I think you should do it.
  
## Features

- **Tables as dictionaries**
  Intended for 'DBA' views like `v$database`, but not limited to, return a dictionary object (yaml: `mapping`).
  
- **Tables as lists**
  Get nested or unnested list objects (yaml: `sequence`)

- **Parse the Central Inventory**
  Make not installing software twice (or at least attempting to) easy by checking the central inventory first.
  
- **Documentation**  
  - *What!? - [docs/source](docs/source)* [^1]
  - https://ansible-db-oracle.readthedocs.io/en/latest/


## Installation

Install directly from git

```bash
ansible-galaxy collection install git+git@github.com:antony-with-no-h/ansible-db-oracle.git
```

## Usage

I make use of inventory aliasing [magic variables](https://docs.ansible.com/ansible/latest/reference_appendices/special_variables.html), an example of my inventory:

```yaml
all:
  children:
    loopback:
      hosts:
        localhost:
          ansible_connection: local
    databases:
      hosts:
        ORCL:
          ansible_host: 13.58.87.28
```

And an example playbook

```yaml
- hosts: databases
  
  vars:
    oracle_home: /u01/app/oracle/product/19.0.0/dbhome_1
    oracle_base: /u01/app/oracle
  
  tasks:
  - name: Oracle inventory
    antony_with_no_h.oracle.inventory:
    register: ora_inventory
  
  - name: Install database software
    ansible.builtin.shell: >-
      runInstaller 
        -responseFile "{{ oracle_home }}/install/response/db_install.rsp"
        -waitforcompletion
        -silent
    environment:
      PATH: "{{ oracle_home }}:/usr/local/bin:/usr/bin:/bin"
    register: sw_db_install
    when: oracle_home not in ora_inventory.resultset
    failed_when: "'[FATAL]' in sw_db_install.stdout"
```

## License

ISC

[^1]: https://pypi.org/project/ansible-doc-extractor/