from flask import Flask, render_template, request, redirect, url_for
from services.database import get_db_connection

app = Flask(__name__)


# ==========================================
# DASHBOARD
# ==========================================


@app.route("/")
def home():

    connection = get_db_connection()

    if not connection:
        return render_template(
            "index.html",
            error="Could not connect to MariaDB."
        )

    try:

        cursor = connection.cursor()

        # ==========================================
        # TOTAL PRODUCTS
        # ==========================================

        cursor.execute("""
            SELECT COUNT(*)
            FROM product
        """)

        products = cursor.fetchone()[0]


        # ==========================================
        # TOTAL CATEGORIES
        # ==========================================

        cursor.execute("""
            SELECT COUNT(*)
            FROM category
        """)

        categories = cursor.fetchone()[0]


        # ==========================================
        # TOTAL CUSTOMERS
        # ==========================================

        cursor.execute("""
            SELECT COUNT(*)
            FROM customer
        """)

        customers = cursor.fetchone()[0]


        # ==========================================
        # TOTAL SUPPLIERS
        # ==========================================

        cursor.execute("""
            SELECT COUNT(*)
            FROM supplier
        """)

        suppliers = cursor.fetchone()[0]


        # ==========================================
        # TOTAL SALES
        # ==========================================

        cursor.execute("""
            SELECT COUNT(*)
            FROM sale
        """)

        total_sales = cursor.fetchone()[0]


        # ==========================================
        # LOW STOCK PRODUCTS
        # ==========================================

        cursor.execute("""
            SELECT COUNT(*)
            FROM inventory
            WHERE quantity > 0
            AND quantity <= reorderLevel
        """)

        low_stock = cursor.fetchone()[0]


        # ==========================================
        # TODAY'S REVENUE
        # ==========================================

        cursor.execute("""
            SELECT COALESCE(SUM(totalAmount), 0)
            FROM sale
            WHERE DATE(saleDate) = CURDATE()
        """)

        today_revenue = cursor.fetchone()[0]


        # ==========================================
        # CLOSE DATABASE
        # ==========================================

        cursor.close()
        connection.close()


        # ==========================================
        # SEND DATA TO DASHBOARD
        # ==========================================

        return render_template(
            "index.html",

            products=products,

            categories=categories,

            customers=customers,

            suppliers=suppliers,

            total_sales=total_sales,

            low_stock=low_stock,

            today_revenue=today_revenue
        )


    except Exception as e:

        if connection:
            connection.close()

        return render_template(
            "index.html",
            error=str(e)
        )



# ==========================================
# VIEW PRODUCTS
# ==========================================

@app.route("/products")
def products():

    connection = get_db_connection()

    if not connection:
        return "Database connection failed."

    try:

        search = request.args.get("search", "").strip()

        cursor = connection.cursor()

        if search:

            query = """
                SELECT
                    p.productID,
                    p.productName,
                    c.categoryName,
                    s.supplierName,
                    p.unitPrice,
                    p.costPrice,
                    p.expiryDate,
                    p.status,
                    p.barcode
                FROM product p
                INNER JOIN category c
                    ON p.categoryID = c.categoryID
                INNER JOIN supplier s
                    ON p.supplierID = s.supplierID
                WHERE
                    p.productID LIKE ?
                    OR p.productName LIKE ?
                    OR c.categoryName LIKE ?
                    OR s.supplierName LIKE ?
                ORDER BY p.productName
            """

            search_value = f"%{search}%"

            cursor.execute(
                query,
                (
                    search_value,
                    search_value,
                    search_value,
                    search_value
                )
            )

        else:

            query = """
                SELECT
                    p.productID,
                    p.productName,
                    c.categoryName,
                    s.supplierName,
                    p.unitPrice,
                    p.costPrice,
                    p.expiryDate,
                    p.status,
                    p.barcode
                FROM product p
                INNER JOIN category c
                    ON p.categoryID = c.categoryID
                INNER JOIN supplier s
                    ON p.supplierID = s.supplierID
                ORDER BY p.productName
            """

            cursor.execute(query)

        products = cursor.fetchall()

        cursor.close()
        connection.close()

        return render_template(
            "products.html",
            products=products,
            search=search
        )

    except Exception as e:

        if connection:
            connection.close()

        return f"""
        <h1>Database Error</h1>
        <p>{e}</p>
        """


# ==========================================
# ADD PRODUCT PAGE
# ==========================================

@app.route("/products/add")
def add_product():

    connection = get_db_connection()

    if not connection:
        return "Database connection failed."

    try:

        cursor = connection.cursor()

        cursor.execute("""
            SELECT categoryID, categoryName
            FROM category
            ORDER BY categoryName
        """)

        categories = cursor.fetchall()

        cursor.execute("""
            SELECT supplierID, supplierName
            FROM supplier
            ORDER BY supplierName
        """)

        suppliers = cursor.fetchall()

        cursor.close()
        connection.close()

        return render_template(
            "add_product.html",
            categories=categories,
            suppliers=suppliers
        )

    except Exception as e:

        if connection:
            connection.close()

        return f"""
        <h1>Database Error</h1>
        <p>{e}</p>
        """


# ==========================================
# INSERT PRODUCT
# ==========================================

@app.route("/products/add", methods=["POST"])
def save_product():

    product_id = request.form["productID"].strip()
    product_name = request.form["productName"].strip()
    category_id = request.form["categoryID"]
    supplier_id = request.form["supplierID"]
    unit_price = request.form["unitPrice"]
    cost_price = request.form["costPrice"]
    expiry_date = request.form.get("expiryDate") or None
    status = request.form["status"]
    barcode = request.form.get("barcode") or None

    connection = get_db_connection()

    if not connection:
        return "Database connection failed."

    try:

        cursor = connection.cursor()

        query = """
            INSERT INTO product
            (
                productID,
                categoryID,
                supplierID,
                productName,
                unitPrice,
                costPrice,
                expiryDate,
                status,
                barcode
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        cursor.execute(
            query,
            (
                product_id,
                category_id,
                supplier_id,
                product_name,
                unit_price,
                cost_price,
                expiry_date,
                status,
                barcode
            )
        )

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for("products"))

    except Exception as e:

        if connection:
            connection.rollback()
            connection.close()

        return f"""
        <h1>Could Not Add Product</h1>

        <p>{e}</p>

        <br>

        <a href="/products/add">
            Go Back
        </a>
        """


# ==========================================
# EDIT PRODUCT PAGE
# ==========================================

@app.route("/products/edit/<product_id>")
def edit_product(product_id):

    connection = get_db_connection()

    if not connection:
        return "Database connection failed."

    try:

        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                productID,
                categoryID,
                supplierID,
                productName,
                unitPrice,
                costPrice,
                expiryDate,
                status,
                barcode
            FROM product
            WHERE productID = ?
        """, (product_id,))

        product = cursor.fetchone()

        if not product:

            cursor.close()
            connection.close()

            return """
            <h1>Product Not Found</h1>

            <p>The product does not exist.</p>

            <a href="/products">
                Back to Products
            </a>
            """

        cursor.execute("""
            SELECT
                categoryID,
                categoryName
            FROM category
            ORDER BY categoryName
        """)

        categories = cursor.fetchall()

        cursor.execute("""
            SELECT
                supplierID,
                supplierName
            FROM supplier
            ORDER BY supplierName
        """)

        suppliers = cursor.fetchall()

        cursor.close()
        connection.close()

        return render_template(
            "edit_product.html",
            product=product,
            categories=categories,
            suppliers=suppliers
        )

    except Exception as e:

        if connection:
            connection.close()

        return f"""
        <h1>Database Error</h1>
        <p>{e}</p>
        """


# ==========================================
# UPDATE PRODUCT
# ==========================================

