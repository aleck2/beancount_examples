# TODO clean this up
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
from beancount.core.position import Cost, CostSpec
from beancount.ingest import importer

from enum import Enum

SKU_MAPPINGS = {
        'aarke1LWatterBottle': 'UNQ',
}

class TransactionImporter(importer.ImporterProtocol):

    def __init__(self, account, last_four):
        self.account = account
        self.last_four = last_four


    def file_account(self, _):
        return self.account


    def identify(self, f):
        return re.match(".*CustomTransaction\.csv$", os.path.basename(f.name), re.IGNORECASE)


    def extract(self, f):
        entries = []

        with open(f.name, 'r', encoding='utf-8-sig') as f:
            for _ in range(7): # skip first 7 lines
                f.readline()

            for index, row in enumerate(csv.DictReader(f)):
                trans = {}
                # logging.error("%s", row)

                datetime_str = row['date/time'] # trim last 4 characters
                trans['date'] = parse(datetime_str) # Amazon uses Seattle timezone
                trans['trans_type'] = row['type'] 
                trans['sku'] = row['sku']
                trans['desc']  = row['description']
                trans['order_state']  = row['order state'].upper()
                trans['quantity']  = D(row['quantity'])
                trans['product_sales'] = D(row['product sales'])
                trans['shipping_credits'] = D(row['shipping credits'])
                trans['promotional_rebates'] = D(row['promotional rebates'])
                trans['marketplace_withheld_tax'] = D(row['marketplace withheld tax'])
                trans['selling_fees'] = D(row['selling fees']) + D(row['other transaction fees'])
                trans['fba_fees'] = D(row['fba fees'])
                trans['other_fees'] = D(row['other'])
                trans['total'] = D(row['total'])

                # create metadata posting with order state code (for sales tax processing)
                meta = data.new_metadata(f.name, index, {'order_state': trans['order_state']})

                postings = self.create_transaction_postings(trans)

                txn = data.Transaction(
                    meta=meta,
                    date=trans['date'],
                    flag=flags.FLAG_OKAY,
                    payee=trans['trans_type'],
                    narration=trans['desc'],
                    tags=set(),
                    links=set(),
                    postings=postings
                )

                entries.append(txn)

        return entries


    # TODO create flag to treat like normal or override with +/- multiplier
    def create_posting(self, account_name, posting_amount, currency):
        """
        In Amazon records:
            Positive records indicate money to user
            Negative records indicate money from user

        Returns:
         data.posting
        """
        # Assets (debit) always sign kept as-is

        account_type = account_name.split(":")[0]

        # Expenses (credit) always sign reverse
        if account_type == 'Expenses':
            posting_amount *= -1

        # Income (credit) is mostly sign reversed
        # *Exception* for MFT accounts. Collected MFT credits Income; refunded MFT debits Income
        elif account_type == 'Income':
            if 'MFT' not in account_name:
                posting_amount *= -1

        # TODO break off this logic into its own function
        if currency != 'USD':
            cost = Cost(None, 'USD', None, None) 
            # to get cost of {0 USD}
            # currency = 'USD'
            # cost_spec = CostSpec(D(0), None, 'USD', None, None, None) # to get cost of {0 USD}

        else: 
            cost = None


        return data.Posting(account_name, amount.Amount(posting_amount, currency), cost, None, None, None)


    # return list of postings
    def create_transaction_postings(self, trans):
        trans_type = trans['trans_type']

        if trans_type == 'Adjustment':
            postings_to_create = self.get_adjustment_postings(trans)

        elif trans_type == 'FBA Inventory Fee':
            postings_to_create =  self.get_fba_inventory_postings(trans)

        elif trans_type == 'Order':
            postings_to_create =  self.get_order_postings(trans)

        elif trans_type == 'Refund':
            postings_to_create =  self.get_refund_postings(trans)

        elif trans_type == 'Service Fee':
            postings_to_create =  self.get_service_fee_postings(trans)

        elif trans_type == 'Shipping Services':
            postings_to_create =  self.get_shipping_service_postings(trans)

        elif trans_type == 'FBA Customer Return Fee': # new as of 2023-10, all zero dollar transactions, not sure where to post these to
            postings_to_create =  self.get_fba_inventory_postings(trans)

        # elif trans_type == 'Order_Retrocharge': # new as of 2023-10, rare but log against MFT, not positive where to post these to
        #     postings_to_create =  self.get_mft_postings(trans)
        # I think retrocharge is when Amazon refunds a customer right away provided they send the item back within 30 days after and the customer never ends up sending it back Amazon recharges the buyer then.


        else:
            postings_to_create = []
            logging.error("invalid trans_type %s", trans_type)

        postings = []

        for posting in postings_to_create:
            if abs(posting[1]) == D(0):
                continue

            # TODO clean up this currency mess
            if len(posting) == 2:
                currency = 'USD'

            else:
                currency = posting[2]

            postings.append( self.create_posting(posting[0], posting[1], currency) )


        return postings


    def get_order_postings(self, trans):
        postings = [ 
            ('Assets:Sole-Prop:Accounts:Amazon', trans['product_sales'] +
                trans['shipping_credits']+trans['promotional_rebates']+trans['selling_fees']+trans['fba_fees']),
            ('Income:Sole-Prop:Gross:Amazon:Sales', trans['product_sales']),
            ('Income:Sole-Prop:Gross:Amazon:Shipping-credits', trans['shipping_credits']),
            ('Income:Sole-Prop:Gross:Amazon:Promotional-rebates', trans['promotional_rebates']),
            ('Expenses:Sole-Prop:Amazon:Seller-fees', trans['selling_fees']),
            ('Expenses:Sole-Prop:Amazon:FBA-fees', trans['fba_fees']),
            # ('Assets:Sole-Prop:Accounts:Amazon', trans['selling_fees']+trans['fba_fees']),
            ('Income:Sole-Prop:Gross:Amazon:MFT', trans['marketplace_withheld_tax']),
            ('Expenses:Sole-Prop:MFT:Amazon', trans['marketplace_withheld_tax'])]

        # TODO break this into its own function
        if trans['sku'] in SKU_MAPPINGS:
            currency = SKU_MAPPINGS[trans['sku']]
            account_name = ':'.join( ['Assets:Sole-Prop:Inventory', currency] )
            postings.append( (account_name, -1 * trans['quantity'], currency) )
            account_name = ':'.join( ['Expenses:Sole-Prop:COGS', currency] )
            postings.append( (account_name, -1 * trans['quantity'], currency) )
        else:
            logging.error('%s - sku not recorgnized' % (trans['sku']))


        return postings


    def get_refund_postings(self, trans):
        postings = [ 
            ('Assets:Sole-Prop:Accounts:Amazon', trans['product_sales'] +
                trans['shipping_credits']+trans['promotional_rebates']+trans['selling_fees']+trans['fba_fees']),
            ('Income:Sole-Prop:Returned:Amazon:Sales', trans['product_sales']),
            ('Income:Sole-Prop:Returned:Amazon:Shipping-credits', trans['shipping_credits']),
            ('Income:Sole-Prop:Returned:Amazon:Promotional-rebates', trans['promotional_rebates']),
            ('Expenses:Sole-Prop:Amazon:Seller-fees', trans['selling_fees']),
            ('Expenses:Sole-Prop:Amazon:FBA-fees', trans['fba_fees']),
            # ('Assets:Sole-Prop:Accounts:Amazon', trans['selling_fees']+trans['fba_fees']),
            ('Income:Sole-Prop:Returned:Amazon:MFT', trans['marketplace_withheld_tax']),
            ('Expenses:Sole-Prop:MFT:Amazon', trans['marketplace_withheld_tax'])]

        # TODO break this into its own function
        if trans['sku'] in SKU_MAPPINGS:
            currency = SKU_MAPPINGS[trans['sku']]
            account_name = ':'.join( ['Assets:Sole-Prop:Inventory', currency] )
            account_name += ':Priority'
            postings.append( (account_name, trans['quantity'], currency) )
            account_name = ':'.join( ['Expenses:Sole-Prop:COGS', currency] )
            postings.append( (account_name, trans['quantity'], currency) )
        else:
            logging.error(trans['sku'])

        return postings


    def get_shipping_service_postings(self, trans):
        postings = [ 
            ('Assets:Sole-Prop:Accounts:Amazon', trans['total']),
            ('Expenses:Sole-Prop:Amazon:Shipping', trans['total'])]

        return postings


    def get_service_fee_postings(self, trans):
        postings = [ 
            ('Assets:Sole-Prop:Accounts:Amazon', trans['total']),
            ('Expenses:Sole-Prop:Amazon:Subscription-fees', trans['total'])]

        return postings


    def get_fba_inventory_postings(self, trans):
        postings = [ 
            ('Assets:Sole-Prop:Accounts:Amazon', trans['total']),
            ('Expenses:Sole-Prop:Amazon:FBA-fees', trans['total'])]

        return postings


    def get_adjustment_postings(self, trans):

        # if positive, it's a refund. if negative, it's a special 'adjustment' expense
        if trans['total'] >= 0:
            postings = [ 
                ('Assets:Sole-Prop:Accounts:Amazon', trans['total']),
                ('Income:Sole-Prop:Returned:Amazon:FBA-inventory-credits', trans['total'])]

        else:
            postings = [ 
                ('Assets:Sole-Prop:Accounts:Amazon', trans['total']),
                ('Expenses:Sole-Prop:Amazon:Adjustments', trans['total'])]

        return postings
