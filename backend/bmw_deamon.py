#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
from datetime import datetime as dtdatetime
import logging
import logging.handlers
import select
import psycopg2
import psycopg2.extensions
import threading
import time


# Python version 2.6.2 is expected, must be between 2.5-3.0
if sys.version_info < (2, 5, 0) or sys.version_info >= (3, 0, 0):
    sys.stderr.write("Error: %s is supported on Python versions 2.5 or greater\n"
                         "Please upgrade python installed on this machine."
                          % os.path.split(__file__)[-1])
    sys.exit(1)


try:
    from shell_cmd import *
except ImportError, e:
    sys.exit('Error: unable to import module: ' + str(e))


#------------------------------- Public --------------------------------    
dbname = 'hackday'
host = '10.103.219.169'
user = 'postgres'
password = 'passw0rd'
LOGGER=None
host_id = None
conn=None
cfg = []
timers = []
isExiting = False
#------------------------------- Public Interface --------------------------------
def get_default_logger():
    """
    Return the singleton default logger.

    If a logger has not yet been established it creates one that:
              - Logs output to stdout
      - Does not setup file logging.

    Typicial usage would be to call one of the setup_*_logging() functions
    at the beginning of a script in order to establish the exact type of
    logging desired, afterwhich later calls to get_default_logger() can be
    used to return a reference to the logger.
    """
    global LOGGER
    if LOGGER is None:
        handler = logging.handlers.RotatingFileHandler("bmw_deamon.log", maxBytes = 1024*1024, backupCount = 5)
        fmt = '%(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s'
        formatter = logging.Formatter(fmt)
        handler.setFormatter(formatter)
        LOGGER = logging.getLogger('bmw_deamon')
        LOGGER.addHandler(handler)
        LOGGER.setLevel(logging.DEBUG)

def exec_insert_collect_data(sql):
    global conn
    
    cur = conn.cursor()
    try:
        print 'SQL:%s' %sql
        cur.execute(sql)
    except:
        print "Can't execute sql:'%s''" %sql


def deamon_process(cfg_id):
    global cfg, timers, host_id
    print "deamon_process@cfg_id:%i"%cfg_id
    #check enable
    if not cfg[cfg_id][1]:
        timers[cfg_id].cancel()
        return
    # call shell to fetch statitics info
    if cfg[cfg_id][4]=='*':
        (res1,res2,res3,res4)= run_shell_get_mem_stat()
        mem_total=int(res1)
        mem_free=int(res2)
        buffers=int(res3)
        cached=int(res4)
        sql = """INSERT INTO collect_data values(%i, current_timestamp(0), %i, -1,-1,-1, %i, -1,-1,-1, %i, %i)""" % (cfg[cfg_id][0], host_id, mem_total-mem_free-buffers-cached, mem_total, mem_free)
        exec_insert_collect_data(sql)
    elif cfg[cfg_id][4]=='QE':
	rs = run_shell_get_QE_mem_stat() 
	for r in rs:
	    sql = """INSERT INTO collect_data values(%i, current_timestamp(0), %i, %i,%i,%i, %i, -1,-1,-1, -1, -1)""" % (cfg[cfg_id][0], host_id, r[0],r[1],r[2],r[4])
	    exec_insert_collect_data(sql)
	

    else:
        print "To Do 2"
    # reset time
    global isExiting
    if not isExiting:
        timers[cfg_id]=threading.Timer(cfg[cfg_id][2], deamon_process, [cfg_id])
        timers[cfg_id].start()