@app.route("/products/edit/<product_id>", methods=["POST"])
def update_product(product_id):

    product_name = request.form["productName"].strip()
    category_id = request.form["categoryID"]
    supplier_id = request.form["supplierID"]
    unit_price = request.form["unitPrice"]
    cost_price = request.form["costPrice"]
    expiry_date = request.form.get("expiryDate") or None
    status = request.form["status"]
    barcode = request.form.get("barcode") or None

    connection = get_db_connection()

    if not connection:
        return "Database connection failed."

    try:

        cursor = connection.cursor()

        query = """
            UPDATE product
            SET
                categoryID = ?,
                supplierID = ?,
                productName = ?,
                unitPrice = ?,
                costPrice = ?,
                expiryDate = ?,
                status = ?,
                barcode = ?
            WHERE productID = ?
        """

        cursor.execute(
            query,
            (
                category_id,
                supplier_id,
                product_name,
                unit_price,
                cost_price,
                expiry_date,
                status,
                barcode,
                product_id
            )
        )

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for("products"))

    except Exception as e:

        if connection:
            connection.rollback()
            connection.close()

        return f"""
        <h1>Could Not Update Product</h1>

        <p>{e}</p>

        <br>

        <a href="/products/edit/{product_id}">
            Go Back
        </a>
        """


# ==========================================
# DELETE / DISCONTINUE PRODUCT
# ==========================================

@app.route("/products/delete/<product_id>", methods=["POST"])
def delete_product(product_id):

    connection = get_db_connection()

    if not connection:
        return "Database connection failed."

    try:

        cursor = connection.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM purchaseitem
            WHERE productID = ?
        """, (product_id,))

        purchase_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM saleitem
            WHERE productID = ?
        """, (product_id,))

        sale_count = cursor.fetchone()[0]

        if purchase_count > 0 or sale_count > 0:

            cursor.execute("""
                UPDATE product
                SET status = 'Discontinued'
                WHERE productID = ?
            """, (product_id,))

            connection.commit()

            cursor.close()
            connection.close()

            return redirect(url_for("products"))

        cursor.execute("""
            DELETE FROM product
            WHERE productID = ?
        """, (product_id,))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for("products"))

    except Exception as e:

        if connection:
            connection.rollback()
            connection.close()

        return f"""
        <h1>Could Not Delete Product</h1>

        <p>{e}</p>

        <br>

        <a href="/products">
            Back to Products
        </a>
        """


# ==========================================
# INVENTORY
# ==========================================

@app.route("/inventory")
def inventory():

    connection = get_db_connection()

    if not connection:
        return "Database connection failed."

    try:

        search = request.args.get("search", "").strip()

        cursor = connection.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM inventory
        """)

        total_items = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM inventory
            WHERE quantity > 0
            AND quantity <= reorderLevel
        """)

        low_stock = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM inventory
            WHERE quantity = 0
        """)

        out_of_stock = cursor.fetchone()[0]

        query = """
            SELECT
                i.inventoryID,
                i.productID,
                p.productName,
                c.categoryName,
                i.quantity,
                i.reorderLevel,
                i.lastUpdated
            FROM inventory i
            INNER JOIN product p
                ON i.productID = p.productID
            INNER JOIN category c
                ON p.categoryID = c.categoryID
        """

        if search:

            query += """
                WHERE
                    i.productID LIKE ?
                    OR p.productName LIKE ?
                    OR c.categoryName LIKE ?
            """

            search_value = f"%{search}%"

            cursor.execute(
                query + " ORDER BY p.productName",
                (
                    search_value,
                    search_value,
                    search_value
                )
            )

        else:

            cursor.execute(
                query + " ORDER BY p.productName"
            )

        inventory_items = cursor.fetchall()

        cursor.close()
        connection.close()

        return render_template(
            "inventory.html",
            inventory_items=inventory_items,
            total_items=total_items,
            low_stock=low_stock,
            out_of_stock=out_of_stock,
            search=search
        )

    except Exception as e:

        if connection:
            connection.close()

        return f"""
        <h1>Inventory Error</h1>

        <p>{e}</p>

        <br>

        <a href="/">
            Back to Dashboard
        </a>
        """


# ==========================================
# ADD STOCK PAGE
# ==========================================

@app.route("/inventory/add")
def add_stock():

    connection = get_db_connection()

    if not connection:
        return "Database connection failed."

    try:

        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                productID,
                productName
            FROM product
            WHERE status != 'Discontinued'
            ORDER BY productName
        """)

        products = cursor.fetchall()

        cursor.execute("""
            SELECT
                employeeID,
                fName,
                lName
            FROM employee
            WHERE status = 'Active'
            ORDER BY fName, lName
        """)

        employees = cursor.fetchall()

        cursor.close()
        connection.close()

        return render_template(
            "add_stock.html",
            products=products,
            employees=employees
        )

    except Exception as e:

        if connection:
            connection.close()

        return f"""
        <h1>Inventory Error</h1>
        <p>{e}</p>
        """


# ==========================================
# SAVE STOCK MOVEMENT
# ==========================================

@app.route("/inventory/add", methods=["POST"])
def save_stock():

    product_id = request.form["productID"]
    employee_id = request.form["employeeID"]
    movement_type = request.form["movementType"]
    quantity = int(request.form["quantity"])
    reference_id = request.form.get("referenceID") or None

    connection = get_db_connection()

    if not connection:
        return "Database connection failed."

    try:

        cursor = connection.cursor()

        if quantity <= 0:

            cursor.close()
            connection.close()

            return """
            <h1>Invalid Quantity</h1>

            <p>Quantity must be greater than zero.</p>

            <br>

            <a href="/inventory/add">
                Go Back
            </a>
            """

        cursor.execute("""
            SELECT quantity
            FROM inventory
            WHERE productID = ?
        """, (product_id,))

        inventory_record = cursor.fetchone()

        if not inventory_record:

            cursor.close()
            connection.close()

            return """
            <h1>Inventory Error</h1>

            <p>This product does not have an inventory record.</p>

            <br>

            <a href="/inventory">
                Back to Inventory
            </a>
            """

        current_quantity = inventory_record[0]

        if movement_type in ["Purchase", "Return"]:

            new_quantity = current_quantity + quantity

        elif movement_type in ["Sale", "Damage", "Expiry"]:

            if quantity > current_quantity:

                cursor.close()
                connection.close()

                return f"""
                <h1>Insufficient Stock</h1>

                <p>
                    Current stock is
                    <strong>{current_quantity}</strong>.
                </p>

                <p>
                    You cannot remove
                    <strong>{quantity}</strong> items.
                </p>

                <br>

                <a href="/inventory/add">
                    Go Back
                </a>
                """

            new_quantity = current_quantity - quantity

        elif movement_type == "Adjustment":

            new_quantity = quantity

        else:

            cursor.close()
            connection.close()

            return """
            <h1>Invalid Movement Type</h1>

            <p>Invalid inventory movement.</p>

            <br>

            <a href="/inventory/add">
                Go Back
            </a>
            """

        cursor.execute("""
            UPDATE inventory
            SET
                quantity = ?,
                lastUpdated = CURRENT_TIMESTAMP
            WHERE productID = ?
        """, (
            new_quantity,
            product_id
        ))

        cursor.execute("""
            SELECT movementID
            FROM inventorymovement
            ORDER BY movementID DESC
            LIMIT 1
        """)

        last_movement = cursor.fetchone()

        if last_movement:

            last_id = last_movement[0]

            number = int(last_id.replace("MOV", ""))

            movement_id = f"MOV{number + 1:03d}"

        else:

            movement_id = "MOV001"

        cursor.execute("""
            INSERT INTO inventorymovement
            (
                movementID,
                productID,
                employeeID,
                movementType,
                quantity,
                referenceID
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            movement_id,
            product_id,
            employee_id,
            movement_type,
            quantity,
            reference_id
        ))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for("inventory"))

    except Exception as e:

        if connection:
            connection.rollback()
            connection.close()

        return f"""
        <h1>Could Not Update Inventory</h1>

        <p>{e}</p>

        <br>

        <a href="/inventory/add">
            Go Back
        </a>
        """


# ==========================================
# EMPLOYEES
# ==========================================

# ==========================================
# ADD EMPLOYEE PAGE
# ==========================================

@app.route("/employees/add")
def add_employee():

    return render_template("add_employee.html")


# ==========================================
# VIEW EMPLOYEES
# ==========================================

@app.route("/employees")
def employees():

    connection = get_db_connection()

    if not connection:
        return "Database connection failed."

    try:

        search = request.args.get("search", "").strip()

        cursor = connection.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM employee
        """)

        total_employees = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM employee
            WHERE status = 'Active'
        """)

        active_employees = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM employee
            WHERE status = 'Inactive'
        """)

        inactive_employees = cursor.fetchone()[0]

        query = """
            SELECT
                employeeID,
                fName,
                lName,
                position,
                phone,
                email,
                hireDate,
                status
            FROM employee
        """

        if search:

            query += """
                WHERE
                    employeeID LIKE ?
                    OR fName LIKE ?
                    OR lName LIKE ?
                    OR position LIKE ?
                    OR phone LIKE ?
                    OR email LIKE ?
            """

            search_value = f"%{search}%"

            cursor.execute(
                query + """
                    ORDER BY fName, lName
                """,
                (
                    search_value,
                    search_value,
                    search_value,
                    search_value,
                    search_value,
                    search_value
                )
            )

        else:

            cursor.execute(
                query + """
                    ORDER BY fName, lName
                """
            )

        employees = cursor.fetchall()

        cursor.close()
        connection.close()

        return render_template(
            "employees.html",
            employees=employees,
            total_employees=total_employees,
            active_employees=active_employees,
            inactive_employees=inactive_employees,
            search=search
        )

    except Exception as e:

        if connection:
            connection.close()

        return f"""
        <h1>Employee Error</h1>

        <p>{e}</p>

        <br>

        <a href="/">
            Back to Dashboard
        </a>
        """


