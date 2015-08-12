for host in `cat all_hosts`; do ssh $host 'scp -r gpadmin@test1:~/workspace/hack_day/ ~/workspace/' ; done
for host in `cat all_hosts`; do ssh $host 'scp -r gpadmin@test1:~/workspace/hack_day/bmw_deamon.py ~/workspace/hack_day/' ; done
for host in `cat all_hosts`; do ssh $host 'python ~/workspace/hack_day/bmw_deamon.py >~/workspace/hack_day/logfile 2>&1 &' ; done
