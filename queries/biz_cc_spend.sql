SELECT 
  sum(cost(position)) as total
FROM
  HAS_ACCOUNT('Assets:Sole-Prop')
  AND NOT HAS_ACCOUNT ('Expenses:Sole-Prop:COGS')
WHERE
  year(date) = year(today())
  AND account ~ 'Liabilities:Credit-cards' 
