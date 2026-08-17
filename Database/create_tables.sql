USE SupermarketDB;

CREATE TABLE Category (
     categoryID VARCHAR(10) PRIMARY KEY,
     categoryName VARCHAR(100) NOT NULL UNIQUE,
     description VARCHAR(255)
     );

CREATE TABLE Supplier (
    supplierID VARCHAR(10) PRIMARY KEY,
    supplierName VARCHAR(100) NOT NULL,
    phoneNo VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(100) UNIQUE,
    address VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL
    );

CREATE TABLE Customer (
     customerID VARCHAR(10) PRIMARY KEY,
     fName VARCHAR(50) NOT NULL,
     lName VARCHAR(50) NOT NULL,
     email VARCHAR(100) UNIQUE,
     address VARCHAR(255),
     phone VARCHAR(20) NOT NULL UNIQUE
     );

CREATE TABLE Employee (
     employeeID VARCHAR(10) PRIMARY KEY,
     fName VARCHAR(50) NOT NULL,
     lName VARCHAR(50) NOT NULL,
     position VARCHAR(50) NOT NULL,
     phone VARCHAR(20) NOT NULL UNIQUE,
     email VARCHAR(100) UNIQUE,
     hireDate DATE NOT NULL,
     passwordHash VARCHAR(255) NOT NULL,
     status ENUM('Active','Inactive') DEFAULT 'Active'
     );

CREATE TABLE Discount (
     discountID VARCHAR(10) PRIMARY KEY,
     discountName VARCHAR(100) NOT NULL,
     discountPercent DECIMAL(5,2) NOT NULL CHECK(discountPercent>=0 AND discountPercent<=100),
     startDate DATE NOT NULL,
     endDate DATE NOT NULL,
     discountType ENUM('Percentage','Fixed') NOT NULL DEFAULT 'Percentage',
     fixedAmount DECIMAL(10,2) DEFAULT 0 CHECK(fixedAmount >= 0),
     CHECK(endDate>=startDate)
     );

CREATE TABLE Product (
     productID VARCHAR(10) PRIMARY KEY,
     categoryID VARCHAR(10) NOT NULL,
     supplierID VARCHAR(10) NOT NULL,
     productName VARCHAR(100) NOT NULL UNIQUE,
     unitPrice DECIMAL(10,2) NOT NULL CHECK(unitPrice>=0),
     costPrice DECIMAL(10,2) NOT NULL CHECK(costPrice>=0),
     expiryDate DATE,
     status ENUM('Available','Out of Stock','Discontinued') DEFAULT 'Available',
     barcode VARCHAR(50) UNIQUE,
     FOREIGN KEY(categoryID) REFERENCES Category(categoryID) ON UPDATE CASCADE ON DELETE RESTRICT,
     FOREIGN KEY(supplierID) REFERENCES Supplier(supplierID) ON UPDATE CASCADE ON DELETE RESTRICT
    );


CREATE TABLE LoyaltyCard (
     cardID VARCHAR(10) PRIMARY KEY,
     customerID VARCHAR(10) NOT NULL UNIQUE,
     points INT DEFAULT 0 CHECK(points>=0),
     issueDate DATE NOT NULL,
     expiryDate DATE NOT NULL,
     status ENUM('Active','Expired','Suspended') DEFAULT 'Active',
     CHECK(expiryDate>issueDate),
     FOREIGN KEY(customerID) REFERENCES Customer(customerID) ON UPDATE CASCADE ON DELETE CASCADE
     );

CREATE TABLE Inventory (
     inventoryID VARCHAR(10) PRIMARY KEY,
     productID VARCHAR(10) NOT NULL UNIQUE,
     quantity INT DEFAULT 0 CHECK(quantity>=0),
     reorderLevel INT DEFAULT 10 CHECK(reorderLevel>=0),
     lastUpdated DATETIME DEFAULT CURRENT_TIMESTAMP,
     FOREIGN KEY(productID) REFERENCES Product(productID) ON UPDATE CASCADE ON DELETE CASCADE
    );

