# Useful Queries (for me)

I've used some of these queries over the years. They may make more sense for my particular account tree and my preferences, but they may help you get a better sense of how to use BQL.  
  
Last I checked, there are no ways to add comments to BQL, so I'm including short summaries of some of the queries here.  
  
## misc notes
sum(cost(position)) just takes the value of the corresponding posting, not the entire transaction  
  
Use negative lookaheads in regex to filter these postings
eg:
```
  WHERE
    account ~ '^((?!Liabilities:Credit-cards).)*$'
    AND account ~ '^((?!Assets:Checking).)*$'
    AND account ~ '^((?!Assets:Cash).)*$'  
```  

How to run bean-query  
```
cat ./total_cc_spend_per_period.sql | bean-query ~/Documents/financial/beancount/my_ledger.bean
```
  
# Queries
## session_summaries.sql
Summarize multiple transactions per link

## biz_spend.sql
  get all spending for sole-prop by non-spend source categories

  Does not double count Assets -> COGS because it excludes transactions with Income accounts
  -false

## total_cc_non_tax_spend
Calculate all credit card spending for the year but exclude tax payments and the corresponding tax processing fees made with credit cards.  
Whenever I make a tax payment, it includes a posting with Expenses:Taxes or Liabilities:Taxes. My ```from``` clause excludes transactions with any of those postings  
I am excluding transactions that match ```Assets:Checkings``` and ```Income``` because I want to exclude transactions that pay-off credit cards and also exclude income from credit card cash back/points.

## total_cc_spend.sql
Calculate spend on cc by excluding payoffs and cash back  
Include refunds  

Note: this query along with other "total*" queries will exclude any transactions that were partially split between credit card(s) and an excluded account like "Assets:Checking"  

## tax_churn_profit.sql
Measure total profit from paying off taxes with credit card  
  
At present, paying quarterly federal taxes with a credit card has a 1.87% fee. You may be able to make a profit by paying quarterly taxes with a credit card compared to an other funding source. Additionally, you can make money from the extra few weeks of interest-free financing offered by a credit card.  
  
I log each transaction concering a quarterly tax payment, property tax payment, state tax payment with a specific link like ```^tax-2023-q1``` and log the appropriate postings. When I receive the corresponding cash back for that transaction, I tag the cash back transaction with the same link from the tax payment and split the income postings to reflect how much of that cash back was from tax churning (as opposed to normal spend). You could apply this same link to any interest income from the extra free float provided by the credit card to get a better idea of your profit from this scheme. So, this query gives a summary of how much you make per tax payment.  
  
Assuming you're not deducting the processing fees and paying your appropriate amount of tax, this is likely not taxable income but I'm a lazy coder and not a tax person, so idk. Pay your taxes - if you can figure out how much you actually owe. [See also] (https://www.flyertalk.com/forum/american-express-membership-rewards/2059711-wsj-amex-pitched-biz-customers-tax-break-doesn-t-add-up.html)
