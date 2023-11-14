SELECT 
  account, sum(cost(position)) as total
FROM
  HAS_ACCOUNT('Liabilities:Credit-cards')
  AND NOT HAS_ACCOUNT('Income')
  AND NOT HAS_ACCOUNT('Assets:Checking')
  AND NOT HAS_ACCOUNT('Assets:Reimbursable')
  AND NOT HAS_ACCOUNT('Expenses:Taxes')
  AND NOT HAS_ACCOUNT('Liabilities:Taxes')
  AND NOT HAS_ACCOUNT('Expenses:Work:Churning:Tax.*')
  AND NOT HAS_ACCOUNT('Expenses:Work:Churning:CC.*')
WHERE
  year(date) = year(today())
  AND account ~ '^((?!Liabilities:Credit-cards).)*$'
