USE SupermarketDB;

-- query 1;
SELECT
    c.customerID,
    CONCAT(c.fName, ' ', c.lName) AS customerName,
    c.phone,
    lc.points AS loyaltyPoints,
    COUNT(s.saleID) AS totalOrders,
    SUM(s.totalAmount) AS totalSpent
FROM Customer c
JOIN LoyaltyCard lc
    ON c.customerID = lc.customerID
JOIN Sale s
    ON c.customerID = s.customerID
GROUP BY
    c.customerID,
    c.fName,
    c.lName,
    c.phone,
    lc.points
ORDER BY totalSpent DESC
LIMIT 5;


-- query 2;
SELECT
    p.productID,
    p.productName,
    cat.categoryName,
    p.costPrice,
    p.unitPrice,
    (p.unitPrice - p.costPrice) AS profitPerUnit,
    ROUND(
        ((p.unitPrice - p.costPrice) / p.costPrice) * 100,
        2
    ) AS profitMarginPercent
FROM Product p
JOIN Category cat
    ON p.categoryID = cat.categoryID
ORDER BY profitMarginPercent DESC;


-- query 3;
SELECT
    p.productID,
    p.productName,
    inv.quantity AS currentStock,
    inv.reorderLevel,
    sup.supplierName,
    sup.phoneNo AS supplierPhone
FROM Inventory inv
JOIN Product p
    ON inv.productID = p.productID
JOIN Supplier sup
    ON p.supplierID = sup.supplierID
WHERE inv.quantity <= (inv.reorderLevel + 30)
ORDER BY inv.quantity ASC;


-- query 4;
SELECT
    e.employeeID,
    CONCAT(e.fName, ' ', e.lName) AS cashierName,
    e.position,
    COUNT(s.saleID) AS totalTransactions,
    SUM(s.totalAmount) AS totalRevenueProcessed
FROM Employee e
JOIN Sale s
    ON e.employeeID = s.employeeID
GROUP BY
    e.employeeID,
    e.fName,
    e.lName,
    e.position
HAVING totalRevenueProcessed >= 100.00
ORDER BY totalRevenueProcessed DESC;


-- query 5;
SELECT
    cat.categoryID,
    cat.categoryName,
    SUM(si.quantity) AS totalUnitsSold,
    SUM(si.quantity * si.unitPrice) AS grossRevenue,
    ROUND(
        SUM(
            si.quantity * si.unitPrice * (si.discount / 100)
        ),
        2
    ) AS totalDiscountsGiven,
    SUM(si.subTotal) AS netRevenue
FROM Category cat
JOIN Product p
    ON cat.categoryID = p.categoryID
JOIN SaleItem si
    ON p.productID = si.productID
GROUP BY
    cat.categoryID,
    cat.categoryName
ORDER BY netRevenue DESC;


-- query 6;
SELECT
    sup.supplierID,
    sup.supplierName,
    COUNT(DISTINCT p.productID) AS productsSupplied,
    SUM(inv.quantity * p.unitPrice) AS retailStockValue,
    SUM(inv.quantity * p.costPrice) AS wholesaleStockCost
FROM Supplier sup
JOIN Product p
    ON sup.supplierID = p.supplierID
JOIN Inventory inv
    ON p.productID = inv.productID
GROUP BY
    sup.supplierID,
    sup.supplierName
ORDER BY retailStockValue DESC;


-- query 7;
SELECT
    d.discountID,
    d.discountName,
    d.discountPercent,
    d.startDate,
    d.endDate,
    p.productID,
    p.productName,
    p.unitPrice AS originalPrice,
    ROUND(
        p.unitPrice * (1 - d.discountPercent / 100),
        2
    ) AS discountedPrice
FROM Discount d
JOIN ProductDiscount pd
    ON d.discountID = pd.discountID
JOIN Product p
    ON pd.productID = p.productID
ORDER BY d.discountPercent DESC;


-- query 8;
SELECT
    paymentMethod,
    COUNT(saleID) AS totalTransactions,
    SUM(totalAmount) AS totalRevenue,
    ROUND(AVG(totalAmount), 2) AS averageTransactionValue
FROM Sale
GROUP BY paymentMethod
ORDER BY totalRevenue DESC;


-- query 9;
SELECT
    p.productID,
    p.productName,
    si.quantity,
    si.subTotal,
    DENSE_RANK() OVER (
        ORDER BY si.subTotal DESC
    ) AS salesRank
FROM Product p
JOIN SaleItem si
    ON p.productID = si.productID;


-- query 10;
SELECT
    p.productID,
    p.productName,
    p.unitPrice,
    inv.quantity AS stockInHand,
    p.status
FROM Product p
JOIN Inventory inv
    ON p.productID = inv.productID
LEFT JOIN SaleItem si
    ON p.productID = si.productID
WHERE si.saleID IS NULL;