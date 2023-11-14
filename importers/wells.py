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

class CreditCardImporter(importer.ImporterProtocol):
    def __init__(self, account, last_four):
        self.account = account
        self.last_four = last_four


    def file_account(self, _):
        return self.account


    # Very important to distinguish cards from one another
    def identify(self, f):
        return re.match(''.join(['.*CreditCard.*', '\.csv$']), os.path.basename(f.name))


    # Expect format: March2021_last4.csv
    # def file_date(self, f):
    #     filename = os.path.basename(f.name)
    #     date_str = ''.join([filename.split('_')[0], '15']) # assume statement date always on 15 (not working)

    #     return parse(date_str)


    def extract(self, f):
        entries = []

        with open(f.name) as f:
            for row in csv.reader(f):
                trans_date = parse(row[0]).date()
                trans_desc = row[4]
                trans_amt  = row[1]


                txn = data.Transaction(
                    meta=data.new_metadata(f.name, 0),
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
                            'WIDGET2 {}'), None, None, None, None))

                entries.append(txn)

        return entries
