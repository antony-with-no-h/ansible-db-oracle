# -*- coding: utf-8 -*-

# Copyright: (c) 2021, antony.with.no.h <https://github.com/antony-with-no-h>
# ISC License (see LICENSE or https://www.isc.org/licenses)

from __future__ import (absolute_import, print_function, division)
__metaclass__ = type

import csv
import re
import os

class DatabaseNotFound(Exception):
    pass

def pgrep(module, pattern=None, user=None):
    """ A poor mans psutil """
        
    if not (pattern or user):
        raise TypeError('missing required positional argument')
    
    # `ps` no header and print pid,user and the command string: comma separated
    command = ['ps', 'h', '-o %p,', '-o %u,', '-o cmd', '-p']
    
    # use pgrep to filter 
    if pattern:
        command.append('$(pgrep -d, -f {0})'.format(pattern))
    else:
        command.append('$(pgrep -d, -u {0})'.format(user))
    
    run_c = ' '.join(command)
    
    rc, stdout, stderr = module.run_command(args=run_c, use_unsafe_shell=True)
    
    if rc != 0:
        return (rc, [], stderr)
    
    ps_list = [
        ps for ps in [
            [col.strip() for col in row.split(',', 2)] for row in stdout.split('\n') if row
        ]
    ]
    
    return (rc, ps_list, stderr)
    
def oratab(oratab_loc='/etc/oratab'):
    """ Format oratab as a dictionary """
        
    with open(oratab_loc, 'r') as fd:
        oratab_contents = list(csv.reader(strip_comments(fd)))
    
    oratab_dict = dict(
        (row[0], {
            'oracle_home': row[1],
            'dbstart': row[2],
        }) for row in (line[0].split(':') for line in oratab_contents if line)
    )
    
    #oratab_dict = {
    #    row[0]: {
    #        'oracle_home': row[1],
    #        'dbstart': row[2],
    #    } for row in [line[0].split(':') for line in oratab_contents if line]
    #}
    
    return oratab_dict

def oraenv(module, database_name, oratab_loc='/etc/oratab', oracle_base=None):
    """ Create an environment dictionary from the database name """
    
    oratab_dict = oratab(oratab_loc)
    if database_name not in oratab_dict:
        raise DatabaseNotFound('No oratab entry for {0}'.format(database_name))
    
    oracle_home = oratab_dict[database_name]['oracle_home']
    
    environment = {
        'PATH': ":".join([
                    '{0}/srvm/admin'.format(oracle_home),
                    '{0}/perl/bin'.format(oracle_home),
                    '{0}/OPatch'.format(oracle_home),
                    '{0}/bin'.format(oracle_home),
                    '/usr/local/bin',
                    '/usr/bin',
                    '/bin'
                ]),
        'ORACLE_HOME': oracle_home,
        'ORACLE_SID': database_name,
    }
    
    if not oracle_base:
        rc, stdout, _ = module.run_command(['orabase'], environ_update=environment)
        
        if rc == 0:
           environment['ORACLE_BASE'] = stdout.strip() 
    else:
        environment['ORACLE_BASE'] = oracle_base
    
    # this is a proprietary implementation that has been left in
    database_env = '{0}/{1}.env'.format(oracle_home, database_name)
    
    if os.path.exists(database_env):
        with open(database_env, 'r') as fd:
            lines = list(csv.reader(strip_comments(fd)))
        
        # find all lines which valid POSIX variables and not empty
        re_posix_var = re.compile(r'(?:export\s?)([a-zA-Z_]+\w*=(?!$).*)|(^[a-zA-Z_]+\w*=(?!$).*)')
        
        valid_lines = [
            line[0].replace('export ', '') for line in lines if re_posix_var.match(line[0])
        ]
        
        # update environment dictionary
        for line in valid_lines:
            key, value = line.split('=', 1)
            
            # to account for any databases which are customised with things like
            # Heterogeneous Services or a dedicated listener (TNS_ADMIN)
            # we keep these variables in an environment file
            if key == 'PATH':
                environment["PATH"] += ":{0}".format(
                    ":".join([p for p in value.split(":") if p != '$PATH'])
                )
            else:
                environment.update({key: value.replace('"', '')})
           
    return (0, environment, None)

def sqlplus(module, sql, environment, raw_return=False, cd=None):
    """ Pass commands to SQL*Plus """
    
    re_errors = re.compile(r'[A-Z]{2}\d-\d{4}:.*|[A-Z]{3}-\d{5,}:.*', re.MULTILINE)
    re_sub_errors = re.compile(r'\*\nERROR at line \d{1,}:|[A-Z]{2}\d-\d{4}:.*|[A-Z]{3}-\d{5,}:.*', re.MULTILINE)
    
    sqlplus_quiet_nolog = ['sqlplus', '-s', '/nolog']
    
    rc, stdout, stderr = module.run_command(
        args=sqlplus_quiet_nolog,
        cwd=cd,
        data=sql,
        environ_update=environment,
    )
    
    # most likely an error starting sqlplus and not the sql itself
    if stderr:
        return (rc, stdout, stderr)
    
    # ORA-/SP2 etc errors are not written to stderr
    query_errors = '\n'.join(re_errors.findall(stdout))
    
    # multi-block may be easier to debug without substitution
    if raw_return:
        query_result = stdout
    else:
        # at a playbook/role level I found it easier to cast ints and floats here
        # before sending back to 'Ansible' which will then handle them properly
        # rather than having to use filters constantly
        query_result = str_to_intfl(re_sub_errors.sub("", stdout))
    
    return (rc, query_result, query_errors)
    
def table_as_csv(module, environment, table, columns, predicates=None):
    """ Fetch and send back the contents of a table in CSV format """
    
    # a 12.1 and earlier way of creating CSVs
    # sqlplus 12.2+ has newer syntax to make this a lot easier
    
    # made with performance, catalog or data dict. views/tables in mind.
    # Not your application table with loads of data in it
    
    # start building a cursor
    sql_columns = ','.join(columns)
    
    sql_cursor = '''
        CURSOR query_data IS
        SELECT {0}
          FROM {1}
    '''.format(sql_columns, table)
       
    if predicates is not None:
        sql_cursor += ' WHERE {0}'.format(predicates)
    
    # should handle function calls with column aliases but not robustly tested
    l_output_columns = "||','||".join([
        "row." + col for col in (line.split()[-1] for line in columns)
    ])
    
    dynamic_sql = '''
        CONN / AS SYSDBA
        SET LINES 1000 PAGES 0 FEEDBACK OFF SERVEROUT ON
        DECLARE
            {0};
            l_output VARCHAR2(32767);
        BEGIN
            FOR row IN query_data LOOP
                l_output := {1};
                DBMS_OUTPUT.put_line(l_output);
            END LOOP;
        END;
        /
    '''.format(sql_cursor, l_output_columns)
    
    rc, stdout, stderr = sqlplus(module, dynamic_sql, environment, True)
    
    if not stderr:
        return (0, stdout, stderr)
    else:
        return (1, stdout, stderr)
    
def strip_comments(data):
    """ Remove block and inline comments """
    
    for line in data:
        columns = line.split('#')
        not_hashed = columns[0].strip()
        
        if not_hashed:
            yield not_hashed

def str_to_intfl(value):
    """ Cast to int/float or send back """
    
    if not value:
        return value
    
    # i know...
    try:
        return_value = int(value)
    except ValueError:
        pass
    else:
        return return_value
    
    try:
        return_value = float(value)
    except ValueError:
        pass
    else:
        return return_value
    
    return value.strip()