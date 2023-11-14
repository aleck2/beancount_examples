SELECT 
  account, sum(cost(position)) as total
FROM
  NOT HAS_ACCOUNT('Income')
  AND (HAS_ACCOUNT('Assets:Sole-Prop:.*Inventory') OR HAS_ACCOUNT('Expenses:Sole-Prop'))
WHERE
  year(date) = year(today())
  AND account ~ '^((?!Liabilities:Credit-cards).)*$'
  AND account ~ '^((?!Assets:Checking).)*$'
  AND account ~ '^((?!Assets:Cash).)*$'
ORDER BY
  account