# ==========================================
# INSERT EMPLOYEE
# ==========================================

@app.route("/employees/add", methods=["POST"])
def save_employee():

    employee_id = request.form["employeeID"].strip()
    first_name = request.form["fName"].strip()
    last_name = request.form["lName"].strip()
    position = request.form["position"].strip()
    phone = request.form["phone"].strip()

    email = request.form.get(
        "email",
        ""
    ).strip() or None

    hire_date = request.form["hireDate"]

    password_hash = request.form["passwordHash"].strip()

    status = request.form["status"]

    connection = get_db_connection()

    if not connection:
        return "Database connection failed."

    try:

        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO employee
            (
                employeeID,
                fName,
                lName,
                position,
                phone,
                email,
                hireDate,
                passwordHash,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            employee_id,
            first_name,
            last_name,
            position,
            phone,
            email,
            hire_date,
            password_hash,
            status
        ))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(
            url_for("employees")
        )

    except Exception as e:

        if connection:
            connection.rollback()
            connection.close()

        return f"""
        <h1>Could Not Add Employee</h1>

        <p>{e}</p>

        <br>

        <a href="/employees/add">
            Go Back
        </a>
        """


# ==========================================
# EDIT EMPLOYEE PAGE
# ==========================================

@app.route("/employees/edit/<employee_id>")
def edit_employee(employee_id):

    connection = get_db_connection()

    if not connection:
        return "Database connection failed."

    try:

        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                employeeID,
                fName,
                lName,
                position,
                phone,
                email,
                hireDate,
                passwordHash,
                status
            FROM employee
            WHERE employeeID = ?
        """, (
            employee_id,
        ))

        employee = cursor.fetchone()

        cursor.close()
        connection.close()

        if not employee:

            return """
            <h1>Employee Not Found</h1>

            <p>
                The employee does not exist.
            </p>

            <br>

            <a href="/employees">
                Back to Employees
            </a>
            """

        return render_template(
            "edit_employee.html",
            employee=employee
        )

    except Exception as e:

        if connection:
            connection.close()

        return f"""
        <h1>Employee Error</h1>

        <p>{e}</p>

        <br>

        <a href="/employees">
            Back to Employees
        </a>
        """


# ==========================================
# UPDATE EMPLOYEE
# ==========================================

@app.route("/employees/edit/<employee_id>", methods=["POST"])
def update_employee(employee_id):

    first_name = request.form["fName"].strip()
    last_name = request.form["lName"].strip()
    position = request.form["position"].strip()
    phone = request.form["phone"].strip()

    email = request.form.get(
        "email",
        ""
    ).strip() or None

    hire_date = request.form["hireDate"]

    password_hash = request.form["passwordHash"].strip()

    status = request.form["status"]

    connection = get_db_connection()

    if not connection:
        return "Database connection failed."

    try:

        cursor = connection.cursor()

        cursor.execute("""
            UPDATE employee
            SET
                fName = ?,
                lName = ?,
                position = ?,
                phone = ?,
                email = ?,
                hireDate = ?,
                passwordHash = ?,
                status = ?
            WHERE employeeID = ?
        """, (
            first_name,
            last_name,
            position,
            phone,
            email,
            hire_date,
            password_hash,
            status,
            employee_id
        ))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(
            url_for("employees")
        )

    except Exception as e:

        if connection:
            connection.rollback()
            connection.close()

        return f"""
        <h1>Could Not Update Employee</h1>

        <p>{e}</p>

        <br>

        <a href="/employees/edit/{employee_id}">
            Go Back
        </a>
        """


# ==========================================
# DELETE / DEACTIVATE EMPLOYEE
# ==========================================

@app.route("/employees/delete/<employee_id>", methods=["POST"])
def delete_employee(employee_id):

    connection = get_db_connection()

    if not connection:
        return "Database connection failed."

    try:

        cursor = connection.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM inventorymovement
            WHERE employeeID = ?
        """, (
            employee_id,
        ))

        movement_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM sale
            WHERE employeeID = ?
        """, (
            employee_id,
        ))

        sale_count = cursor.fetchone()[0]

        if movement_count > 0 or sale_count > 0:

            cursor.execute("""
                UPDATE employee
                SET status = 'Inactive'
                WHERE employeeID = ?
            """, (
                employee_id,
            ))

            connection.commit()

            cursor.close()
            connection.close()

            return redirect(
                url_for("employees")
            )

        cursor.execute("""
            DELETE FROM employee
            WHERE employeeID = ?
        """, (
            employee_id,
        ))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(
            url_for("employees")
        )

    except Exception as e:

        if connection:
            connection.rollback()
            connection.close()

        return f"""
        <h1>Could Not Delete Employee</h1>

        <p>{e}</p>

        <br>

        <a href="/employees">
            Back to Employees
        </a>
        """
# ==========================================

# CUSTOMERS

# ==========================================

# ==========================================

# VIEW CUSTOMERS

# ==========================================

@app.route("/customers")
def customers():
    connection = get_db_connection()

    if not connection:
        return "Database connection failed."

    try:
        search = request.args.get("search", "").strip()

        cursor = connection.cursor()

        # ==========================================
        # CUSTOMER SUMMARY
        # ==========================================

        cursor.execute("""
            SELECT COUNT(*)
            FROM customer
        """)

        total_customers = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM customer
            WHERE email IS NOT NULL
            AND email != ''
        """)

        customers_with_email = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM customer
            WHERE address IS NOT NULL
            AND address != ''
        """)

        customers_with_address = cursor.fetchone()[0]

        # ==========================================
        # GET CUSTOMERS
        # ==========================================

        query = """
            SELECT
                customerID,
                fName,
                lName,
                email,
                address,
                phone
            FROM customer
        """

        # ==========================================
        # SEARCH CUSTOMERS
        # ==========================================

        if search:

            query += """
                WHERE
                    customerID LIKE ?
                    OR fName LIKE ?
                    OR lName LIKE ?
                    OR email LIKE ?
                    OR address LIKE ?
                    OR phone LIKE ?
            """

            search_value = f"%{search}%"

            cursor.execute(
                query + """
                    ORDER BY fName, lName
                """,
                (
                    search_value,
                    search_value,
                    search_value,
                    search_value,
                    search_value,
                    search_value
                )
            )

        else:

            cursor.execute(
                query + """
                    ORDER BY fName, lName
                """
            )

        customers_list = cursor.fetchall()

        cursor.close()
        connection.close()

        return render_template(
            "customers.html",
            customers=customers_list,
            total_customers=total_customers,
            customers_with_email=customers_with_email,
            customers_with_address=customers_with_address,
            search=search
        )

    except Exception as e:

        if connection:
            connection.close()

        return f"""
        <h1>Customer Error</h1>

        <p>{e}</p>

        <br>

        <a href="/">
            Back to Dashboard
        </a>
        """


# ==========================================

# ADD CUSTOMER PAGE

# ==========================================

@app.route("/customers/add")
def add_customer():
    return render_template(
        "add_customer.html"
    )

# ==========================================

# INSERT CUSTOMER

# ==========================================

@app.route("/customers/add", methods=["POST"])
def save_customer():
    customer_id = request.form["customerID"].strip()
    first_name = request.form["fName"].strip()
    last_name = request.form["lName"].strip()

    email = request.form.get(
        "email",
        ""
    ).strip() or None

    address = request.form.get(
        "address",
        ""
    ).strip() or None

    phone = request.form["phone"].strip()

    connection = get_db_connection()

    if not connection:
        return "Database connection failed."

    try:

        cursor = connection.cursor()

        # ==========================================
        # INSERT CUSTOMER
        # ==========================================

        cursor.execute("""
            INSERT INTO customer
            (
                customerID,
                fName,
                lName,
                email,
                address,
                phone
            )

            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            customer_id,
            first_name,
            last_name,
            email,
            address,
            phone
        ))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(
            url_for("customers")
        )

    except Exception as e:

        if connection:
            connection.rollback()
            connection.close()

        return f"""
        <h1>Could Not Add Customer</h1>

        <p>{e}</p>

        <br>

        <a href="/customers/add">
            Go Back
        </a>
        """

