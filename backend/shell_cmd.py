#!/usr/bin/env python
# encoding: utf-8
'''
This file contains all API for calling shell related commands directly
'''

import logging
import os, sys, subprocess
import re

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)

def parse_command_output(inputs, regexps):
    '''
    inputs:
        inputs: it can be a list with a nested list (like a table: row, column),
            or a string includes all lines, which can be transformed as a table with one column
        regexps: it can be a list with format [[input_col_id, regexp, output_group_num], ...] ,
            or it can be a string which can be transformed as [[0, regexps, 1]]

    Parse the inputs string with regular expression matched on each line, and fetch the groups of matched part as colums of one row
    '''
    result=[]
    line_id = 0
    p=[]

    # if it is a string
    if not hasattr(regexps, '__iter__') or isinstance(regexps, basestring):
        regexps = [[0, regexps, 1]]
    for rei in regexps:
        if(len(rei)!=3):
            logger.error("Format error for : %s" % (rei))
            raise Exception("Format error for : %s" % (rei))
        p.append(re.compile(rei[1]))

    # if inputs is a non-string sequence and is iterable, then it should a list, each item stands for a line
    if hasattr(inputs, '__iter__') and not isinstance(inputs, basestring):
        content = inputs
    else:
        content = inputs.splitlines()

    while(line_id<len(content)):
        row = []
        m = []
        is_all_matched = True
        j=-1
        for rei in regexps:
            j+=1
            input_col_id = rei[0]
            if input_col_id==-1 or content != inputs: #the whole item
                line = content[line_id]
            else:
                line = content[line_id][input_col_id]

            mi = p[j].match(line)
            if mi:
                m.append(mi)
            else:
                is_all_matched = False
                break

        if is_all_matched:
            i=-1
            for rei in regexps:
                i+=1
                group_num = rei[2]
                for gid in range(1, group_num+1):
                    row.append(m[i].group(gid));
            result.append(row)

        line_id+=1;
        
    return result

