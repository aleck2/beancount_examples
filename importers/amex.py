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

# TODO make a base class that inherits ImporterProtocol and make that base class for both import classes

# Note: Amex reverses sign on its transactions!
class PlatinumImporter(importer.ImporterProtocol):
    def __init__(self, account, last_four):
        self.account = account
        self.last_four = last_four

    def file_account(self, _):
        return self.account

    def identify(self, f):
        return re.match('.*amex.*platinum.*\.csv$', os.path.basename(f.name), re.IGNORECASE)

    def extract(self, f):
        entries = []
        # Date,Description,Card Member,Account #,Amount,Extended Details,Appears On Your Statement As,Address,City/State,Zip Code,Country,Reference,Category
        with open(f.name) as f:
            for index, row in enumerate(csv.DictReader(f)):
                trans_date = parse(row['Date']).date()
                trans_desc = row['Description'] 
                trans_desc = re.sub(' +', ' ', trans_desc)
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
                    data.Posting(self.account, amount.Amount(-D(trans_amt),
                        'USD'), None, None, None, None)
                )

                if re.match('.*(PAYPAL[^(\*EBAYINCSHIP)]|MERCARI|EBAY O).*',
                        trans_desc, re.IGNORECASE):
                    txn.postings.append(
                            data.Posting('Assets:Sole-Prop:Inventory:TODO', amount.Amount(D(1),
                            'TODO {}'), None, None, None, None))
                

                entries.append(txn)

        return entries

class GoldImporter(importer.ImporterProtocol):
    def __init__(self, account, last_four):
        self.account = account
        self.last_four = last_four

    def file_account(self, _):
        return self.account

    def identify(self, f):
        return re.match('.*amex.*gold.*\.csv$', os.path.basename(f.name), re.IGNORECASE)

    def extract(self, f):
        entries = []
        # Date,Description,Card Member,Account #,Amount,Extended Details,Appears On Your Statement As,Address,City/State,Zip Code,Country,Reference,Category
        # TODO add num: reference num
        with open(f.name) as f:
            for index, row in enumerate(csv.DictReader(f)):
                trans_date = parse(row['Date']).date()
                trans_desc = row['Description'] 
                trans_desc = re.sub(' +', ' ', trans_desc)
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
                    data.Posting(self.account, amount.Amount(-D(trans_amt),
                        'USD'), None, None, None, None)
                )

                if re.match('.*PAYPAL \*EBAYINCSHIP.*', trans_desc, re.IGNORECASE):
                    txn.postings.append(
                            data.Posting('Expenses:Sole-Prop:Ebay:Shipping', 
                                amount.Amount(-D(trans_amt), 'USD'), None, None, None, None))

                elif re.match('.*PAYPAL .USPOSTALSER.*', trans_desc, re.IGNORECASE):
                    txn.postings.append(
                            data.Posting('Expenses:Sole-Prop:Amazon:Shipping', 
                                amount.Amount(-D(trans_amt), 'USD'), None, None, None, None))

                elif re.match('.*(PAYPAL[^(\*EBAYINCSHIP)]|MERCARI|EBAY O).*',
                        trans_desc, re.IGNORECASE):
                    txn.postings.append(
                            data.Posting('Assets:Sole-Prop:Inventory:TODO', amount.Amount(D(1),
                            'TODO {}'), Cost(D(trans_amt), 'USD', None, None), None, None, None))
                

                entries.append(txn)

        return entries