# ==========================================

# EDIT CUSTOMER PAGE

# ==========================================

@app.route("/customers/edit/<customer_id>")
def edit_customer(customer_id):

    connection = get_db_connection()

    if not connection:
        return "Database connection failed."

    try:

        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                customerID,
                fName,
                lName,
                email,
                address,
                phone
            FROM customer
            WHERE customerID = ?
        """, (
            customer_id,
        ))

        customer = cursor.fetchone()

        cursor.close()
        connection.close()

        if not customer:

            return """
            <h1>Customer Not Found</h1>

            <p>
                The customer does not exist.
            </p>

            <br>

            <a href="/customers">
                Back to Customers
            </a>
            """

        return render_template(
            "edit_customer.html",
            customer=customer
        )

    except Exception as e:

        if connection:
            connection.close()

        return f"""
    <h1>Customer Error</h1>

    <p>{e}</p>

    <br>

    <a href="/customers">
        Back to Customers
    </a>
    """


# ==========================================

# UPDATE CUSTOMER

# ==========================================

@app.route("/customers/edit/<customer_id>", methods=["POST"])
def update_customer(customer_id):
    first_name = request.form["fName"].strip()
    last_name = request.form["lName"].strip()

    email = request.form.get(
        "email",
        ""
    ).strip() or None

    address = request.form.get(
        "address",
        ""
    ).strip() or None

    phone = request.form["phone"].strip()

    connection = get_db_connection()

    if not connection:
        return "Database connection failed."

    try:
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE customer

            SET
                fName = ?,
                lName = ?,
                email = ?,
                address = ?,
                phone = ?

            WHERE customerID = ?
        """, (
            first_name,
            last_name,
            email,
            address,
            phone,
            customer_id
        ))

        connection.commit()
    except Exception as e:
        connection.rollback()
        if connection:
            connection.close()
        return f"""
        <h1>Could Not Update Customer</h1>

        <p>{e}</p>

        <br>

        <a href="/customers/edit/{customer_id}">
            Go Back
        </a>
        """
    finally:
        if connection:
            connection.close()

    return redirect(
        url_for("customers")
    )


# ==========================================

# DELETE CUSTOMER

# ==========================================

@app.route("/customers/delete/<customer_id>", methods=["POST"])
def delete_customer(customer_id):
    connection = get_db_connection()

    if not connection:
        return "Database connection failed."

    try:

        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM customer
            WHERE customerID = ?
        """, (
            customer_id,
        ))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(
            url_for("customers")
        )

    except Exception as e:

        if connection:
            connection.rollback()
            connection.close()

        return f"""
        <h1>Could Not Delete Customer</h1>

        <p>{e}</p>

        <br>

        <a href="/customers">
            Back to Customers
        </a>
        """
# ==========================================

# CATEGORIES

# ==========================================

# ==========================================

# VIEW CATEGORIES

# ==========================================

@app.route("/categories")
def categories():
    connection = get_db_connection()

    if not connection:
        return "Database connection failed."

    try:
        search = request.args.get("search", "").strip()

        cursor = connection.cursor()

        # ==========================================
        # CATEGORY SUMMARY
        # ==========================================

        cursor.execute("""
            SELECT COUNT(*)
            FROM category
        """)

        total_categories = cursor.fetchone()[0]

        # ==========================================
        # GET CATEGORIES
        # ==========================================

        query = """
            SELECT
                c.categoryID,
                c.categoryName,
                c.description,
                COUNT(p.productID) AS productCount
            FROM category c

            LEFT JOIN product p
                ON c.categoryID = p.categoryID
        """

        # ==========================================
        # SEARCH
        # ==========================================

        if search:
            query += """
                WHERE
                    c.categoryID LIKE ?
                    OR c.categoryName LIKE ?
                    OR c.description LIKE ?
            """

            search_value = f"%{search}%"

            query += """
                GROUP BY
                    c.categoryID,
                    c.categoryName,
                    c.description

                ORDER BY c.categoryName
            """

            cursor.execute(
                query,
                (
                    search_value,
                    search_value,
                    search_value
                )
            )

        else:

            query += """
                GROUP BY
                    c.categoryID,
                    c.categoryName,
                    c.description

                ORDER BY c.categoryName
            """

            cursor.execute(query)

        category_list = cursor.fetchall()

        cursor.close()
        connection.close()

        return render_template(
            "categories.html",
            categories=category_list,
            total_categories=total_categories,
            search=search
        )

    except Exception as e:

        if connection:
            connection.close()

        return f"""
        <h1>Category Error</h1>

        <p>{e}</p>

        <br>

        <a href="/">
            Back to Dashboard
        </a>
        """


# ==========================================

# ADD CATEGORY PAGE

# ==========================================

@app.route("/categories/add")
def add_category():
    return render_template(
        "add_category.html"
    )


# ==========================================

# INSERT CATEGORY

# ==========================================

@app.route("/categories/add", methods=["POST"])
def save_category():
    category_id = request.form["categoryID"].strip()
    category_name = request.form["categoryName"].strip()
    description = request.form.get(
        "description",
        ""
    ).strip() or None

    connection = get_db_connection()

    if not connection:
        return "Database connection failed."

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO category
            (
                categoryID,
                categoryName,
                description
            )

            VALUES (?, ?, ?)
        """, (
            category_id,
            category_name,
            description
        ))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(
            url_for("categories")
        )

    except Exception as e:
        if connection:
            connection.rollback()
            connection.close()

        return f"""
        <h1>Could Not Add Category</h1>

        <p>{e}</p>

        <br>

        <a href="/categories/add">
            Go Back
        </a>
        """


# ==========================================

# EDIT CATEGORY PAGE

# ==========================================

@app.route("/categories/edit/<category_id>")
def edit_category(category_id):
    connection = get_db_connection()

    if not connection:
        return "Database connection failed."

    try:

        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                categoryID,
                categoryName,
                description
            FROM category
            WHERE categoryID = ?
        """, (
            category_id,
        ))

        category = cursor.fetchone()

        cursor.close()
        connection.close()

        if not category:

            return """
            <h1>Category Not Found</h1>

            <p>
                The category does not exist.
            </p>

            <br>

            <a href="/categories">
                Back to Categories
            </a>
            """

        return render_template(
            "edit_category.html",
            category=category
        )

    except (ValueError, KeyError, TypeError) as e:

        if connection:
            connection.close()

        return f"""
        <h1>Category Error</h1>

        <p>{e}</p>

        <br>

        <a href="/categories">
            Back to Categories
        </a>
        """


# ==========================================

# UPDATE CATEGORY

# ==========================================

@app.route("/categories/edit/<category_id>", methods=["POST"])
def update_category(category_id):
    category_name = request.form["categoryName"].strip()

    description = request.form.get(
        "description",
        ""
    ).strip() or None

    connection = get_db_connection()

    if not connection:
        return "Database connection failed."

    try:
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE category

            SET
                categoryName = ?,
                description = ?

            WHERE categoryID = ?
        """, (
            category_name,
            description,
            category_id
        ))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(
            url_for("categories")
        )

    except Exception as e:

        if connection:
            connection.rollback()
            connection.close()

        return f"""
        <h1>Could Not Update Category</h1>

        <p>{e}</p>

        <br>

        <a href="/categories/edit/{category_id}">
            Go Back
        </a>
        """


# ==========================================

# DELETE CATEGORY

# ==========================================

