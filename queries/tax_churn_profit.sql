SELECT
  links, sum(cost(position))
WHERE 
  account ~ "Income:Churning:Tax|Expenses:Work:Churning:Tax"
GROUP BY
  links
