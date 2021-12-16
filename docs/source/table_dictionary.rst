.. _table_dictionary_module:


table_dictionary -- Table as a dictionary
=========================================

.. contents::
   :local:
   :depth: 1


Synopsis
--------

Returns a nested or unnested collection of key value pairs






Parameters
----------

  database_name (True, str, None)
    Name of the database to connect to


  table_name (True, str, None)
    The database table to be queried


  column_as_key (False, str, None)
    Use column name as dictionary key

    Specifying this parameter will return a nested dictionary









Examples
--------

.. code-block:: yaml+jinja

    
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





Status
------





Authors
~~~~~~~

- antony.with.no.h

