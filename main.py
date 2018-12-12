import sys
import re
import os
import codecs # UniCode support

from math import ceil
from time import sleep
import logging
import argparse
import asyncio
from datetime import datetime
from pprint import pprint

from bson.int64 import Int64
from db import db, info, transfers

from tronapi import Tron
from tools.tronconfig import TronConfigParser
from pprint import pprint

def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

parser = argparse.ArgumentParser()
parser.add_argument('--clear', action='store_true', default=False,
                    dest='clear', help='Clear DB')

parser.add_argument('--debug', action='store_true', default=True,
                    dest='debug', help='Debug mode')

results = parser.parse_args()

# start loggin
if results.debug:
    logging.basicConfig(format='%(asctime)s %(message)s',filename='tron_track.log',filemode='w',level=logging.DEBUG)
else:
    logging.basicConfig(format='%(asctime)s %(message)s',level=logging.DEBUG)


config = TronConfigParser()
config.read('config.conf')
checkPing = int(config['DEFAULT']['PING_INTERVAL'])

# Init DB client
db.start(config['DATABASE']['DB_NAME'], config['DATABASE']['DB_USERNAME'], config['DATABASE']['DB_PASSWORD'],
                config['DATABASE']['DB_HOST'], config['DATABASE']['DB_PORT'], config['DATABASE']['DB_AUTHDB'])
         
# Start Tron API
tron = Tron(full_node=config['API']['FULL_NODE'],
        solidity_node=config['API']['SOLIDITY_NODE'],
        event_server=config['API']['EVENT_SERVER'])

track_list = config['TRACK']['ADDRESSES'].split(',')


def run_sync(bInit, bEnd):
        
    for n in range(bInit, bEnd+1):
        logging.info('Downloading Block...')
        block = tron.trx.get_block(n)
        if 'transactions' not in block: continue
        # check all transactions
        for transaction in block['transactions']:
            if 'contract' not in transaction['raw_data']: continue
            # check all contracts in transaction
            for contract in transaction['raw_data']['contract']:
                # check if type is Transfer
                if contract['type'] in ['TransferContract','TransferAssetContract']:
                   #  check if contract has tracking addresses
                    if (
                        (tron.address.from_hex(contract['parameter']['value']['owner_address']).decode('utf-8') in  track_list) or
                        (tron.address.from_hex(contract['parameter']['value']['to_address']).decode('utf-8') in track_list)
                        ):
                        logging.info('Adding')
                        transfers.addToTransfers(
                            tron.address.from_hex(contract['parameter']['value']['owner_address']).decode('utf-8'),
                            tron.address.from_hex(contract['parameter']['value']['to_address']).decode('utf-8'),
                            contract['parameter']['value']['amount'],
                            'TRX' if contract['type']=='TransferContract' else tron.toText(contract['parameter']['value']['asset_name']),
                            block['block_header']['raw_data']['timestamp'],
                            block['block_header']['raw_data']['number'],
                            tron.toText(transaction['raw_data']['data']) if 'data' in transaction['raw_data'] else "",
                            transaction['txID']
                        )
                        
                   

async def main():
    # run main loop
    while True:
        try:
            # get last block
            lastBlock = getLastBlockNum()
            lastBDBlock = info.get('last_block')
            if lastBDBlock is None:
                lastBDBlock = Int64(0)
            lastBDBlock += 1
            if lastBDBlock<lastBlock:
                if (lastBDBlock+Int64(config['DEFAULT']['BATCH']))<lastBlock: lastBlock = lastBDBlock+Int64(config['DEFAULT']['BATCH'])
                logging.info('Checking data from block {} to {}...'.format(lastBDBlock, lastBlock ))
                run_sync(lastBDBlock, lastBlock)
                info.set('last_block', lastBlock)
            else:
                logging.info('DB is in sync, waiting {}s'.format(checkPing))
                await asyncio.sleep(checkPing) 

        except KeyboardInterrupt:
            logging.error("Interrupted!")
            break
        except:
            logging.error("Unexpected error:", sys.exc_info()[0])
            # Stop scrip... cant continue sync if found an error... 
            sys.exit(1)

def getLastBlockNum():
    lastBlock = tron.trx.get_latest_blocks()
    return lastBlock[0]['block_header']['raw_data']['number']

if __name__ == "__main__":
    if results.clear:
        logging.info('Deleting all database...')
        db.deleteAll()
        db.createIndex()
        logging.info('Database deleted!')

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())  
    
logging.info('App closed...')
