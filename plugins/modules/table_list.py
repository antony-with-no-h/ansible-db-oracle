# -*- coding: utf-8 -*-

# Copyright: (c) 2021, antony.with.no.h <https://github.com/antony-with-no-h>
# ISC License (see LICENSE or https://www.isc.org/licenses)

from __future__ import (absolute_import, print_function, division)
__metaclass__ = type

DOCUMENTATION = r"""
module: table_list
author:
  - antony.with.no.h
short_description: Table data as a list
description:
  - Pass one or more table columns and data will be returned as a list
version_added: 0.2.0
options:
  database_name:
    description:
      - Oracle database name
    required: true
    type: str
    aliases: ['name', 'sid']
  table_name:
    description:
      - The table name
  table_columns:
    description:
      - Add or remove database
    required: true
    type: list
  where:
    description:
      - Filter table data
    type: str
  flatten:
    description:
      - List is flattened before being returned
    type: bool
    default: no
notes:
- C(columns) ['*'] is not currently supported
"""

EXAMPLES = r"""
- name: Results are nested by default use flatten to... flatten
  antony_with_no_h.oracle.table_list:
    database_name: ORCL
    table: dba_pdbs
    columns:
      - pdb_name
    flatten: yes

- name: Column functions can be used
  antony_with_no_h.oracle.table_list:
    database_name: ORCL
    table_name: dba_objects
    table_columns:
      - SUBSTR(owner, 20) owner
      - SUBSTR(object_type, 1, 15) obj_type
      - SUBSTR(object_name, 1, 30) obj_name
      - created
      - last_ddl_time

- name: You can also specify conditions
  antony_with_no_h.oracle.table_list:
    database_name: ORCL
    table_name: dba_objects
    table_columns:
      - SUBSTR(owner, 20) owner
      - SUBSTR(object_type, 1, 15) obj_type
      - SUBSTR(object_name, 1, 30) obj_name
      - created
      - last_ddl_time
    where: status != 'VALID'
"""

RETURN = r"""
resultset:
  description: Table data
  returned: always
  type: list
  sample:
"""

from itertools import chain

import ansible_collections.antony_with_no_h.oracle.plugins.module_utils.common as noh
from ansible.module_utils.basic import AnsibleModule

def main(module):
    """ Return query as a list """
    
    database_name = module.params["database_name"]
    table_columns = module.params["columns"]
    query_condition = module.params["where"]
    table_name = module.params["table"]
    flatten = module.params["flatten"]
    
    module_fail = {
        'msg': 'An error has occured',
        'rc': 1,
        'resultset': [],
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
        
    rc, csv_data, csv_err = noh.table_as_csv(module, environment, table_name, table_columns, query_condition)
    
    if csv_err:
        module_fail['stderr'] = csv_data
        module.fail_json(**module_fail)
    
    if csv_data is None:
        module.exit_json(changed=False, msg='no rows selected', resultset=[])
    
    if flatten:
        resultset = list(chain.from_iterable([
            column for column in [row.split(',') for row in csv_data.split('\n') if row]
        ]))
    else:
        resultset = [
            column for column in [row.split(',') for row in csv_data.split('\n') if row]
        ]
        
    module.exit_json(changed=False, resultset=resultset)

if __name__ == "__main__":
    
    argument_spec = {
        "database_name": {
            "required": True,
            "type": "str",
            "aliases": ["name", "sid"],
        },
        "table": {
            "required": True,
            "type": "str",
            "aliases": ["table_name"],
        },
        "columns": {
            "required": True,
            "type": "list",
            "aliases": ["table_columns"],
        },
        "where": {
            "type": "str",
        },
        'flatten': {
            'type': 'bool',
            'default': False,
        }
    }
    
    module = AnsibleModule(
        argument_spec = argument_spec,
    )
    
    main(module)