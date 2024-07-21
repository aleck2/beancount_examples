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

class TransactionImporter(importer.ImporterProtocol):
    def __init__(self, account, last_four):
        self.account = account
        self.last_four = last_four


    def file_account(self, _):
        return self.account


    def identify(self, f):
        return 'Account Activity Download.csv' == os.path.basename(f.name)


    def extract(self, f):
        entries = []

        with open(f.name) as f:
            symbol = 'VITSX' # TODO put you own ticker here

            for _ in range(4): # skip first 4 lines
                f.readline()

            for index, row in enumerate(csv.DictReader(f)):
                trade_date = parse(row['Activity Date']).date()
                action  = row['Category']
                trans_amt  = row['Amount'].replace('$', '')

                meta = data.new_metadata(f.name, index)

                if action == 'Investment Buy':
                    action = 'Buy'


                txn = data.Transaction(
                    meta=meta,
                    date=trade_date,
                    flag=flags.FLAG_OKAY,
                    payee=action,
                    narration=symbol,
                    tags=set(),
                    links=set(),
                    postings=[],
                )

                if action =='Employee Contribution':
                    continue;

                txn.postings.append(
                    data.Posting(self.account + ':Cash', amount.Amount(D(trans_amt), 'USD'), None, None, None, None))

                if action == 'Buy':
                    # via's shitty reporting doesn't give security quantity, so you have to manually fill this in
                    txn.postings.append(
                        data.Posting(self.account + f':{symbol}', -amount.Amount(D(1), symbol + '{}'), None, None, None, None)
                    )
                elif action == 'Account Interest':
                    txn.postings.append(
                            data.Posting('Income:Investing:Tax-advantaged', -amount.Amount(D(trans_amt), 'USD'), None, None, None, None)
                    )
                elif action =='Investment Fee':
                    txn.postings.append(
                            data.Posting('Expenses:Work:Bank-fees:Retirement', -amount.Amount(D(trans_amt), 'USD'), None, None, None, None)
                    )

                elif action =='Employer Contribution Incentive':
                    txn.postings.append(
                            data.Posting('Income:Career', -amount.Amount(D(trans_amt), 'USD'), None, None, None, None)
                    )

                entries.append(txn)

        return entries
