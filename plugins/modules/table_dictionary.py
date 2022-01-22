# -*- coding: utf-8 -*-

# Copyright: (c) 2021, antony.with.no.h <https://github.com/antony-with-no-h>
# ISC License (see LICENSE or https://www.isc.org/licenses)

from __future__ import (absolute_import, print_function, division)
__metaclass__ = type

DOCUMENTATION = r"""
module: table_dictionary
author:
  - antony.with.no.h
short_description: Table as a dictionary
description:
  - Returns a nested or unnested collection of key value pairs
version_added: 0.1.0
options:
  database_name:
    description:
      - Name of the database to connect to
    required: true
    type: str
    aliases: ['name', 'sid']
  table_name:
    description:
      - The database table to be queried
    required: true
    type: str
    aliases: ['table']
  column_as_key:
    description:
      - Use column name as dictionary key
      - Specifying this parameter will return a nested dictionary
    required: false
    type: str
notes:
"""

EXAMPLES = r"""
- name: v$database
  antony_with_no_h.oracle.table_dictionary:
    database_name: ORCL
    table: v$database
  register: v_database

- ansible.builtin.assert:
    that: v_database.resultset.LOG_MODE == 'ARCHIVELOG'

- name: v$parameter - nested dictionary
  antony_with_no_h.oracle.table_dictionary:
    database_name: ORCL
    table: v$parameter
    column_as_key: name
  register: v_parameter
  
- antony_with_no_h.oracle.sqlplus:
    database_name: ORCL
    sql: |
      ALTER SYSTEM SET processes = 400 SCOPE=spfile;
    when:
      - v_parameter.resultset.processes.DISPLAY_VALUE < 400
"""

RETURN = r"""
resultset:
  description: Table data as a dictionary object
  returned: success
  type: dict
  sample:
"""

import platform

python_tuple = tuple(map(int, platform.python_version_tuple()))
if python_tuple <= (2, 7, 18):
    from itertools import izip as zip

import ansible_collections.antony_with_no_h.oracle.plugins.module_utils.common as noh
from ansible.module_utils.basic import AnsibleModule

def main(module):
    
    try:
        column_as_key = module.params['column_as_key'].upper()
    except AttributeError:
        column_as_key = module.params['column_as_key']
        
    database_name = module.params['database_name'].upper()
    table_name = module.params['table_name']
    
    module_fail = {
        'msg': 'An error has occured',
        'rc': 1,
        'stdout': '',
    }
        
    try:
        _, environment, _ = noh.oraenv(module, database_name)
    except noh.DatabaseNotFound as fault:
        module_fail['stderr'] = str(fault)
        
        module.fail_json(**module_fail)
        
    _, process_list, _ = noh.pgrep(module, pattern='ora_pmon_')
    database_running = [proc for proc in process_list if proc[2] == 'ora_pmon_{0}'.format(database_name)]
    
    if not database_running:
        module_fail.update({
            'stderr': 'Cannot find ora_pmon_{0}'.format(database_name),
            'resultset': process_list,
        })
             
        module.fail_json(**module_fail)
    
    # build up a list of columns using `desc`
    sql_table_columns = '''
        CONN / AS SYSDBA
        DESC {0}
        EXIT
    '''.format(table_name)
        
    _, table_desc, table_desc_err = noh.sqlplus(module, sql_table_columns, environment)
    if table_desc_err:
        module_fail.update({
            'stdout': sql_table_columns,
            'stderr': table_desc_err,
        })
        
        module.fail_json(**module_fail)
    
    # remove the header and split on \t to get the column names
    columns = [
        name.split('\t')[0].strip() for name in table_desc.split('\n')[2:] if name
    ]
        
    if column_as_key is None:
        # tables with a single row (e.g. v$database) are good candidates for a
        # simple dictionary
        _, table_data, table_data_err = noh.table_as_csv(module, environment, table_name, columns)
        
        if table_data_err:
            module_fail['stderr'] = str(fault)
            module.fail_json(**module_fail)
        
        table_data_list = [
            noh.str_to_intfl(column) for column in table_data.split(',')
        ]
        
        resultset = dict(zip(columns, table_data_list))
    else:
        # multiple rows make more sense as nested dictionaries
        # there is no check for uniqueness we assume the enduser has determined
        # a good column to use as the dictionary key
        key_index = columns.index(column_as_key)
        _, table_data, table_data_err = noh.table_as_csv(module, environment, table_name, columns)
        
        if table_data_err:
            module_fail['stderr'] = str(fault)
            module.fail_json(**module_fail)
            
        table_data_list = [
            list(map(noh.str_to_intfl, column.split(','))) for column 
                in table_data.split('\n') if column
        ]
        
        resultset = dict(
            (data_iter[key_index], dict(zip(columns, data_iter)))
                for data_iter in table_data_list
        )
        
    module_exit = {
        'changed': False,
        'msg': 'Table returned as dictionary object',
        'stdout': '',
        'stderr': '',
        'resultset': resultset,
    }
    
    module.exit_json(**module_exit)

if __name__ == "__main__":
    
    argument_spec = {
        "database_name": {
            "required": True,
            "type": "str",
            "aliases": ["name", "sid"],
        },
        "table_name": {
            "required": True,
            "type": "str",
            "aliases": ["table"],
        },
        "column_as_key": {
            "required": False,
            "type": "str",
        }
    }
    
    module = AnsibleModule(
        argument_spec = argument_spec,
    )
    
    main(module)