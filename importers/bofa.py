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


    # Very important to distinguish bofa cards from one another
    def identify(self, f):
        return re.match(''.join(['.*', self.last_four, '\.csv$']), os.path.basename(f.name))


    # Expect format: March2021_last4.csv
    def file_date(self, f):
        filename = os.path.basename(f.name)
        date_str = ''.join([filename.split('_')[0], '15']) # assume statement date always on 15 (not working)

        return parse(date_str)


    def extract(self, f):
        entries = []

        with open(f.name) as f:
            for index, row in enumerate(csv.DictReader(f)):

                if row['Reference Number'].startswith('TEMPRE'):
                    continue

                trans_date = parse(row['Posted Date']).date()

                trans_desc = row['Payee']
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


class BankImporter(importer.ImporterProtocol):
    def __init__(self, account, last_four):
        self.account = account
        self.last_four = last_four


    def file_account(self, _):
        return self.account


    def identify(self, f):
        return re.match(''.join(['.*', self.last_four, '\.csv$']), os.path.basename(f.name))


    def file_date(self, f):
        filename = os.path.basename(f.name)
        date_str = filename.split('_')[1]

        return parse(date_str)


    # Date	Description	Amount	Running Bal.
    def extract(self, f):
        entries = []

        with open(f.name) as f:
            for i in range(6): # skip first 6 lines
                f.readline()

            for index, row in enumerate(csv.DictReader(f)):
                trans_date = parse(row['Date']).date()
                trans_desc = row['Description'] 
                trans_amt  = row['Amount']
                # logging.error("%s", row)

                # stop trailing backslash from escaping beancount quotes
                if trans_desc[-1] == "\\":
                    trans_desc = trans_desc.rstrip(trans_desc[-1])

                meta = data.new_metadata(f.name, index)

                # TODO make ebay payee = "transfer"
                # accomplish this by modifying trans_desc and creating txn after
                # classify_posting_accounts
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

                if re.match('^Interest Earned', trans_desc, re.IGNORECASE):
                    txn.postings.append(
                            data.Posting('Income:Investing:Taxable:Short-term', amount.Amount(-D(trans_amt), 'USD'),
                                None, None, None, None))


                posting_accounts = self.classify_posting_accounts(trans_desc)

                if posting_accounts:
                    for account in posting_accounts:
                        txn.postings.append(
                            data.Posting(account, None, None, None, None, None)
                        )

                entries.append(txn)

        return entries


    # Figure out if payment or expense involving Ebay and which account
    def classify_posting_accounts(self, trans_desc):

        # # Payment to Me
        if re.match("^(EBAY DES:EDI PYMNTS|eBay Inc).*", trans_desc):

            if self.is_business(trans_desc): # bofa update broke this, default to business
                return ('Assets:Sole-Prop:Accounts:Ebay',)

            return ('Expenses:Work:Selling:Seller-fees', 'Expenses:Work:Selling:Shipping', 'Income:Selling')

        # # Expense paid to Ebay
        # elif re.match("eBay Inc.*", trans_desc):
        #     if self.is_business(trans_desc):
        #         return 'Liabilities:Sole-Prop:Ebay:Payable'

        #     return 'Income:Selling'

        return None


    def is_business(self, trans_desc):
        if re.match('.*INDN:MY NAME.*', trans_desc):
            return False

        elif re.match('.*INDN\:MY FULL NAME.*', trans_desc):
            return True

        logging.error("is_business returns None, see %s", trans_desc)
        return True # default to business transaction
