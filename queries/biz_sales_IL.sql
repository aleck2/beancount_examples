SELECT
  month(date), account, sum(cost(position))
WHERE 
  year(date) = year(today())
  AND account ~ 'Income:Sole-Prop'
  AND ENTRY_META('order_state') ~ '^IL.*'
GROUP BY
  account, month(date)
