import json
import os

meta = json.load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'meta.json')))
connector = meta.get('connector')
if connector not in ['jdbc']:
    raise Exception('unsupported connector %s' % connector)
print meta
