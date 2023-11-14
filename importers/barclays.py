import csv
import os
import re
import logging
from dateutil.parser import parse

from beancount.core.number import D
from beancount.core.number import ZERO
from beancount.core import data
from beancount.core import account
from beancount.core import amount
from beancount.core import flags
from beancount.core.position import Cost
from beancount.ingest import importer

from enum import Enum

# Posted Date Reference Number Payee Address Amount

class CreditCardImporter(importer.ImporterProtocol):
    def __init__(self, account, last_four):
        self.account = account
        self.last_four = last_four


    def file_account(self, _):
        return self.account


    def identify(self, f):
        #return re.match(r'^CreditCard.*\.csv', os.path.basename(f.name))
        # used to be called uber card, that's why I use this filename
        return re.match(r'.*uber.*\.csv', os.path.basename(f.name))


    # Expect format: March2021_last4.csv
    def file_date(self, f):
        filename = os.path.basename(f.name)
        date_str = ''.join([filename.split('_')[0], '15']) # assume statement date always on 15 (not working)

        return parse(date_str)


    def extract(self, f):
        entries = []

        with open(f.name) as f:
            for i in range(4): # skip first 4 lines
                f.readline()

            for index, row in enumerate(csv.DictReader(f)):
                trans_date = parse(row['Transaction Date']).date()
                trans_desc = row['Description']
                trans_amt  = row['Amount']

                meta = data.new_metadata(f.name, index)

                txn = data.Transaction(
                    meta=meta,
                    date=trans_date,
                    flag=flags.FLAG_OKAY,
                    payee=trans_desc,
                    narration="",
                    tags=set(),
                    links=set(),
                    postings=[],
                )

                txn.postings.append(
                    data.Posting(self.account, amount.Amount(D(trans_amt),
                        'USD'), None, None, None, None)
                )

                if re.match('.*PAYPAL \*EBAYINCSHIP.*', trans_desc, re.IGNORECASE):
                    txn.postings.append(
                            data.Posting('Expenses:Sole-Prop:Ebay:Shipping', 
                                amount.Amount(-D(trans_amt), 'USD'), None, None, None, None))

                elif re.match('.*PAYPAL \*(USPOSTALSER|SHIPSTATION).*', trans_desc, re.IGNORECASE):
                    txn.postings.append(
                            data.Posting('Expenses:Sole-Prop:Amazon:Shipping', 
                                amount.Amount(-D(trans_amt), 'USD'), None, None, None, None))

                elif re.match('.*(PAYPAL[^( \*EBAYINCSHIP)]|MERCARI|EBAY O).*',
                        trans_desc, re.IGNORECASE):

                    txn.postings.append(
                            data.Posting('Assets:Sole-Prop:Inventory:TODO', amount.Amount(D(1),
                            'WIDGET {}'), None, None, None, None))

                entries.append(txn)

        return entries
