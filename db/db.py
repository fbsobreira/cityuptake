import sys

from pymongo import MongoClient
import logging

# this is a pointer to the module object instance itself.
this = sys.modules[__name__]
this.db = None
this.client = None

this.DBNAME = 'cityuptake'

collTransfers = 'transfers'
collInfo = 'info'


def start(dbName, username, password, host, port, authDB):
    # MongoDB connection
    if username == "NA":
        this.client = MongoClient()
    else:
        this.client = MongoClient(host+":"+port,
                        username=username,
                        password=password,
                        authSource=authDB)

    # Database
    if dbName != None:
        this.DBNAME = dbName
    this.db = this.client[this.DBNAME]
    print("Connected to MongoDB successfully!")
    createIndex()

def createIndex():

    transfers_index = ['address_from','address_from','txID','update','timestamp']
    for ti in transfers_index:
        if ti+"_1" not in db[collTransfers].index_information():
            db[collTransfers].create_index([(ti, 1)],
                                background=True)
            logging.info('Index {} added'.format(ti))

def deleteAll():
    db[collTransfers].remove()
    db[collInfo].remove()