@app.route("/categories/delete/<category_id>", methods=["POST"])
def delete_category(category_id):

    connection = get_db_connection()

    if not connection:
        return "Database connection failed."

    try:

        cursor = connection.cursor()

        # ==========================================
        # CHECK WHETHER CATEGORY HAS PRODUCTS
        # ==========================================

        cursor.execute("""
            SELECT COUNT(*)
            FROM product
            WHERE categoryID = ?
        """, (
            category_id,
        ))

        product_count = cursor.fetchone()[0]

        # ==========================================
        # DO NOT DELETE CATEGORY WITH PRODUCTS
        # ==========================================

        if product_count > 0:

            cursor.close()
            connection.close()

            return """
            <h1>Cannot Delete Category</h1>

            <p>
                This category contains products.
            </p>

            <p>
                Remove or move the products to another
                category before deleting this category.
            </p>

            <br>

            <a href="/categories">
                Back to Categories
            </a>
            """

        # ==========================================
        # DELETE CATEGORY
        # ==========================================

        cursor.execute("""
            DELETE FROM category
            WHERE categoryID = ?
        """, (
            category_id,
        ))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(
            url_for("categories")
        )

    except Exception as e:

        if connection:
            connection.rollback()
            connection.close()

        return f"""
        <h1>Could Not Delete Category</h1>

        <p>{e}</p>

        <br>

        <a href="/categories">
            Back to Categories
        </a>
        """

# =========================================================
# SUPPLIERS
# =========================================================

