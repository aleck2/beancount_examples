SELECT 
  account, sum(cost(position)) as total
FROM
  NOT HAS_ACCOUNT('Assets:Checking')
  AND NOT HAS_ACCOUNT('Income')
WHERE
  year(date) = year(today())
  AND account ~ 'Liabilities:Credit-cards:.*'
