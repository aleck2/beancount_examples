SELECT 
  account, sum(cost(position)) as total
FROM
  NOT HAS_ACCOUNT('Expenses:Sole-Prop')
WHERE
  YEAR(date) = year(today())
  AND account ~ 'Assets:Sole-Prop:Inventory'
