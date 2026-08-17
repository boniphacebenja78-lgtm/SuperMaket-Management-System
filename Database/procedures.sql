USE SupermarketDB;


-- To process sale
DELIMITER //

CREATE PROCEDURE ProcessSale(
    IN p_saleID VARCHAR(10), IN p_customerID VARCHAR(10), IN p_employeeID VARCHAR(10),
    IN p_productID VARCHAR(10), IN p_quantity INT, IN p_paymentMethod VARCHAR(20))
BEGIN
    DECLARE v_price DECIMAL(10,2);
    DECLARE v_discount DECIMAL(5,2) DEFAULT 0;
    SELECT unitPrice INTO v_price FROM Product WHERE productID = p_productID AND status <> 'Discontinued';
    SELECT COALESCE(MAX(d.discountPercent),0) INTO v_discount FROM Discount d
        JOIN ProductDiscount pd ON d.discountID = pd.discountID
        WHERE pd.productID = p_productID AND d.discountType = 'Percentage'
          AND CURDATE() BETWEEN d.startDate AND d.endDate;
    INSERT INTO Sale(saleID,customerID,employeeID,paymentMethod) VALUES(p_saleID,p_customerID,p_employeeID,p_paymentMethod);
    -- subTotal is a generated column, so it is left out of this insert
    INSERT INTO SaleItem(saleID,productID,quantity,unitPrice,discount)
        VALUES(p_saleID,p_productID,p_quantity,v_price,v_discount);
END //

DELIMITER ;


--To Search for Products
DELIMITER //

CREATE PROCEDURE SearchProducts(IN p_search VARCHAR(100))
BEGIN
    SELECT p.productID, p.productName, p.barcode, c.categoryName, p.unitPrice, i.quantity, p.status
    FROM Product p
    JOIN Category c ON p.categoryID = c.categoryID
    JOIN Inventory i ON p.productID = i.productID
    WHERE p.productName LIKE CONCAT('%', p_search, '%')
       OR p.barcode = p_search
       OR c.categoryName LIKE CONCAT('%', p_search, '%');
END //

DELIMITER ;


--To record a purchase
DELIMITER //

CREATE PROCEDURE RecordPurchase(
    IN p_purchaseID VARCHAR(10), IN p_supplierID VARCHAR(10), IN p_employeeID VARCHAR(10),
    IN p_productID VARCHAR(10), IN p_quantity INT, IN p_unitCost DECIMAL(10,2))
BEGIN
    DECLARE v_total DECIMAL(12,2);
    INSERT INTO Purchase(purchaseID,supplierID,employeeID,purchaseDate,totalCost,status)
        VALUES(p_purchaseID,p_supplierID,p_employeeID,CURDATE(),p_quantity*p_unitCost,'Completed');
    INSERT INTO PurchaseItem(purchaseID,productID,quantity,unitCost) VALUES(p_purchaseID,p_productID,p_quantity,p_unitCost);
    SELECT SUM(quantity*unitCost) INTO v_total FROM PurchaseItem WHERE purchaseID=p_purchaseID;
    UPDATE Purchase SET totalCost=v_total WHERE purchaseID=p_purchaseID;
END //

DELIMITER ;


--To calculate sale total
DELIMITER //

CREATE FUNCTION CalculateSaleTotal(p_saleID VARCHAR(10))
RETURNS DECIMAL(12,2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_total DECIMAL(12,2);
    SELECT COALESCE(SUM(subTotal),0) INTO v_total FROM SaleItem WHERE saleID = p_saleID;
    RETURN v_total;
END //

DELIMITER ;

DELIMITER //


--To get product discount
CREATE FUNCTION GetProductDiscount(p_productID VARCHAR(10))
RETURNS DECIMAL(5,2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_discount DECIMAL(5,2) DEFAULT 0;
    SELECT COALESCE(MAX(
        CASE WHEN d.discountType = 'Percentage' THEN d.discountPercent
             WHEN d.discountType = 'Fixed' AND p.unitPrice > 0 THEN (d.fixedAmount / p.unitPrice) * 100
             ELSE 0 END), 0) INTO v_discount
    FROM Discount d
    JOIN ProductDiscount pd ON d.discountID = pd.discountID
    JOIN Product p ON pd.productID = p.productID
    WHERE pd.productID = p_productID
      AND CURDATE() BETWEEN d.startDate AND d.endDate;
    RETURN LEAST(v_discount, 100);
END //

DELIMITER ;
