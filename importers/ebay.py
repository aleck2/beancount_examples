import csv
import os
import re
import logging
from dateutil.parser import parse
from dateutil.relativedelta import *

from beancount.core.number import D
from beancount.core.number import ZERO
from beancount.core import data
from beancount.core import account
from beancount.core import amount
from beancount.core import flags
from beancount.core.position import Cost
from beancount.ingest import importer

from enum import Enum

SKU_MAPPINGS = {}

# TODO: definitely add "claim"

class TransactionImporter(importer.ImporterProtocol):
    def __init__(self, account, last_four):
        self.account = account
        self.last_four = last_four


    def file_account(self, _):
        return self.account


    def identify(self, f):
        positive_match = re.match("^my_username.*\.csv$", os.path.basename(f.name), re.IGNORECASE)
        return positive_match


    # Order without item ID is a multi-line order
    def extract(self, f):
        entries = []

        with open(f.name) as f:
            for _ in range(11): # skip first lines
                f.readline()

            for index, row in enumerate(csv.DictReader(f)):

                trans = {}

                datetime_str = row['Transaction creation date']
                # convert into CST from PST
                trans['date'] = (parse(datetime_str) + relativedelta(hours=2)).date()
                # Populate trans dictionary using column headers in snake case and put them into appropriate
                # data formats
                trans['type'] = row['Type']
                trans['item_title'] = row['Item title']
                trans['order_number'] = row['Order number']
                trans['order_state'] = row['Ship to province/region/state']
                if trans['order_state'] == '--':
                    trans['order_state'] = ''
                trans['quantity'] = self.get_value(row, 'Quantity')
                trans['ebay_collected_tax'] = self.get_value(row, 'eBay collected tax')
                trans['net_amount'] = self.get_value(row, 'Net amount')
                trans['item_subtotal'] = self.get_value(row, 'Item subtotal')
                trans['final_value_fee_fixed'] = self.get_value(row, 'Final Value Fee - fixed')
                trans['final_value_fee_variable'] = self.get_value(row, 'Final Value Fee - variable')
                trans['international_fee'] = self.get_value(row, 'International fee')
                trans['gross_transaction_amount'] = self.get_value(row, 'Gross transaction amount')
                trans['description'] = row['Description']

                meta = data.new_metadata(f.name, index)
                postings = self.create_transaction_postings(trans)

                meta = data.new_metadata(f.name, index, {'order_state': trans['order_state']})

                txn = data.Transaction(
                    meta=meta,
                    date=trans['date'],
                    flag=flags.FLAG_OKAY,
                    payee=trans['type'],
                    narration=trans['item_title'],
                    tags=set(),
                    links=set(),
                    postings=postings
                )

                entries.append(txn)


        return entries


    def get_value(self, data, column_title):

        value = data[column_title]

        if value == '--':
            return 0

        return D(value)


    def handle_multi_order(self, trans):
        return


    # return list of postings
    def create_transaction_postings(self, trans):
        trans_type = trans['type']


        # # parent of multiple posting Order
        # if trans['type'] == '--' and trans['item_id'] == '--':
        #     self.handle_multi_order(trans)

        #     return

        # hacky guard against multi-item orders
        if trans_type == 'Order' and trans['final_value_fee_variable'] != 0:
            return self.create_single_item_order_postings(trans)

        elif trans_type == 'Refund':
            return self.create_refund_postings(trans)

        elif trans_type == 'Shipping label':
            return self.create_shipping_service_postings(trans)

        elif trans_type == 'Other fee' and re.match('^Ad fee.*', trans['description'], re.IGNORECASE):
            return self.create_ad_fee(trans)

        logging.error("invalid trans_type %s (maybe multi-order?)", trans_type)

        return []


    def create_postings(self, posting_dict):

        postings = []
        for account_name, value in posting_dict.items():
            if isinstance(value, amount.Amount):
                postings.append( data.Posting(account_name, value, None, None, None, None))

            elif value != 0:
                postings.append( data.Posting(account_name, amount.Amount(value, 'USD'), None, None, None, None))
                # data.Posting('Assets:Sole-Prop:Inventory:TODO', amount.Amount(D(1),
                # 'TODO'), Cost(None, 'USD', None, None), None, None, None))

        return postings


    def create_ad_fee(self, trans):

        posting_dict = {
                'Assets:Sole-Prop:Accounts:Ebay' :  trans['net_amount'],
                'Expenses:Sole-Prop:Ebay:Ad-fees' : -1 * trans['net_amount'],
                }

        return self.create_postings(posting_dict)


    def create_single_item_order_postings(self, trans):

        posting_dict = {
                'Assets:Sole-Prop:Accounts:Ebay' : trans['net_amount'],
                'Income:Sole-Prop:Gross:Ebay:Sales' : -1 * trans['gross_transaction_amount'],
                'Expenses:Sole-Prop:Ebay:Seller-fees' : -1 * (trans['final_value_fee_fixed'] +
                    trans['final_value_fee_variable'] + trans['international_fee']),
                'Income:Sole-Prop:Gross:Ebay:MFT' : -1 * trans['ebay_collected_tax'],
                'Expenses:Sole-Prop:MFT:Ebay' : trans['ebay_collected_tax'],
                }

        if re.match('.*widget_name1.?', trans['item_title'], re.IGNORECASE):
            posting_dict['Assets:Sole-Prop:Inventory:WIDGET1'] = amount.Amount(D(-1 * trans['quantity']), 'WIDGET1 {USD}')
            posting_dict['Expenses:Sole-Prop:COGS:WIDGET1'] = amount.Amount(D(trans['quantity']), 'WIDGET1 {USD}')

        if re.match('.*widget_name2.?', trans['item_title'], re.IGNORECASE):
            posting_dict['Assets:Sole-Prop:Inventory:WIDGET2'] = amount.Amount(D(-1 * trans['quantity']), 'WIDGET2 {USD}')
            posting_dict['Expenses:Sole-Prop:COGS:WIDGET2'] = amount.Amount(D(trans['quantity']), 'WIDGET2 {USD}')

        return self.create_postings(posting_dict)


    def create_shipping_service_postings(self, trans):

        posting_dict = {
                'Expenses:Sole-Prop:Ebay:Shipping' : -1 * trans['gross_transaction_amount'],
                'Assets:Sole-Prop:Accounts:Ebay' : trans['gross_transaction_amount'],
                }

        return self.create_postings(posting_dict)


    def create_refund_postings(self, trans):

        posting_dict = {
                'Assets:Sole-Prop:Accounts:Ebay' : trans['net_amount'],
                'Income:Sole-Prop:Returned:Ebay:Sales' : -1 * trans['gross_transaction_amount'],
                'Expenses:Sole-Prop:Ebay:Seller-fees' : -1 * (trans['final_value_fee_fixed'] +
                    trans['final_value_fee_variable']),
                'Income:Sole-Prop:Returned:Ebay:MFT' : -1 * trans['ebay_collected_tax'],
                'Expenses:Sole-Prop:MFT:Ebay' : trans['ebay_collected_tax'],
                }

        # if re.match('.*widget.?1', trans['item_title'], re.IGNORECASE):
        #     posting_dict['Assets:Sole-Prop:Inventory:WIDGET1:Priority'] = 1
        #     posting_dict['Expenses:Sole-Prop:COGS:WIDGET1'] = -1

        # if re.match('.*widget.?2', trans['item_title'], re.IGNORECASE):
        #     posting_dict['Assets:Sole-Prop:Inventory:WIDGET2:Priority'] = 1
        #     posting_dict['Expenses:Sole-Prop:COGS:WIDGET2'] = -1

        return self.create_postings(posting_dict)
