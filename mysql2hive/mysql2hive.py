# coding=utf-8
import json
import os
import jinja2
from datetime import datetime, date, timedelta
import commands
import sys

reload(sys)
sys.setdefaultencoding('utf8')

meta = json.load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'meta.json')))
config = json.load(open(sys.argv[1]))

db_info = meta['databases'][config['mysql']['db']]
connect = "jdbc:mysql://{host}:{port}/{db_name}".format(
    host=db_info['host'],
    port=db_info['port'],
    db_name=db_info['db']
)
username = db_info['username']
password = db_info['password']

# mysql配置
mysql_table = config['mysql']['table']
incremental = config['mysql'].get('incremental')
check_column = config['mysql'].get('check-column')
last_value = eval(config['mysql'].get('last-value'))
columns = ','.join(config['mysql'].get('columns') or []) or None

# hive配置
hive_db = config['hive']['db']
hive_table = config['hive']['table']
partition = config['hive'].get('partition')
if partition is not None:
    assert len(partition.keys()) == 1
    partition_key = partition.keys()[0]
    partition_value = eval(partition[partition_key])
else:
    partition_key = None
    partition_value = None

# 其他配置
overwrite = config['hive'].get('overwrite')
compress = config['hive'].get('compress')
compression_codec = config['hive'].get('compression_codec')
num_mappers = config['hive'].get('num-mappers')
split_by = config['hive'].get('split-by')

cmd = """ sqoop import --hive-import --hive-drop-import-delims
{# mysql连接属性 #}
--connect {{ connect }}
--username {{ username }}
--password {{ password }}

{# source配置#}
--table {{ mysql_table }}
{% if columns is not none %}
--columns {{ columns }}
{% endif %}
{% if incremental is not none %}
--incremental {{ incremental }}
--check-column {{ check_column }}
--last-value '{{ last_value }}'
{% endif %}

{# target配置 #}
--hive-database {{ hive_db }}
--hive-table {{ hive_table }}
{% if partition_key is not none %}
--hive-partition-key {{ partition_key }}
--hive-partition-value '{{ partition_value }}'
{% endif %}


{# 其他配置 #}
{% if compress %}
--compress
{% endif %}
{% if compression_codec is not none %}
--compression-codec {{ compression_codec }}
{% endif %}
{% if num_mappers is not none %}
--num-mappers {{ num_mappers }}
{% endif %}
{% if overwrite %}
--hive-overwrite
{% endif %}

"""
cmd = jinja2.Template(cmd).render(
    connect=connect,
    username=username,
    password=password,
    mysql_table=mysql_table,
    columns=columns,
    incremental=incremental,
    check_column=check_column,
    last_value=last_value,
    hive_db=hive_db,
    hive_table=hive_table,
    partition_key=partition_key,
    partition_value=partition_value,
    compress=compress,
    compression_codec=compression_codec,
    num_mappers=num_mappers,
    overwrite=overwrite
).replace('\n', ' ')

status, output = commands.getstatusoutput(cmd)
print output
if status != 0: exit(1)