@app.route("/suppliers")
def suppliers():

    search = request.args.get("search", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        if search:

            query = """
                SELECT
                    supplierID,
                    supplierName,
                    phoneNo,
                    email,
                    address,
                    city
                FROM supplier
                WHERE
                    supplierID LIKE %s
                    OR supplierName LIKE %s
                    OR phoneNo LIKE %s
                    OR email LIKE %s
                    OR address LIKE %s
                    OR city LIKE %s
                ORDER BY supplierName
            """

            search_value = f"%{search}%"

            cursor.execute(
                query,
                (
                    search_value,
                    search_value,
                    search_value,
                    search_value,
                    search_value,
                    search_value
                )
            )

        else:

            cursor.execute("""
                SELECT
                    supplierID,
                    supplierName,
                    phoneNo,
                    email,
                    address,
                    city
                FROM supplier
                ORDER BY supplierName
            """)

        suppliers_list = cursor.fetchall()

        return render_template(
            "suppliers.html",
            suppliers=suppliers_list,
            search=search
        )

    finally:

        cursor.close()
        conn.close()


# =========================================================
# ADD SUPPLIER
# =========================================================

@app.route("/suppliers/add")
def add_supplier():

    return render_template(
        "add_supplier.html"
    )


# =========================================================
# SAVE SUPPLIER
# =========================================================

@app.route("/suppliers/save", methods=["POST"])
def save_supplier():

    supplier_id = request.form.get("supplierID", "").strip()
    supplier_name = request.form.get("supplierName", "").strip()
    phone_no = request.form.get("phoneNo", "").strip()
    email = request.form.get("email", "").strip()
    address = request.form.get("address", "").strip()
    city = request.form.get("city", "").strip()

    # -----------------------------------------------------
    # BASIC VALIDATION
    # -----------------------------------------------------

    if not supplier_id:
        return render_template(
            "add_supplier.html",
            error="Supplier ID is required."
        )

    if not supplier_name:
        return render_template(
            "add_supplier.html",
            error="Supplier name is required."
        )

    if not phone_no:
        return render_template(
            "add_supplier.html",
            error="Phone number is required."
        )

    if not address:
        return render_template(
            "add_supplier.html",
            error="Address is required."
        )

    if not city:
        return render_template(
            "add_supplier.html",
            error="City is required."
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        # Convert empty email to NULL
        if email == "":
            email = None

        cursor.execute(
            """
            INSERT INTO supplier
            (
                supplierID,
                supplierName,
                phoneNo,
                email,
                address,
                city
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                supplier_id,
                supplier_name,
                phone_no,
                email,
                address,
                city
            )
        )

        conn.commit()

        return redirect("/suppliers")

    except Exception as e:

        conn.rollback()

        error_message = str(e)

        if "Duplicate entry" in error_message:

            if "supplierID" in error_message:

                error_message = (
                    "A supplier with this Supplier ID already exists."
                )

            elif "phoneNo" in error_message:

                error_message = (
                    "A supplier with this phone number already exists."
                )

            elif "email" in error_message:

                error_message = (
                    "A supplier with this email already exists."
                )

            else:

                error_message = (
                    "A supplier with the provided information already exists."
                )

        return render_template(
            "add_supplier.html",
            error=error_message
        )

    finally:

        cursor.close()
        conn.close()


# =========================================================
# EDIT SUPPLIER
# =========================================================

@app.route("/suppliers/edit/<supplier_id>")
def edit_supplier(supplier_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT
                supplierID,
                supplierName,
                phoneNo,
                email,
                address,
                city
            FROM supplier
            WHERE supplierID = %s
            """,
            (supplier_id,)
        )

        supplier = cursor.fetchone()

        if not supplier:

            return redirect("/suppliers")

        return render_template(
            "edit_supplier.html",
            supplier=supplier
        )

    finally:

        cursor.close()
        conn.close()


# =========================================================
# UPDATE SUPPLIER
# =========================================================

@app.route(
    "/suppliers/update/<supplier_id>",
    methods=["POST"]
)
def update_supplier(supplier_id):

    supplier_name = request.form.get(
        "supplierName",
        ""
    ).strip()

    phone_no = request.form.get(
        "phoneNo",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip()

    address = request.form.get(
        "address",
        ""
    ).strip()

    city = request.form.get(
        "city",
        ""
    ).strip()

    if not supplier_name:
        return redirect(
            f"/suppliers/edit/{supplier_id}"
        )

    if not phone_no:
        return redirect(
            f"/suppliers/edit/{supplier_id}"
        )

    if not address:
        return redirect(
            f"/suppliers/edit/{supplier_id}"
        )

    if not city:
        return redirect(
            f"/suppliers/edit/{supplier_id}"
        )

    if email == "":
        email = None

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            UPDATE supplier
            SET
                supplierName = %s,
                phoneNo = %s,
                email = %s,
                address = %s,
                city = %s
            WHERE supplierID = %s
            """,
            (
                supplier_name,
                phone_no,
                email,
                address,
                city,
                supplier_id
            )
        )

        conn.commit()

        return redirect("/suppliers")

    except Exception as e:

        conn.rollback()

        print(
            "Error updating supplier:",
            e
        )

        return redirect(
            f"/suppliers/edit/{supplier_id}"
        )

    finally:

        cursor.close()
        conn.close()


# =========================================================
# DELETE SUPPLIER
# =========================================================

@app.route(
    "/suppliers/delete/<supplier_id>",
    methods=["POST"]
)
def delete_supplier(supplier_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            DELETE FROM supplier
            WHERE supplierID = %s
            """,
            (supplier_id,)
        )

        conn.commit()

        return redirect("/suppliers")

    except Exception as e:

        conn.rollback()

        print(
            "Error deleting supplier:",
            e
        )

        return redirect("/suppliers")

    finally:

        cursor.close()
        conn.close()
        

# =========================================================
# DISCOUNTS
# =========================================================

@app.route("/discounts")
def discounts():

    search = request.args.get("search", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        if search:

            query = """
                SELECT
                    discountID,
                    discountName,
                    discountPercent,
                    startDate,
                    endDate,
                    discountType,
                    fixedAmount
                FROM Discount
                WHERE
                    discountID LIKE %s
                    OR discountName LIKE %s
                    OR discountType LIKE %s
                ORDER BY startDate DESC
            """

            search_value = f"%{search}%"

            cursor.execute(
                query,
                (
                    search_value,
                    search_value,
                    search_value
                )
            )

        else:

            cursor.execute("""
                SELECT
                    discountID,
                    discountName,
                    discountPercent,
                    startDate,
                    endDate,
                    discountType,
                    fixedAmount
                FROM Discount
                ORDER BY startDate DESC
            """)

        discounts_list = cursor.fetchall()

        return render_template(
            "discounts.html",
            discounts=discounts_list,
            search=search
        )

    finally:

        cursor.close()
        conn.close()


# =========================================================
# ADD DISCOUNT
# =========================================================

@app.route("/discounts/add")
def add_discount():

    return render_template(
        "add_discount.html"
    )


# =========================================================
# SAVE DISCOUNT
# =========================================================

@app.route("/discounts/save", methods=["POST"])
def save_discount():

    discount_id = request.form.get(
        "discountID",
        ""
    ).strip()

    discount_name = request.form.get(
        "discountName",
        ""
    ).strip()

    discount_percent = request.form.get(
        "discountPercent",
        "0"
    ).strip()

    start_date = request.form.get(
        "startDate",
        ""
    ).strip()

    end_date = request.form.get(
        "endDate",
        ""
    ).strip()

    discount_type = request.form.get(
        "discountType",
        "Percentage"
    ).strip()

    fixed_amount = request.form.get(
        "fixedAmount",
        "0"
    ).strip()


    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if not discount_id:
        return render_template(
            "add_discount.html",
            error="Discount ID is required."
        )

    if not discount_name:
        return render_template(
            "add_discount.html",
            error="Discount name is required."
        )

    if not start_date:
        return render_template(
            "add_discount.html",
            error="Start date is required."
        )

    if not end_date:
        return render_template(
            "add_discount.html",
            error="End date is required."
        )

    if discount_type not in [
        "Percentage",
        "Fixed"
    ]:

        return render_template(
            "add_discount.html",
            error="Invalid discount type."
        )


    # -----------------------------------------------------
    # CONVERT NUMERIC VALUES
    # -----------------------------------------------------

    try:

        discount_percent = float(
            discount_percent or 0
        )

        fixed_amount = float(
            fixed_amount or 0
        )

    except ValueError:

        return render_template(
            "add_discount.html",
            error="Discount values must be valid numbers."
        )


    # -----------------------------------------------------
    # TYPE VALIDATION
    # -----------------------------------------------------

    if discount_type == "Percentage":

        if discount_percent < 0 or discount_percent > 100:

            return render_template(
                "add_discount.html",
                error="Percentage discount must be between 0 and 100."
            )

        fixed_amount = 0


    elif discount_type == "Fixed":

        if fixed_amount < 0:

            return render_template(
                "add_discount.html",
                error="Fixed discount cannot be negative."
            )

        discount_percent = 0


    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO Discount
            (
                discountID,
                discountName,
                discountPercent,
                startDate,
                endDate,
                discountType,
                fixedAmount
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                discount_id,
                discount_name,
                discount_percent,
                start_date,
                end_date,
                discount_type,
                fixed_amount
            )
        )

        conn.commit()

        return redirect("/discounts")

    except Exception as e:

        conn.rollback()

        error_message = str(e)

        if "Duplicate entry" in error_message:

            error_message = (
                "A discount with this ID already exists."
            )

        return render_template(
            "add_discount.html",
            error=error_message
        )

    finally:

        cursor.close()
        conn.close()


# =========================================================
# EDIT DISCOUNT
# =========================================================

@app.route("/discounts/edit/<discount_id>")
def edit_discount(discount_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT
                discountID,
                discountName,
                discountPercent,
                startDate,
                endDate,
                discountType,
                fixedAmount
            FROM Discount
            WHERE discountID = %s
            """,
            (discount_id,)
        )

        discount = cursor.fetchone()

        if not discount:

            return redirect("/discounts")

        return render_template(
            "edit_discount.html",
            discount=discount
        )

    finally:

        cursor.close()
        conn.close()


# =========================================================
# UPDATE DISCOUNT
# =========================================================

@app.route(
    "/discounts/update/<discount_id>",
    methods=["POST"]
)
def update_discount(discount_id):

    discount_name = request.form.get(
        "discountName",
        ""
    ).strip()

    discount_percent = request.form.get(
        "discountPercent",
        "0"
    ).strip()

    start_date = request.form.get(
        "startDate",
        ""
    ).strip()

    end_date = request.form.get(
        "endDate",
        ""
    ).strip()

    discount_type = request.form.get(
        "discountType",
        "Percentage"
    ).strip()

    fixed_amount = request.form.get(
        "fixedAmount",
        "0"
    ).strip()


    if not discount_name:

        return redirect(
            f"/discounts/edit/{discount_id}"
        )

    if not start_date:

        return redirect(
            f"/discounts/edit/{discount_id}"
        )

    if not end_date:

        return redirect(
            f"/discounts/edit/{discount_id}"
        )


    try:

        discount_percent = float(
            discount_percent or 0
        )

        fixed_amount = float(
            fixed_amount or 0
        )

    except ValueError:

        return redirect(
            f"/discounts/edit/{discount_id}"
        )


    if discount_type == "Percentage":

        if discount_percent < 0 or discount_percent > 100:

            return redirect(
                f"/discounts/edit/{discount_id}"
            )

        fixed_amount = 0


    elif discount_type == "Fixed":

        if fixed_amount < 0:

            return redirect(
                f"/discounts/edit/{discount_id}"
            )

        discount_percent = 0


    else:

        return redirect(
            f"/discounts/edit/{discount_id}"
        )


    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            UPDATE Discount
            SET
                discountName = %s,
                discountPercent = %s,
                startDate = %s,
                endDate = %s,
                discountType = %s,
                fixedAmount = %s
            WHERE discountID = %s
            """,
            (
                discount_name,
                discount_percent,
                start_date,
                end_date,
                discount_type,
                fixed_amount,
                discount_id
            )
        )

        conn.commit()

        return redirect("/discounts")

    except Exception as e:

        conn.rollback()

        print(
            "Error updating discount:",
            e
        )

        return redirect(
            f"/discounts/edit/{discount_id}"
        )

    finally:

        cursor.close()
        conn.close()


# =========================================================
# DELETE DISCOUNT
# =========================================================

@app.route(
    "/discounts/delete/<discount_id>",
    methods=["POST"]
)
def delete_discount(discount_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            DELETE FROM Discount
            WHERE discountID = %s
            """,
            (discount_id,)
        )

        conn.commit()

        return redirect("/discounts")

    except Exception as e:

        conn.rollback()

        print(
            "Error deleting discount:",
            e
        )

        return redirect("/discounts")

    finally:

        cursor.close()
        conn.close()
        
# =========================================================
# LOYALTY CARDS
# =========================================================


# =========================================================
# VIEW LOYALTY CARDS
# =========================================================

@app.route("/loyalty-cards")
def loyalty_cards():

    search = request.args.get("search", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        if search:

            query = """
                SELECT
                    l.cardID,
                    l.customerID,
                    l.points,
                    l.issueDate,
                    l.expiryDate,
                    l.status,
                    c.fName,
                    c.lName,
                    c.phone
                FROM LoyaltyCard l
                INNER JOIN Customer c
                    ON l.customerID = c.customerID
                WHERE
                    l.cardID LIKE %s
                    OR l.customerID LIKE %s
                    OR c.fName LIKE %s
                    OR c.lName LIKE %s
                    OR c.phone LIKE %s
                ORDER BY l.cardID
            """

            search_value = f"%{search}%"

            cursor.execute(
                query,
                (
                    search_value,
                    search_value,
                    search_value,
                    search_value,
                    search_value
                )
            )

        else:

            cursor.execute("""
                SELECT
                    l.cardID,
                    l.customerID,
                    l.points,
                    l.issueDate,
                    l.expiryDate,
                    l.status,
                    c.fName,
                    c.lName,
                    c.phone
                FROM LoyaltyCard l
                INNER JOIN Customer c
                    ON l.customerID = c.customerID
                ORDER BY l.cardID
            """)

        loyalty_cards_list = cursor.fetchall()

        return render_template(
            "loyalty_cards.html",
            loyalty_cards=loyalty_cards_list,
            search=search
        )

    except Exception as e:

        print("Error loading loyalty cards:", e)

        return render_template(
            "loyalty_cards.html",
            loyalty_cards=[],
            search=search,
            error=str(e)
        )

    finally:

        cursor.close()
        conn.close()


# =========================================================
# ADD LOYALTY CARD PAGE
# =========================================================

@app.route("/loyalty-cards/add")
def add_loyalty_card():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        # Get customers who do not already have a loyalty card
        cursor.execute("""
            SELECT
                c.customerID,
                c.fName,
                c.lName
            FROM Customer c
            LEFT JOIN LoyaltyCard l
                ON c.customerID = l.customerID
            WHERE l.customerID IS NULL
            ORDER BY c.fName, c.lName
        """)

        customers = cursor.fetchall()

        return render_template(
            "add_loyalty_card.html",
            customers=customers
        )

    except Exception as e:

        print("Error loading add loyalty card page:", e)

        return render_template(
            "add_loyalty_card.html",
            customers=[],
            error=str(e)
        )

    finally:

        cursor.close()
        conn.close()


# =========================================================
# SAVE LOYALTY CARD
# =========================================================

@app.route(
    "/loyalty-cards/save",
    methods=["POST"]
)
def save_loyalty_card():

    card_id = request.form.get(
        "cardID",
        ""
    ).strip()

    customer_id = request.form.get(
        "customerID",
        ""
    ).strip()

    points = request.form.get(
        "points",
        "0"
    ).strip()

    issue_date = request.form.get(
        "issueDate",
        ""
    ).strip()

    expiry_date = request.form.get(
        "expiryDate",
        ""
    ).strip()

    status = request.form.get(
        "status",
        "Active"
    ).strip()


    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if not card_id:

        return redirect(
            "/loyalty-cards/add"
        )

    if not customer_id:

        return redirect(
            "/loyalty-cards/add"
        )

    if not issue_date:

        return redirect(
            "/loyalty-cards/add"
        )

    if not expiry_date:

        return redirect(
            "/loyalty-cards/add"
        )

    if not points:

        points = 0


    # -----------------------------------------------------
    # INSERT
    # -----------------------------------------------------

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO LoyaltyCard
            (
                cardID,
                customerID,
                points,
                issueDate,
                expiryDate,
                status
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                card_id,
                customer_id,
                points,
                issue_date,
                expiry_date,
                status
            )
        )

        conn.commit()

        return redirect(
            "/loyalty-cards"
        )

    except Exception as e:

        conn.rollback()

        print(
            "Error saving loyalty card:",
            e
        )

        return redirect(
            "/loyalty-cards/add"
        )

    finally:

        cursor.close()
        conn.close()


# =========================================================
# EDIT LOYALTY CARD
# =========================================================

@app.route(
    "/loyalty-cards/edit/<card_id>"
)
def edit_loyalty_card(card_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        # Get loyalty card
        cursor.execute(
            """
            SELECT
                cardID,
                customerID,
                points,
                issueDate,
                expiryDate,
                status
            FROM LoyaltyCard
            WHERE cardID = %s
            """,
            (card_id,)
        )

        card = cursor.fetchone()

        if not card:

            return redirect(
                "/loyalty-cards"
            )


        # Get all customers
        cursor.execute("""
            SELECT
                customerID,
                fName,
                lName
            FROM Customer
            ORDER BY fName, lName
        """)

        customers = cursor.fetchall()


        return render_template(
            "edit_loyalty_card.html",
            card=card,
            customers=customers
        )

    except Exception as e:

        print(
            "Error loading loyalty card:",
            e
        )

        return redirect(
            "/loyalty-cards"
        )

    finally:

        cursor.close()
        conn.close()


# =========================================================
# UPDATE LOYALTY CARD
# =========================================================

@app.route(
    "/loyalty-cards/update/<card_id>",
    methods=["POST"]
)
def update_loyalty_card(card_id):

    customer_id = request.form.get(
        "customerID",
        ""
    ).strip()

    points = request.form.get(
        "points",
        "0"
    ).strip()

    issue_date = request.form.get(
        "issueDate",
        ""
    ).strip()

    expiry_date = request.form.get(
        "expiryDate",
        ""
    ).strip()

    status = request.form.get(
        "status",
        "Active"
    ).strip()


    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if not customer_id:

        return redirect(
            f"/loyalty-cards/edit/{card_id}"
        )

    if not issue_date:

        return redirect(
            f"/loyalty-cards/edit/{card_id}"
        )

    if not expiry_date:

        return redirect(
            f"/loyalty-cards/edit/{card_id}"
        )

    if not points:

        points = 0


    # -----------------------------------------------------
    # UPDATE
    # -----------------------------------------------------

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            UPDATE LoyaltyCard
            SET
                customerID = %s,
                points = %s,
                issueDate = %s,
                expiryDate = %s,
                status = %s
            WHERE cardID = %s
            """,
            (
                customer_id,
                points,
                issue_date,
                expiry_date,
                status,
                card_id
            )
        )

        conn.commit()

        return redirect(
            "/loyalty-cards"
        )

    except Exception as e:

        conn.rollback()

        print(
            "Error updating loyalty card:",
            e
        )

        return redirect(
            f"/loyalty-cards/edit/{card_id}"
        )

    finally:

        cursor.close()
        conn.close()


# =========================================================
# DELETE LOYALTY CARD
# =========================================================

@app.route(
    "/loyalty-cards/delete/<card_id>",
    methods=["POST"]
)
def delete_loyalty_card(card_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            DELETE FROM LoyaltyCard
            WHERE cardID = %s
            """,
            (card_id,)
        )

        conn.commit()

        return redirect(
            "/loyalty-cards"
        )

    except Exception as e:

        conn.rollback()

        print(
            "Error deleting loyalty card:",
            e
        )

        return redirect(
            "/loyalty-cards"
        )

    finally:

        cursor.close()
        conn.close()
        
# =========================================================
# SALES
# =========================================================

# =========================================================
# VIEW SALES
# =========================================================

@app.route("/sales")
def sales():

    search = request.args.get("search", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        if search:

            query = """
                SELECT
                    s.saleID,
                    s.saleDate,
                    s.customerID,
                    s.employeeID,
                    s.totalAmount,
                    s.paymentMethod,
                    s.taxAmount,
                    s.pointsRedeemed,

                    CONCAT(c.fName, ' ', c.lName) AS customerName,

                    CONCAT(e.fName, ' ', e.lName) AS employeeName

                FROM Sale s

                LEFT JOIN Customer c
                    ON s.customerID = c.customerID

                INNER JOIN Employee e
                    ON s.employeeID = e.employeeID

                WHERE
                    s.saleID LIKE %s
                    OR s.customerID LIKE %s
                    OR s.employeeID LIKE %s
                    OR s.paymentMethod LIKE %s
                    OR CONCAT(c.fName, ' ', c.lName) LIKE %s
                    OR CONCAT(e.fName, ' ', e.lName) LIKE %s

                ORDER BY s.saleDate DESC
            """

            search_value = f"%{search}%"

            cursor.execute(
                query,
                (
                    search_value,
                    search_value,
                    search_value,
                    search_value,
                    search_value,
                    search_value
                )
            )

        else:

            cursor.execute("""
                SELECT
                    s.saleID,
                    s.saleDate,
                    s.customerID,
                    s.employeeID,
                    s.totalAmount,
                    s.paymentMethod,
                    s.taxAmount,
                    s.pointsRedeemed,

                    CONCAT(c.fName, ' ', c.lName) AS customerName,

                    CONCAT(e.fName, ' ', e.lName) AS employeeName

                FROM Sale s

                LEFT JOIN Customer c
                    ON s.customerID = c.customerID

                INNER JOIN Employee e
                    ON s.employeeID = e.employeeID

                ORDER BY s.saleDate DESC
            """)

        sales_list = cursor.fetchall()

        return render_template(
            "sales.html",
            sales=sales_list,
            search=search
        )

    except Exception as e:

        print("Error loading sales:", e)

        return render_template(
            "sales.html",
            sales=[],
            search=search,
            error=str(e)
        )

    finally:

        cursor.close()
        conn.close()


# =========================================================
# ADD SALE PAGE
# =========================================================

@app.route("/sales/add")
def add_sale():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        # -------------------------------------------------
        # GET EMPLOYEES
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                employeeID,
                fName,
                lName
            FROM Employee
            ORDER BY fName, lName
        """)

        employees = cursor.fetchall()


        # -------------------------------------------------
        # GET CUSTOMERS
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                customerID,
                fName,
                lName
            FROM Customer
            ORDER BY fName, lName
        """)

        customers = cursor.fetchall()


        # -------------------------------------------------
        # GET PRODUCTS
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                p.productID,
                p.productName,
                p.unitPrice
            FROM Product p

            INNER JOIN Inventory i
                ON p.productID = i.productID

            WHERE i.quantity > 0

            ORDER BY p.productName
        """)

        products = cursor.fetchall()


        return render_template(
            "add_sale.html",
            employees=employees,
            customers=customers,
            products=products
        )

    except Exception as e:

        print("Error loading add sale page:", e)

        return render_template(
            "add_sale.html",
            employees=[],
            customers=[],
            products=[],
            error=str(e)
        )

    finally:

        cursor.close()
        conn.close()


def get_employees_for_sale():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                employeeID,
                fName,
                lName
            FROM Employee
            ORDER BY fName, lName
        """)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_customers_for_sale():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                customerID,
                fName,
                lName
            FROM Customer
            ORDER BY fName, lName
        """)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_products_for_sale():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                p.productID,
                p.productName,
                p.unitPrice
            FROM Product p

            INNER JOIN Inventory i
                ON p.productID = i.productID

            WHERE i.quantity > 0

            ORDER BY p.productName
        """)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


@app.route(
    "/sales/save",
    methods=["POST"]
)
def save_sale():

    # -----------------------------------------------------
    # GET FORM DATA
    # -----------------------------------------------------

    sale_id = request.form.get("saleID", "").strip()
    employee_id = request.form.get("employeeID", "").strip()
    customer_id = request.form.get("customerID", "").strip()
    payment_method = request.form.get("paymentMethod", "").strip()
    product_id = request.form.get("productID", "").strip()

    quantity_text = request.form.get("quantity", "").strip()
    discount_text = request.form.get("discount", "0").strip()
    points_text = request.form.get("pointsRedeemed", "0").strip()


    # -----------------------------------------------------
    # BASIC VALIDATION
    # -----------------------------------------------------

    if not sale_id:
        return render_template(
            "add_sale.html",
            employees=get_employees_for_sale(),
            customers=get_customers_for_sale(),
            products=get_products_for_sale(),
            error="Sale ID is required."
        )

    if not employee_id:
        return render_template(
            "add_sale.html",
            employees=get_employees_for_sale(),
            customers=get_customers_for_sale(),
            products=get_products_for_sale(),
            error="Please select an employee."
        )

    if not payment_method:
        return render_template(
            "add_sale.html",
            employees=get_employees_for_sale(),
            customers=get_customers_for_sale(),
            products=get_products_for_sale(),
            error="Please select a payment method."
        )

    if not product_id:
        return render_template(
            "add_sale.html",
            employees=get_employees_for_sale(),
            customers=get_customers_for_sale(),
            products=get_products_for_sale(),
            error="Please select a product."
        )


    # -----------------------------------------------------
    # CONVERT NUMERIC VALUES
    # -----------------------------------------------------

    try:

        quantity = int(quantity_text)

        if quantity <= 0:
            raise ValueError

    except ValueError:

        return render_template(
            "add_sale.html",
            employees=get_employees_for_sale(),
            customers=get_customers_for_sale(),
            products=get_products_for_sale(),
            error="Quantity must be a positive whole number."
        )


    try:

        discount = float(discount_text or 0)

        if discount < 0 or discount > 100:
            raise ValueError

    except ValueError:

        return render_template(
            "add_sale.html",
            employees=get_employees_for_sale(),
            customers=get_customers_for_sale(),
            products=get_products_for_sale(),
            error="Discount must be between 0 and 100."
        )


    try:

        points_redeemed = int(points_text or 0)

        if points_redeemed < 0:
            raise ValueError

    except ValueError:

        return render_template(
            "add_sale.html",
            employees=get_employees_for_sale(),
            customers=get_customers_for_sale(),
            products=get_products_for_sale(),
            error="Points redeemed cannot be negative."
        )


    # Empty customer means walk-in customer
    if customer_id == "":
        customer_id = None


    # -----------------------------------------------------
    # DATABASE CONNECTION
    # -----------------------------------------------------

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        # -------------------------------------------------
        # 1. CHECK SALE ID
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT saleID
            FROM Sale
            WHERE saleID = %s
            """,
            (sale_id,)
        )

        if cursor.fetchone():

            return render_template(
                "add_sale.html",
                employees=get_employees_for_sale(),
                customers=get_customers_for_sale(),
                products=get_products_for_sale(),
                error=f"Sale ID '{sale_id}' already exists."
            )


        # -------------------------------------------------
        # 2. CHECK EMPLOYEE
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT employeeID
            FROM Employee
            WHERE employeeID = %s
            """,
            (employee_id,)
        )

        employee = cursor.fetchone()

        if not employee:

            return render_template(
                "add_sale.html",
                employees=get_employees_for_sale(),
                customers=get_customers_for_sale(),
                products=get_products_for_sale(),
                error=f"Employee '{employee_id}' does not exist."
            )


        # -------------------------------------------------
        # 3. CHECK CUSTOMER
        # -------------------------------------------------

        if customer_id:

            cursor.execute(
                """
                SELECT customerID
                FROM Customer
                WHERE customerID = %s
                """,
                (customer_id,)
            )

            customer = cursor.fetchone()

            if not customer:

                return render_template(
                    "add_sale.html",
                    employees=get_employees_for_sale(),
                    customers=get_customers_for_sale(),
                    products=get_products_for_sale(),
                    error=f"Customer '{customer_id}' does not exist."
                )


        # -------------------------------------------------
        # 4. GET PRODUCT AND INVENTORY
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                p.productID,
                p.productName,
                p.unitPrice,
                i.quantity AS stockQuantity

            FROM Product p

            INNER JOIN Inventory i
                ON p.productID = i.productID

            WHERE p.productID = %s
            """,
            (product_id,)
        )

        product = cursor.fetchone()


        if not product:

            return render_template(
                "add_sale.html",
                employees=get_employees_for_sale(),
                customers=get_customers_for_sale(),
                products=get_products_for_sale(),
                error=f"Product '{product_id}' was not found or has no inventory record."
            )


        # -------------------------------------------------
        # 5. CHECK STOCK
        # -------------------------------------------------

        stock_quantity = int(
            product["stockQuantity"] or 0
        )


        if stock_quantity < quantity:

            return render_template(
                "add_sale.html",
                employees=get_employees_for_sale(),
                customers=get_customers_for_sale(),
                products=get_products_for_sale(),
                error=(
                    f"Insufficient stock for "
                    f"{product['productName']}. "
                    f"Available: {stock_quantity}, "
                    f"Requested: {quantity}."
                )
            )


        # -------------------------------------------------
        # 6. GET UNIT PRICE
        # -------------------------------------------------

        unit_price = float(
            product["unitPrice"]
        )


        # -------------------------------------------------
        # 7. CALCULATE SALE
        # -------------------------------------------------

        gross_amount = unit_price * quantity

        discount_amount = (
            gross_amount * discount / 100
        )

        subtotal = (
            gross_amount - discount_amount
        )


        # Your existing database sales use 3% tax
        tax_amount = subtotal * 0.03

        total_amount = subtotal + tax_amount


        # -------------------------------------------------
        # 8. INSERT SALE
        # -------------------------------------------------

        cursor.execute(
            """
            INSERT INTO Sale
            (
                saleID,
                customerID,
                employeeID,
                saleDate,
                totalAmount,
                paymentMethod,
                taxAmount,
                pointsRedeemed
            )
            VALUES
            (
                %s,
                %s,
                %s,
                CURRENT_TIMESTAMP,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                sale_id,
                customer_id,
                employee_id,
                total_amount,
                payment_method,
                tax_amount,
                points_redeemed
            )
        )


        # -------------------------------------------------
        # 9. INSERT SALE ITEM
        # -------------------------------------------------

        cursor.execute(
            """
            INSERT INTO SaleItem
            (
                saleID,
                productID,
                quantity,
                unitPrice,
                discount
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                sale_id,
                product_id,
                quantity,
                unit_price,
                discount
            )
        )


        # -------------------------------------------------
        # 10. COMMIT EVERYTHING
        # -------------------------------------------------

        conn.commit()


        # -------------------------------------------------
        # 11. SUCCESS
        # -------------------------------------------------

        return redirect(
            f"/sales/view/{sale_id}"
        )


    except Exception as e:

        conn.rollback()

        print(
            "ERROR SAVING SALE:",
            repr(e)
        )

        return render_template(
            "add_sale.html",
            employees=get_employees_for_sale(),
            customers=get_customers_for_sale(),
            products=get_products_for_sale(),
            error=f"Unable to create sale: {str(e)}"
        )


    finally:

        cursor.close()
        conn.close()



# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)