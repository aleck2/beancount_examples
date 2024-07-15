SELECT 
  account, sum(cost(position)) as total
FROM
  NOT HAS_ACCOUNT('Assets:Checking')
  AND NOT HAS_ACCOUNT('Income')
WHERE
  QUARTER(date) = QUARTER(today())
  AND account ~ 'Liabilities:Credit-cards:.*'
ORDER BY account
