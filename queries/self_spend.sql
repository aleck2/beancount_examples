SELECT 
  account, sum(cost(position)) as total
FROM
  HAS_ACCOUNT('Expenses:Self')
WHERE
  year(date) = year(today())
ORDER BY account ASC 
