SELECT
  month(date), sum(cost(position)) as profit
WHERE 
  year(date) = year(today())
  AND 
  (account ~ 'Income:Sole-Prop'
  OR account ~ 'Expenses:Sole-Prop')
GROUP BY
  month(date)
