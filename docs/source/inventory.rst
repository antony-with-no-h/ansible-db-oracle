.. _inventory_module:


inventory -- Parse Oracle Central Inventory
===========================================

.. contents::
   :local:
   :depth: 1


Synopsis
--------

Return inventory as a dictionary






Parameters
----------

  orainst_loc (optional, str, /etc/oraInst.loc)
    Path to the oraInst.loc file









Examples
--------

.. code-block:: yaml+jinja

    
    - name: Parse inventory
      antony_with_no_h.oracle.inventory:
      register: orainventory
      
    - ansible.builtin.assert:
        that: '/u01/app/oracle/product/19.0.0/dbhome_1' in orainventory.resultset





Status
------





Authors
~~~~~~~

- antony.with.no.h

