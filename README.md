# My Beancount Set-Up
After removing some sensitive personal info (hopefully), I have exported my beancount utility files here to help others get started with beancount.  
  
Beancount is an open-sourced double-entry accounting system based on plain text data.
  
When I started my small side-gig in college, I wasted so much time trying to figure out how taxes work and how to bookkeep appropriately, The side-gig initially focused on reselling used products from eBay and other marketplace sites. Holding inventory posed multiple challenges from an accounting perspective and beancount helped simplify things substantially. Some of my challenges:
-- How to account for inventory with non uniform costs and deduct the unique cost of an inventory lot when making a sale (cash or accrual; FIFO or LIFO)  
-- How to quickly import hundreds of transactions? GUI based accounting systems like GNU Cash and Quickbooks took way too much time  
-- This was very much a side-gig and I did not want to pay big bucks for an accounting program  
  
I found double-entry especially blissful because I was previously relying on spotty PayPal and eBay exports where an easy to make mistake could result in me misreporting earnings and paying an incorrect tax amount (eBay has since redone their reporting and payment system).  
  
With double-entry accounting, I can verify my personal balance sheet against official financial statements. This makes it very easy to spot an error with my bookkeeping and ensures I have truthfully represented my finances within beancount. The bliss this inspires is should not be underestimated! Beancount lets me narrow down the search range to find any discrapancies that emerge as a result of bookkeeping mistakes. Moreover, I can impose "balance assertions" on any accounts across various points in time, so if I ever mistakenly delete or modify a transaction, the balance assertion will fail and alert me. Additionally, plaintext makes revision control easy with Git, so I can better maintain changes.  
  
Even if you are soley an employee, you may find a financial management software beyond Excel helpful. The ability to track networth and various sources of income (investments, side work, gifts, sign-up bonuses) along with track retirement account contributions can be invaluable. The US tax system is quite... something. If you engage in any number of retirement account maneuvers like a backdoor conversion, you may be required to keep documentation supporting that move until retirement. Beancount gives you an excellent platform to retain records over decades in a non-proprietary format in support of your future retirement.

Recently, personal finance tracking app Mint was acquired by Credit Karma leaving users in jeopardy of losing their years of tracking history. I understand a data transfer tool was made available but there were issues. I have no such qualms about Beancount given that I host my own data. The permanence of this format is very attractive.  
  
Keeping your personal ledger may take a lot of time depending on your situation. Importers easily allow you to convert CSV format into Beancount format. I have provided mine to help speed-up your transition. Some people won't like manually exporting their data into CSV and then manually categorizing transactions. There is a tool that uses AI/ML to auto categorize postings, but there is no free tool for mass exporting financial data. There is a paid tool called [Tiller] (https://www.tillerhq.com/how-tiller-works/). I have never used it but had once considered the idea of becoming an "affiliate" with an affiliate link to get a few extra bucks. I am not monetized as of yet.  
  
[My slides on Beancount] (https://docs.google.com/presentation/d/1KUTAJH_XT8YqCVIfYUJeM1ULDxObw5UXbJfI9KVky6g/edit?usp=sharing)  
[Beancount documentation] (https://beancount.github.io/docs/index.html)  
[Beancount repo] (https://github.com/beancount/)  
