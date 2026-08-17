USE SupermarketDB;

-- Product Stock Status
 CREATE VIEW ProductStockStatus AS
SELECT p.productID, p.productName, c.categoryName, s.supplierName, i.quantity, i.reorderLevel,
    CASE WHEN i.quantity = 0 THEN 'Out of Stock'
         WHEN i.quantity <= i.reorderLevel THEN 'Low Stock'
         ELSE 'In Stock' END AS stockStatus
FROM Product p
JOIN Category c ON p.categoryID = c.categoryID
JOIN Supplier s ON p.supplierID = s.supplierID
JOIN Inventory i ON p.productID = i.productID;

--Customer Purchase History
CREATE VIEW CustomerPurchaseHistory AS
SELECT c.customerID, CONCAT(c.fName, ' ', c.lName) AS customerName, s.saleID, s.saleDate,
    p.productName, si.quantity, si.unitPrice, si.discount, si.subTotal
FROM Customer c
JOIN Sale s ON c.customerID = s.customerID
JOIN SaleItem si ON s.saleID = si.saleID
JOIN Product p ON si.productID = p.productID;

-- Active Discounts
CREATE VIEW ActiveDiscounts AS
SELECT d.discountID, d.discountName, d.discountType, d.discountPercent, d.fixedAmount,
    d.startDate, d.endDate, p.productID, p.productName
FROM Discount d
JOIN ProductDiscount pd ON d.discountID = pd.discountID
JOIN Product p ON pd.productID = p.productID
WHERE CURDATE() BETWEEN d.startDate AND d.endDate;

--Supplier Purchase Summary
CREATE VIEW SupplierPurchaseSummary AS
SELECT s.supplierID, s.supplierName, COUNT(DISTINCT pu.purchaseID) AS totalPurchases,
    COALESCE(SUM(pu.totalCost),0) AS totalPurchaseCost
FROM Supplier s
LEFT JOIN Purchase pu ON s.supplierID = pu.supplierID
GROUP BY s.supplierID, s.supplierName;

-- Sales Summary
CREATE VIEW SalesSummary AS
SELECT DATE(s.saleDate) AS saleDate, COUNT(DISTINCT s.saleID) AS totalSales,
    COALESCE(SUM(si.subTotal),0) AS totalRevenue,
    COALESCE(SUM(s.pointsRedeemed), 0) AS totalPointsRedeemed
FROM Sale s
LEFT JOIN SaleItem si ON s.saleID = si.saleID
GROUP BY DATE(s.saleDate);

-- Products Per Category
CREATE VIEW ProductsPerCategory AS
SELECT c.categoryID, c.categoryName, COUNT(p.productID) AS numberOfProducts
FROM Category c
LEFT JOIN Product p ON c.categoryID = p.categoryID
GROUP BY c.categoryID, c.categoryName;