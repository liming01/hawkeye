- Introduction
A tools to collection statistics info for lost of machines. All config data and statiscs data collected need to be stored in postgresql.

Now for simplicity, there is no UI to define monitor rules. We can directly change them in postgresql table monitor_meta, and monitor on all other's nodes will be notified and changed accordingly. After finishing collecting data, you can run below sql to quit all monitor on all nodes:
  sql> notify monitor_meta , 'quit';

- Preparation for one machine:

—- PostgreSQL server version >=9.0
yum install postgresql-server
service postgresql restart

run sql file postgresql.sql to init db

- Preparation for all hosts need to be monited:
—- PostgreSQL client and python client (version > 2.4)
yum install postgresql
yum install python-psycopg2

after that, you can write all nodes' hostname into file: all_hosts, then run below command to copy directory to all nodes.
  shell> for host in `cat all_hosts`; do ssh $host 'scp -r gpadmin@test1:~/workspace/hack_day/ ~/workspace/' ; done 

Fininally, you can run the monitor:
  shell> for host in `cat all_hosts`; do ssh $host 'python ~/workspace/hack_day/bmw_deamon.py >~/workspace/hack_day/logfile 2>&1 &' ; done
