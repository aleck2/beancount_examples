SELECT 
  root(account, 3), sum(cost(position)) as total
FROM
  year(date) = year(today())
WHERE
  account ~ 'Income:Sole-Prop:Gross|Income:Sole-Prop:Returned|Expenses:Sole-Prop'
ORDER BY root(account,3) DESC 
