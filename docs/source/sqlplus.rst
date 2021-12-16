.. _sqlplus_module:


sqlplus -- Run queries against database
=======================================

.. contents::
   :local:
   :depth: 1


Synopsis
--------

Use SQL*Plus to create a session and run database commands






Parameters
----------

  database_name (True, str, None)
    Oracle database name (SID)


  sql (True, str, None)
    A block of SQL to be run

    Accepts PL/SQL


  raw (optional, bool, False)
    Errors will be sent to stderr only by default

    Enable to return the complete traceback from SQL*Plus


  ignore_errors (optional, bool, False)
    Module fails on error (ORA-* or SP2-*)


  chdir (optional, any, None)
    Working directory to start SQL*Plus in





Notes
-----

.. note::
   - SQL*Plus is started with nolog, specify the connection string to connect to the database e.g. ``conn / as sysdba``
   - Single numeric type values (count(*)) will be returned as int/float
   - Host commands are blocked (!/HOST)




Examples
--------

.. code-block:: yaml+jinja

    
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



Return Values
-------------

resultset (always, str, None)
  Output from SQL*Plus





Status
------





Authors
~~~~~~~

- antony.with.no.h

