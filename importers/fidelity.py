import csv
import os
import re
import logging
from dateutil.parser import parse

from decimal import Decimal
from beancount.core.number import D
from beancount.core.number import ZERO
from beancount.core import data
from beancount.core import account
from beancount.core import amount
from beancount.core import flags
from beancount.core.position import Cost
from beancount.ingest import importer

from enum import Enum


class BrokerageImporter(importer.ImporterProtocol):
    """
    Simple Fidelity importer for someone who uses brokerage as a checking account (because of SPAXX as default core position)
    
    If buying commodities, tweak this to accomodate symbol, quantity, price, and description cols
    """
    def __init__(self, account, last_four):
        self.account = account
        self.last_four = last_four


    def file_account(self, _):
        return self.account


    def identify(self, f):
        return re.match(''.join(['History_for_Account_Z.*', self.last_four, '\.csv$']), os.path.basename(f.name))


    def extract(self, f):
        entries = []

        # Trade Date, Settlement Date, Account, Description, Type, Symbol/ CUSIP, Quantity, Price, Amount
        with open(f.name) as f:
            for _ in range(2): # skip first 2 lines
                f.readline()

            for index, row in enumerate(csv.DictReader(f)):

                # terminate at footer text
                try:
                    trade_date = parse(row['Run Date']).date()
                except:
                    break

                action  = row['Action']
                trans_amt  = row['Amount ($)']


                meta = data.new_metadata(f.name, index)

                txn = data.Transaction(
                    meta=meta,
                    date=trade_date,
                    flag=flags.FLAG_OKAY,
                    payee=action,
                    narration='',
                    tags=set(),
                    links=set(),
                    postings=[],
                )

                txn.postings.append(
                    data.Posting(self.account, amount.Amount(D(trans_amt), 'USD'), None, None, None, None)
                )

                entries.append(txn)

        return entries
