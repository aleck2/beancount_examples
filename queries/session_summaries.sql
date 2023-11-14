SELECT 
  links, sum(cost(position)) as total
FROM
  year(date) = year(today())
WHERE
  (account ~ 'Income:.*:Betting' OR account ~ 'Expenses:.*:Betting')
