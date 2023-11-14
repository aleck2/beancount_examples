SELECT 
  account, sum(cost(position)) as total
FROM
  HAS_ACCOUNT('Expenses:Self')
  AND HAS_ACCOUNT('Liabilities:Credit-cards')
WHERE
  year(date) = year(today())
ORDER BY account ASC 
