---user roles---

CREATE ROLE 'admin_role';
CREATE ROLE 'sales_role';



---privileges---
GRANT ALL PRIVILEGES ON supermarketdb.* TO 'admin_role';


GRANT SELECT, INSERT, UPDATE ON supermarketdb.Customer TO 'sales_role';
GRANT SELECT, INSERT, UPDATE ON supermarketdb.Sale TO 'sales_role';
GRANT SELECT, INSERT ON supermarketdb.SaleItem TO 'sales_role';
GRANT SELECT, INSERT, UPDATE ON supermarketdb.LoyaltyCard TO 'sales_role';
GRANT SELECT ON supermarketdb.Product TO 'sales_role';
GRANT SELECT ON supermarketdb.Discount TO 'sales_role';