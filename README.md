# Oracle collection for Ansible

[![License: ISC](https://img.shields.io/badge/License-ISC-blue.svg)](https://opensource.org/licenses/ISC)

Primarily a collection of modules for use with an Oracle database(s), written with 0 dependencies in mind.

## Features

- Zero dependencies  
  *Because sometimes the distro Python is all you've got*
- Python 2 Support  
  *Ansible 2.11 still supports 2.6 so this will too*
- Documentation  
  *What!? - [docs/source](docs/source)* [^1]


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