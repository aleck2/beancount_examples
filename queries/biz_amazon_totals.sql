SELECT 
  sum(cost(position)) as total
FROM
  NOT HAS_ACCOUNT('Assets:Checking')
  AND NOT HAS_ACCOUNT('Liabilities')
WHERE
  year(date) = year(today())
  AND account ~ 'Assets:Sole-Prop:Accounts:Amazon'
