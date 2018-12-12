import sys
sys.path.append("src")

from . import db
from pprint import pprint   

def set(field, value):
    db.db[db.collInfo].update_one({},{'$set': {field: value}}, upsert=True)

def get(field):
    result = db.db[db.collInfo].find_one({})
    if result is None:
        return None
    if field in result:
        return result[field]
    else:
        return None
