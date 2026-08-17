USE SupermarketDB;

-- Before a Sale Item is inserted
DELIMITER //

CREATE TRIGGER BeforeSaleItemInsert
BEFORE INSERT ON SaleItem
FOR EACH ROW
BEGIN
    DECLARE v_stock INT;
    SELECT quantity INTO v_stock FROM Inventory WHERE productID = NEW.productID;
    IF v_stock IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Product does not have an inventory record';
    END IF;
    IF NEW.quantity > v_stock THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient stock for this product';
    END IF;
END //

DELIMITER ;

--After a Sale Item is inserted
DELIMITER //

CREATE TRIGGER AfterSaleItemInsert
AFTER INSERT ON SaleItem
FOR EACH ROW
BEGIN
    UPDATE Inventory SET quantity = quantity - NEW.quantity, lastUpdated = CURRENT_TIMESTAMP
    WHERE productID = NEW.productID;
END //

DELIMITER ;

-- After a purchase Item is inserted
DELIMITER //
 
CREATE TRIGGER AfterPurchaseItemInsert
AFTER INSERT ON PurchaseItem
FOR EACH ROW
BEGIN
    DECLARE v_employeeID VARCHAR(10);
    UPDATE Inventory SET quantity = quantity + NEW.quantity, lastUpdated = CURRENT_TIMESTAMP
    WHERE productID = NEW.productID;
 
    SELECT employeeID INTO v_employeeID FROM Purchase WHERE purchaseID = NEW.purchaseID;
    INSERT INTO InventoryMovement(productID, employeeID, movementType, quantity, referenceID)
        VALUES(NEW.productID, v_employeeID, 'Purchase', NEW.quantity, NEW.purchaseID);
END //
 
DELIMITER ;