import sys
sys.path.append("src")
from datetime import datetime

from . import db

def insert(DATA):
    db.db[db.collTransfers].insert_one(DATA)

def addToTransfers(t_from, t_to, t_amount, t_token, t_timestamp, t_block, t_data, t_id):
    insert({
        "from": t_from,
        "to": t_to,
        "amount": t_amount if t_token!= 'TRX' else t_amount/1000000,
        "token": t_token,
        "timestamp": t_timestamp,
        "block": t_block,
        "data": t_data,
        "txid": t_id,
        "update": datetime.utcnow(),
    })


def getTransactionsToAddress(address):
    result = db.db[db.collTransfers].find({'address': address}).sort("update", -1)
    return list(result)