def run_shell_command(cmd, isRaiseException=True, isReturnRC=False):

    _cmd = '%s' % (cmd)
    logger.debug('shell command is: %s', (_cmd))
    p = subprocess.Popen(_cmd, shell=True,
                              close_fds=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
    result = p.communicate()
    if isReturnRC:
        return p.returncode
    if p.returncode != 0:
        logger.debug(result[0])
        if isRaiseException:
            logger.error("Error at execute: %s %s %s" % (str(cmd), result[0], result[1]))
            raise Exception(result[1])
    return result[0]

def run_shell_get_hostname():
    output = run_shell_command('hostname')
    return output.strip()

def run_shell_get_mem_stat():
    print "call run_shell_get_mem_stat()"
    output = run_shell_command('cat /proc/meminfo')
    result1 = parse_command_output(output,[[0,'^MemTotal:\s+(\d+)\s+kB', 1]])
    result2 = parse_command_output(output,[[0,'^MemFree:\s+(\d+)\s+kB', 1]])
    result3 = parse_command_output(output,[[0,'^Buffers:\s+(\d+)\s+kB', 1]])
    result4 = parse_command_output(output,[[0,'^Cached:\s+(\d+)\s+kB', 1]])
    return (result1[0][0], result2[0][0], result3[0][0], result4[0][0])

def run_shell_get_QE_mem_stat():
    print "call run_shell_get_mem_stat()"
    output_ps=run_shell_command('ps -ef | grep postgres')
    rs=[]
    # match master pid regexp    
    result = parse_command_output(output_ps,[[0,'^\w+\s+(\d+)\s+\d+\s+\d+\s+[\d|:|\w]+\s+[?|\w|/]+\s+[\d|:]+\s+postgres:\s+port\s+\d+,\s+\w+\s+\w+\s+\\[\w+\\]\s+con(\d+)\s+\\[\w+\\]\s+cmd(\d+)\s+(.*)$', 4]])
    for i in range(0,len(result)):
	row = []
	pid=int(result[i][0])
	row.append(pid)
	row.append(int(result[i][1])) #conn_id
	row.append(int(result[i][2])) #cmd_id
	row.append(result[i][3].strip()) #cmd_desc
	output = run_shell_command('cat /proc/%d/status'% (pid))
	result1 = parse_command_output(output,[[0,'^VmRSS:\s+(\d+)\s+kB', 1]])
	row.append(int(result1[0][0])) # Vm_RSS
	rs.append(row)
    # match segment  pid regexp    
    result = parse_command_output(output_ps,[[0,'^\w+\s+(\d+)\s+\d+\s+\d+\s+[\d|:|\w]+\s+[?|\w|/]+\s+[\d|:]+\s+postgres:\s+port\s+\d+,\s+\w+\s+\w+\s+[\d|\.]+\\(\d+\\)\s+con(\d+)\s+seg(\d+)\s+(.*)$', 4]])
    for i in range(0,len(result)):
	row = []
	pid=int(result[i][0])
	row.append(pid)
	row.append(int(result[i][1])) #conn_id
	row.append(int(result[i][2])) #seg_id
	row.append(result[i][3].strip()) #cmd_desc
	output = run_shell_command('cat /proc/%d/status'% (pid))
	result1 = parse_command_output(output,[[0,'^VmRSS:\s+(\d+)\s+kB', 1]])
	row.append(int(result1[0][0])) # Vm_RSS
	rs.append(row)
    return rs
#-------------------------------------------------------------
def run_shell_ls(path, isRecurs=False):
    """
    Return [['d', 'dir_path1'], ['-', 'file_path1'], ...]
    """
    cmd = 'ls '
    if isRecurs:
        cmd += '-R '
    cmd += path

    output = run_shell_command(cmd)
    result = parse_command_output(output,[[0,'^([d|-])[r|w|x|-]{9,9}\s+[-|\d]\s+\w+\s+\w+\s+\d+\s+[\d|-]+\s+[\d|:]+\s+(.*)', 2]])
    return result

def run_shell_mkdir(path, isRecurs=False):
    cmd = 'mkdir '
    if isRecurs:
        cmd += '-p '
    cmd += path

    run_shell_command(cmd)

def run_shell_rm(path, isRecurs=False):
    cmd = 'rm '
    if isRecurs:
        cmd += '-R '
    cmd += path

    run_shell_command(cmd)

def run_shell_mv(path, new_path):
    cmd = 'mv %s %s'% (path, new_path)
    run_shell_command(cmd)

def run_shell_test(path, flag):
    cmd = 'test %s %s' % (flag, path)
    return run_shell_command(cmd, isReturnRC=True)

def run_shell_leave_safemode():
    # force to leave safe mode
    cmd = 'dfsadmin -safemode leave'
    run_shell_command(cmd, isDfs=False, isRaiseException=True)

def run_shell_create_snapshot(path, snapshotname):
    # add permission
    cmd = 'dfsadmin -allowSnapshot %s' % path;
    run_shell_command(cmd, isDfs=False)

    cmd = 'createSnapshot %s '% (path)
    if snapshotname:
        cmd += snapshotname
    run_shell_command(cmd)

def run_shell_rename_snapshot(path, oldname, newname):
    cmd = 'renameSnapshot %s %s %s'% (path, oldname, newname)
    run_shell_command(cmd)

def run_shell_delete_snapshot(path, snapshotname):
    cmd = 'deleteSnapshot %s %s'% (path, snapshotname)
    run_shell_command(cmd)


def run_shell_restore_snapshot(path, snapshotname):
    ss_path = os.path.join(path, '.snapshot', snapshotname)
    result = run_shell_ls(ss_path, True)
    for dir, path1 in result:
        if dir!='d':
            path2 = path1.replace("/.snapshot/%s"%snapshotname, "")
            cmd = 'cp -f -p %s %s' % (path1, path2)
            run_shell_command(cmd)
    # successfully restored snapshot, we can delete the snapshot now
    run_shell_delete_snapshot(path, snapshotname)

if __name__ == '__main__':
    # firstly test gdb exists
    #gdb_path = spawn.find_executable("shell")
    #if not gdb_path:
        #logger.info("hadoop shell command doesn't exists, please make sure you have installed hadoop!")
        #exit(1);
    # result = run_shell_ls('/hawq1/gpseg0', True)
    # print "result: %s" % result
    # result1 = run_shell_ls('/hawq1/', False)
    # print "result1: %s" % result1
    # result2 = parse_command_output(result1, [[0, '^(d)$', 1], [1, '^(.*/gpseg\d+)$', 1]])
    # print "result2: %s" % result2
    # result3 = parse_command_output(result1, [[0, '^d$', 0], [1, '^(.*/gpseg\d+)$', 1]])
    # print "result3: %s" % result3
    # result4 = run_shell_test('shell://localhost:9000/hawq1/gpseg0/.snapshot/.gpmigrator_orig', '-e');
    # print "result4: %s" % result4
    # result4 = run_shell_test('shell://localhost:9000/hawq1/gpseg0/.snapshot/.gpmigrator_orig1', '-e');
    # print "result4: %s" % result4
    result = run_shell_get_hostname()
    print "reslut10: %s " % result;

    result = run_shell_get_QE_mem_stat()
