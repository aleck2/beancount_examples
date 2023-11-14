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
        return re.match(''.join(['.*merrill.*', '\.csv$']), os.path.basename(f.name))


    def extract(self, f):
        entries = []

        # Trade Date, Settlement Date, Account, Description, Type, Symbol/ CUSIP, Quantity, Price, Amount
        with open(f.name) as f:
            for index, row in enumerate(csv.DictReader(f)):
                trade_date = parse(row['Trade Date ']).date()
                account = row['Account ']
                description  = row['Description ']
                symbol  = row['Symbol/ CUSIP ']
                quantity  = row['Quantity ']
                price  = row['Price ']
                trans_amt  = row['Amount ']
                trans_amt = re.sub('[$]', '', trans_amt)

                action = description.split(' ')[0]

                meta = data.new_metadata(f.name, index)

                if action == 'Purchase':
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

                if re.match('^CMA-.*', account, re.IGNORECASE):
                    income = 'Income:Investing:Taxable:?-term'
                    extension = ':Brokerage:Merrill'

                else:
                    income = 'Income:Investing:Tax-advantaged'
                    if re.match('^Roth.*', account, re.IGNORECASE):
                        extension = ':Tax-advantaged:Roth:Merrill'
                    else:
                        extension = ':Tax-advantaged:Trad:Merrill'


                if action == 'Buy':
                    txn.postings.append(
                            data.Posting(self.account + extension + ':Cash', amount.Amount(D(trans_amt), 'USD'), None, None, None, None))
                    txn.postings.append(
                            data.Posting(self.account + extension + ':' + symbol , amount.Amount(D(quantity), symbol + '{}'), None, None, None, None)
                    )
                elif action == 'Sale':
                    txn.postings.append(
                        data.Posting(self.account + extension + ':Cash', amount.Amount(D(trans_amt), 'USD'), None, None, None, None))
                    txn.postings.append(
                            data.Posting(self.account + extension + ':' + symbol , amount.Amount(D(quantity), symbol + '{}'), None, None, None, None)
                    )
                    txn.postings.append(
                            data.Posting(income, None, None, None, None, None)
                    )
                elif action == 'Dividend':
                    txn.postings.append(
                        data.Posting(self.account + extension + ':Cash', amount.Amount(D(trans_amt), 'USD'), None, None, None, None)
                    )
                    txn.postings.append(
                            data.Posting(income, None, None, None, None, None)
                    )

                entries.append(txn)

        return entries