CREATE TABLE Purchase (
     purchaseID VARCHAR(10) PRIMARY KEY,
     supplierID VARCHAR(10) NOT NULL,
     employeeID VARCHAR(10) NOT NULL,
     purchaseDate DATE NOT NULL,
     totalCost DECIMAL(12,2) DEFAULT 0 CHECK(totalCost>=0),
     status ENUM('Pending','Completed','Cancelled') DEFAULT 'Pending',
     FOREIGN KEY(supplierID) REFERENCES Supplier(supplierID) ON UPDATE CASCADE ON DELETE RESTRICT,
     FOREIGN KEY(employeeID) REFERENCES Employee(employeeID) ON UPDATE CASCADE ON DELETE RESTRICT
     );

CREATE TABLE Sale (
     saleID VARCHAR(10) PRIMARY KEY,
     customerID VARCHAR(10),
     employeeID VARCHAR(10) NOT NULL,
     saleDate DATETIME DEFAULT CURRENT_TIMESTAMP,
     totalAmount DECIMAL(12,2) DEFAULT 0 CHECK(totalAmount>=0),
     paymentMethod ENUM('Cash','Card','Mobile Money') NOT NULL,
     taxAmount DECIMAL(12,2) NOT NULL DEFAULT 0 CHECK(taxAmount >= 0),
     pointsRedeemed INT NOT NULL DEFAULT 0 CHECK(pointsRedeemed >= 0),
     FOREIGN KEY(customerID) REFERENCES Customer(customerID) ON UPDATE CASCADE ON DELETE SET NULL,
     FOREIGN KEY(employeeID) REFERENCES Employee(employeeID) ON UPDATE CASCADE ON DELETE RESTRICT
     );

CREATE TABLE ProductDiscount (
    productID VARCHAR(10) NOT NULL,
    discountID VARCHAR(10) NOT NULL,
    PRIMARY KEY(productID, discountID),
    FOREIGN KEY(productID) REFERENCES Product(productID) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY(discountID) REFERENCES Discount(discountID) ON UPDATE CASCADE ON DELETE CASCADE
    );

CREATE TABLE PurchaseItem (
     purchaseID VARCHAR(10) NOT NULL,
     productID VARCHAR(10) NOT NULL,
     quantity INT NOT NULL CHECK(quantity>0),
     unitCost DECIMAL(10,2) NOT NULL CHECK(unitCost>=0),
     PRIMARY KEY(purchaseID, productID),
     FOREIGN KEY(purchaseID) REFERENCES Purchase(purchaseID) ON UPDATE CASCADE ON DELETE CASCADE,
     FOREIGN KEY(productID) REFERENCES Product(productID) ON UPDATE CASCADE ON DELETE RESTRICT
    );

CREATE TABLE SaleItem (
    saleID VARCHAR(10) NOT NULL,
    productID VARCHAR(10) NOT NULL,
    quantity INT NOT NULL CHECK(quantity>0),
    unitPrice DECIMAL(10,2) NOT NULL CHECK(unitPrice>=0),
    discount DECIMAL(5,2) DEFAULT 0 CHECK(discount>=0 AND discount<=100),
    subTotal DECIMAL(12,2) GENERATED ALWAYS AS (quantity * unitPrice * (1 - discount / 100)) STORED,
    PRIMARY KEY(saleID, productID),
    FOREIGN KEY(saleID) REFERENCES Sale(saleID) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY(productID) REFERENCES Product(productID) ON UPDATE CASCADE ON DELETE RESTRICT
     );

CREATE TABLE InventoryMovement (
     movementID INT AUTO_INCREMENT PRIMARY KEY,
     productID VARCHAR(10) NOT NULL,
     employeeID VARCHAR(10) NOT NULL,
     movementType ENUM('Purchase','Sale','Return','Damage','Expiry','Adjustment') NOT NULL,
     quantity INT NOT NULL CHECK(quantity > 0),
     movementDate DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
     referenceID VARCHAR(10),
     FOREIGN KEY(productID) REFERENCES Product(productID) ON UPDATE CASCADE ON DELETE RESTRICT,
     FOREIGN KEY(employeeID) REFERENCES Employee(employeeID) ON UPDATE CASCADE ON DELETE RESTRICT
    );
