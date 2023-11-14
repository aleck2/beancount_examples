import csv
import datetime
import os
import re

from dateutil.parser import parse

from beancount.core.number import D
from beancount.core.number import ZERO
from beancount.core import data
from beancount.core import account
from beancount.core import amount
from beancount.core import flags
from beancount.core.position import Cost
from beancount.ingest import importer

# Use "Download Account Activity" from main Chase.com page
# Keep default filename
# Input file has following columns:
# Posted Date Reference Number Payee Address Amount

class CreditCardImporter(importer.ImporterProtocol):
    def __init__(self, account, last_four):
        self.account = account
        self.last_four = last_four

    def file_account(self, _):
        return self.account

    def file_date(self, f):
        filename = os.path.basename(f.name)
        closing_date = parse(filename.split('_')[2])
        return closing_date

    def identify(self, f):
        return re.match(''.join(['.*Chase.*', str(self.last_four), '.*\.csv$']), os.path.basename(f.name), re.IGNORECASE)

    def extract(self, f):
        entries = []
        with open(f.name) as f:
            for index, row in enumerate(csv.DictReader(f)):
                trans_date = parse(row['Transaction Date']).date()
                trans_desc = row['Description'] 
                trans_amt  = row['Amount']
                trans_memo = row['Memo']
                # trans_category = row['Category']

                # kv_dict = {'category': trans_category}
                if re.match('\S', trans_memo):
                    kv_dict['memo'] = trans_memo

                # meta = data.new_metadata(f.name, index, kv_dict)
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
                        'USD'), None, None, None, None))
                # txn.postings.append(
                #     data.Posting('Expenses:', -amount.Amount(D(trans_amt),
                #         'USD'), None, None, None, None))
                # txn.postings.append(
                #         data.Posting('Expenses:Sole-Prop', amount.Amount(D(1),
                #         'WIDGET'), Cost(D(trans_amt), 'USD', None, None), None, None, None))

                entries.append(txn)

        return entries
