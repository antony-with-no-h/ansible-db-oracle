# -*- coding: utf-8 -*-

# Copyright: (c) 2021, antony.with.no.h <https://github.com/antony-with-no-h>
# ISC License (see LICENSE or https://www.isc.org/licenses)

from __future__ import (absolute_import, print_function, division)
__metaclass__ = type

DOCUMENTATION = r"""
module: sqlplus
author:
  - antony.with.no.h
short_description: Run queries against database
description:
  - Use SQL*Plus to create a session and run database commands
version_added: 0.1.0
options:
  database_name:
    description:
      - Oracle database name (SID)
    required: true
    type: str
    aliases: ['name', 'sid']
  sql:
    description:
      - A block of SQL to be run
      - Accepts PL/SQL
    required: true
    type: str
  raw:
    description:
      - Errors will be sent to stderr only by default
      - Enable to return the complete traceback from SQL*Plus
    type: bool
    default: no
  ignore_errors:
    description:
      - Module fails on error (ORA-* or SP2-*)
    type: bool
    default: no
  chdir:
    description:
      - Working directory to start SQL*Plus in
notes:
  - SQL*Plus is started with nolog, specify the connection string to connect to the database e.g. C(conn / as sysdba)
  - Single numeric type values (count(*)) will be returned as int/float
  - Host commands are blocked (!/HOST)
"""

EXAMPLES = r"""
- name: SQL*Plus - Add trigger
  antony_with_no_h.oracle.sqlplus:
    database_name: CORCL
    sql: |
      CONN / AS SYSDBA
      CREATE OR REPLACE TRIGGER open_pdbs
        AFTER STARTUP ON DATABASE
      BEGIN
        EXECUTE IMMEDIATE 'ALTER PLUGGABLE DATABASE ALL OPEN';
      END open_pdbs;
      /

- name: SQL*Plus - No filters required
  antony_with_no_h.oracle.sqlplus:
    database_name: CORCL
    sql: |
      SELECT COUNT(*) FROM v$session;
  register: sql_count
  
- name: Integer
  ansible.builtin.assert:
    that: (sql_count.resultset | type_debug) == 'int'
"""

RETURN = r"""
resultset:
  description: Output from SQL*Plus
  returned: always
  type: str
  sample:
"""

import re

import ansible_collections.antony_with_no_h.oracle.plugins.module_utils.common as noh
from ansible.module_utils.basic import AnsibleModule

def main(module):
    """ Oracle SQL*Plus in Ansible """
    
    ignore_errors = module.params["ignore_errors"]
    database_name = module.params["database_name"]
    chdir = module.params["chdir"]
    raw = module.params["raw"]
    sql = module.params["sql"]
    
    try:
        _, environment, _ = noh.oraenv(module, database_name)
    except noh.DatabaseNotFound as fault:
        module_fail = {
            'msg': 'Oracle SQL*Plus for Ansible',
            'rc': 1,
            'stdout': '',
            'stderr': str(fault),
            'resultset': '',
        }
    
    # a simple 'START/@' would circumvent this measure but im not trying to put
    # the kid gloves on anyone just dont think its a good idea to be executing
    # commands on the host from SQL*Plus that is being called from ansible...
    re_illegal = re.compile(r'(^(\!|host).*)', re.MULTILINE|re.IGNORECASE)
    sql_failure = re_illegal.findall(sql)
    
    if sql_failure:
        module_fail = {
            'msg': 'Oracle SQL*Plus for Ansible',
            'rc': 1,
            'stdout': '',
            'stderr': 'Issuing commands to the host is disabled.',
            'resultset': '',
        }
    
        module.fail_json(**module_fail)
    
    rc, stdout, stderr = noh.sqlplus(module, sql, environment, raw, chdir)
    
    module_exit = {
        'msg': 'Oracle SQL*Plus for Ansible',
        'rc': rc,
        'stdout': '',
        'stderr': stderr,
        'resultset': stdout,
    }
    
    if stderr and not ignore_errors:
        module.fail_json(**module_exit)
    else:
        module.exit_json(**module_exit)
    
if __name__ == '__main__':
    
    argument_spec = {
        "database_name": {
            "required": True,
            "type": "str",
            "aliases": ["name", "sid"],
        },
        "ignore_errors": {
            "default": False,
            "type": "bool",
        },
        "raw": {
            "default": False,
            "type": "bool",
        },
        "chdir": {
            "type": "str",
        },
        "sql": {
            "required": True,
            "type": "str",
        },
    }
    
    module = AnsibleModule(
        argument_spec=argument_spec,
    )
    
    main(module)