#============================================================
class BMW_Deamon:
 #------------------------------------------------------------
    def __init__(self):
        self.dsn = 'dbname=%s host=%s user=%s password=%s' % (dbname, host, user, password) 
        self.hostname = run_shell_get_hostname()
        #self.hostname='test1'
        global cfg,timers,conn
        self.cfg = cfg
        self.timers = timers
        # tempory hack
        # init array size
        size=256
        for i in range(0,size):
            self.cfg.append(None)
            self.timers.append(None)
        try:
            self.conn=psycopg2.connect(self.dsn)
            self.conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        except:
            print "I am unable to connect to the database."
        conn=self.conn


    def Get_monitor_cfg(self):
        # fetch host_id
        cur = self.conn.cursor()
        try:
            _cmd="""SELECT id from hosts where host='%s'"""%self.hostname
            print 'SQL:%s' %_cmd
            cur.execute(_cmd)
        except:
            print "Can't SELECT id from hosts table for host='%s''" %self.hostname

        rows = cur.fetchall()
        if len(rows)!=1:
            print "select id from hosts return %i rows."%len(rows) 
            exit(0);

        global host_id
        host_id = rows[0][0]
        #fetch config for this host_id
        cur = self.conn.cursor()
        try:
            _cmd = """SELECT * from monitor_meta where enable=TRUE AND (-1=ANY(host) OR %i=ANY(host)) ORDER BY id"""%host_id
            print 'SQL:%s' %_cmd
            cur.execute(_cmd)
        except:
            print "Can't SELECT from monitor_meta table for host='%s', host_id='%i'" % (self.hostname, host_id)

        rows = cur.fetchall()
        for row in rows:
            r = []
            for item in row:
                r.append(item)
            self.cfg[r[0]] = r
            self.timers[r[0]]=None

    def process_deamon_timers(self, cfg_id=-1, operator =1):
        """
        operator:  1 -- insert  2 -- update 3-- delete
        cfg_id:  -1 indicate all rows in rule array need to be process
        """
        if cfg_id != -1:
            if cfg[cfg_id] == None:
                return
            if operator==1:
                if self.timers[cfg_id]!=None:
                    print "timers[%i] already created, can't create twice."% cfg_id
                self.timers[cfg_id]=threading.Timer(cfg[cfg_id][2], deamon_process, [cfg_id])
                self.timers[cfg_id].start()

            elif operator==2:
                if self.timers[cfg_id]==None:
                    print "timers[%i] doesn't exists, can't be updated."% cfg_id
                self.timers[cfg_id].cancel()
                self.timers[cfg_id]=threading.Timer(cfg[cfg_id][2], deamon_process, [cfg_id])
                self.timers[cfg_id].start()
            elif operator==3:
                if self.timers[cfg_id]==None:
                    print "timers[%i] doesn't exists, can't be deleted."% cfg_id
                    self.timers[cfg_id].cancel()
            else:
                print "get wrong operator: %i "%operator
        
        else:
            for i in range(0, len(self.cfg)):
                self.process_deamon_timers(i, operator)


    def Listen_at_db(self):

        curs = self.conn.cursor()
        curs.execute("LISTEN monitor_meta;")
        LOGGER.info("Waiting for 'NOTIFY monitor_meta'")

        print "Waiting for 'NOTIFY monitor_meta'"
        while 1:
            if select.select([self.conn],[],[],5)==([],[],[]):
                sys.stdout.write(".")
                sys.stdout.flush()
            else:
                self.conn.poll()
                while conn.notifies:
                    notify = conn.notifies.pop()
                    print "Got NOTIFY:", notify.pid, notify.channel, notify.payload
                    if notify.payload=='quit':
                        print "User requests to quit."
                        for i in range(0, len(self.cfg)):
                            self.process_deamon_timers(i, 3)
                        global isExiting
                        isExiting = True
                        exit(0)
                    payload = notify.payload.split('_')
                    rule_id = int(payload[1])
                    #operator:  1 -- insert  2 -- update 3-- delete
                    if payload[0] == 'DELETE':
                        operator=3
                        self.cfg[rule_id]=None
                        self.process_deamon_timers(rule_id, operator)
                        continue
                    elif payload[0] == 'UPDATE':
                        operator=2
                    elif payload[0] == 'INSERT':
                        operator=1
                    else:
                        print "Get error notify for operator: %s" % payload[0]
                        continue
                    #re fetch cfg_meta 
                    global host_id
                    cur = self.conn.cursor()
                    try:
                        _cmd = """SELECT * from monitor_meta where enable=TRUE AND (-1=ANY(host) OR %i=ANY(host))
                                AND id=%i ORDER BY id"""%(host_id, rule_id)
                        print 'SQL:%s' %_cmd
                        cur.execute(_cmd)
                    except:
                        print "Can't SELECT from monitor_meta table for host='%s', host_id='%i'" % (self.hostname, host_id)

                    rows = cur.fetchall()
                    if len(rows)>1:
                        print "select from monitor_meta for id:%i return %i rows"%(rule_id, len(rows))
                    r = []
                    for item in rows[0]:
                        r.append(item)
                    if operator==1:
                        self.cfg[r[0]] = r
                    elif operator==2:
                        self.cfg[r[0]]= r
                    # change deamon timer
                    self.process_deamon_timers(rule_id, operator)



#============================================================
if __name__ == '__main__':
    get_default_logger()
    dm = BMW_Deamon()

    # parses and validates input
    try:
        dm.Get_monitor_cfg()
        dm.process_deamon_timers()
        dm.Listen_at_db()
    except Exception, e:
        logger.fatal(str(e))
        raise e
        sys.exit(1)

