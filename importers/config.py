import os, sys

# beancount doesn't run from this directory
sys.path.append(os.path.dirname(__file__))

# importers located in the importers directory

import amazon, amex, barclays, bofa, chase, ebay, merrill, wells

CONFIG = [
        # for first argument: put account name; for second arg: put last 4 digits of account
        amazon.TransactionImporter('Assets:Sole-Prop:Payable:Amazon', '0000'),
        amex.PlatinumImporter('Liabilities:Credit-cards:Amex:Platinum', '0001'),
        amex.GoldImporter('Liabilities:Credit-cards:Amex:Gold', '0002'),
        barclays.CreditCardImporter('Liabilities:Credit-cards:Barclays:Business-Aviator', '0003'),
        bofa.BankImporter('Assets:Checking:BofA:0004', '0004'),
        bofa.CreditCardImporter('Liabilities:Credit-cards:BofA:Customized-Rewards', '0005'),
        bofa.CreditCardImporter('Liabilities:Credit-cards:BofA:Premium-Rewards', '0006'),
        chase.CreditCardImporter('Liabilities:Credit-cards:Chase:British', '0007'),
        chase.CreditCardImporter('Liabilities:Credit-cards:Chase:Biz-Ink-Unlimited', '0008'),
        chase.CreditCardImporter('Liabilities:Credit-cards:Chase:Freedom-Flex', '0009'),
        ebay.TransactionImporter('bs', '0000'),
        merrill.TransactionImporter('Assets:Investments', '4X82'),
        wells.CreditCardImporter('Liabilities:Credit-cards:Wells-Fargo:Active-Cash', '0010'),
]
