# -*- coding: utf-8 -*-

# Copyright: (c) 2021, antony.with.no.h <https://github.com/antony-with-no-h>
# ISC License (see LICENSE or https://www.isc.org/licenses)

from __future__ import (absolute_import, print_function, division)
__metaclass__ = type

DOCUMENTATION = r"""
module: inventory
author:
  - antony.with.no.h
short_description: Parse Oracle Central Inventory
description:
  - Return inventory as a dictionary
version_added: 0.1.0
options:
  orainst_loc:
    description:
      - Path to the oraInst.loc file
    default: /etc/oraInst.loc
    type: str
notes:
"""

EXAMPLES = r"""
- name: Parse inventory
  antony_with_no_h.oracle.inventory:
  register: orainventory
  
- ansible.builtin.assert:
    that: '/u01/app/oracle/product/19.0.0/dbhome_1' in orainventory.resultset
"""

import itertools
import os

from xml.etree import ElementTree

from ansible.module_utils.basic import AnsibleModule

def main(module):
    """ Parser for Oracle Inventory """
    orainst_loc = module.params['orainst_loc']
    
    if not os.path.isfile(orainst_loc):
        module.exit_json(changed=False, msg='File not found', resultset={})
    
    # Oracle central inventory can be created anywhere but oracle recommends oraInst.loc
    # be in /etc/oraInst.loc or /var/opt/oracle/oraInst.loc (solaris)
    with open(orainst_loc, 'r') as fd:
        lines = fd.read()
        
    inventory_loc = list(itertools.chain.from_iterable(
        line.split('=') for line in lines.split('\n') if 'inventory_loc' in line
    ))
    
    if not inventory_loc:
        module.fail_json(msg='Cannot locate central inventory', resultset=lines)
    else:
        inventory_file = '/'.join([inventory_loc[1], 'ContentsXML', 'inventory.xml'])
        
    # inventory_loc is just a pointer to where the inventory should be
    # most oracle db products have a script to create it if this it the first
    # installation
    if not os.path.isfile(inventory_file):
        module.exit_json(changed=False, msg='Inventory does not exist', resultset={})
    
    with open(inventory_file, 'r') as fd:
        xml_tree = ElementTree.parse(fd)
        
        # everything between <INVENTORY> tags
        xml_root = xml_tree.getroot()
        
        # each installed product is in a HOME tag
        # when ansible drops 2.6 support will update this to a dict comp
        try:
            inventory = dict(
                (attrs.attrib['LOC'], {
                    'name': attrs.attrib['NAME'],
                    'crs': True if 'CRS' in attrs.attrib else False,
                }) for attrs in xml_root.iter('HOME')
            )
        except AttributeError:
            inventory = dict(
                (attrs.attrib['LOC'], {
                    'name': attrs.attrib['NAME'],
                    'crs': True if 'CRS' in attrs.attrib else False,
                }) for attrs in xml_root.getiterator('HOME')
            )
            
    module.exit_json(changed=False, msg='Inventory parsed', resultset=inventory)
    
if __name__ == "__main__":
    
    argument_spec = {
        "orainst_loc": {
            "required": False,
            "type": "str",
            "default": "/etc/oraInst.loc",
        },
    }
    
    module = AnsibleModule(
        argument_spec = argument_spec,
    )
    
    main(module)