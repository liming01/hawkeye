import web
import json
from pygresql.pg import *

urls = (
    "/", "Main",
    "/rest", "RestService",
)

render = web.template.render('templates/')

class Main:
    def GET(self):
        return render.main('Hawkeye')

class RestService:
    def GET(self):
        input_data = web.input(resType=None, measureType=None, dimType=None, 
                                hostBeginId=None, hostEndId=None, hostGroupSize=None, 
                                timeBegin=None, timeEnd=None, timeInterval=None)
        res_type = input_data.resType.lower()
        measure_type = input_data.measureType.lower()
        dim_type = input_data.dimType.lower()

        host_begin_id = int(input_data.hostBeginId)
        host_end_id = int(input_data.hostEndId)
        host_group_size = int(input_data.hostGroupSize)
        
        time_begin = input_data.timeBegin
        time_end = input_data.timeEnd
        time_interval = input_data.timeInterval

        if dim_type == 'machine':
            sql = "SELECT {0}({1}) measure, \
                    to_timestamp(floor((extract('epoch' from time) / {2} )) * {2}) AT TIME ZONE 'UTC' as interval_alias, \
                    floor((collect_data.host-{3}) / {4}) * {4} as group_alias \
                    FROM collect_data \
                    WHERE time BETWEEN '{5}' AND '{6}' AND host>={7} AND host<={8} AND pid<0 \
                    GROUP BY interval_alias, group_alias \
                    ORDER BY interval_alias;".format(measure_type, res_type, 
                            time_interval, host_begin_id, host_group_size, time_begin, time_end, 
                            host_begin_id, host_end_id)
        else:
            sql = "SELECT {0}({1}) measure, \
                    to_timestamp(floor((extract('epoch' from time) / {2} )) * {2}) AT TIME ZONE 'UTC' as interval_alias, \
                    floor((collect_data.host-{3}) / {4}) * {4} as group_alias \
                    FROM collect_data \
                    WHERE time BETWEEN '{5}' AND '{6}' AND host>={7} AND host<={8} AND pid>0 \
                    GROUP BY interval_alias, group_alias \
                    ORDER BY interval_alias;".format(measure_type, res_type, 
                            time_interval, host_begin_id, host_group_size, time_begin, time_end, 
                            host_begin_id, host_end_id)
       
        
        print sql

        x = []
        y = {}
        db = DB(dbname='hackday', host='10.103.219.169', user='postgres')
        
        r = db.query(sql)
        for row in r.dictresult():
            x.append(row['interval_alias'])
            if not row['group_alias'] in y:
                y[row['group_alias']] = []
            y[row['group_alias']].append({row['interval_alias'] : int(row['measure'])})


        db.close() 

        result = {
            'x' : [],
            'y' : []
        }

        for item in x:
            if item not in result['x']:
                result['x'].append(item)

        hostnames = []
        for i in range(host_begin_id, host_end_id+1, host_group_size):
            begin_id = i
            end_id = min(i + host_group_size - 1, host_end_id)
            if begin_id == end_id:
                hostnames.append('host'+str(begin_id))
            else:
                hostnames.append('host'+str(begin_id)+'-host'+str(end_id))

        names = []
        for group in y:
            names.append(group)
        names = sorted(set(names))
        
        hostnames_map = {}
        for idx, group in enumerate(names):
            hostnames_map[group] = hostnames[idx]
        
        print hostnames_map

        for group in y:
            name = hostnames_map[group]
            result['y'].append([name, []])

        idx = 0
        for group in y:
            data = y[group]
            for time in result['x']:
                found = False
                for item in data:
                    if time in item:
                        found = True
                        if res_type == 'cpu':
                            result['y'][idx][1].append(item[time]) 
                        else:
                            result['y'][idx][1].append(item[time] / 1024) # MB

                        break
                if not found:
                    result['y'][idx][1].append(0)
            idx += 1
        print result

        return json.dumps(result)
         

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
