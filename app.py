# =========================================================
# IMPORTS
# =========================================================

from services.database import get_db_connection

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from auth import (
    authenticate_user,
    get_user_role,
    login_required,
    role_required
)

app = Flask(__name__)

app.secret_key = "supermarket_management_secret_key_2026"

# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    # -----------------------------------------------------
    # ALREADY LOGGED IN
    # -----------------------------------------------------

    if "employee_id" in session:

        return redirect(
            url_for("dashboard")
        )

    # -----------------------------------------------------
    # LOGIN FORM SUBMITTED
    # -----------------------------------------------------

    if request.method == "POST":

        login_value = request.form.get(
            "employee_id",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )


        # -------------------------------------------------
        # CHECK EMPTY FIELDS
        # -------------------------------------------------

        if not login_value or not password:

            return render_template(
                "login.html",
                error="Employee ID/email and password are required."
            )


        # -------------------------------------------------
        # AUTHENTICATE USER
        # -------------------------------------------------

        user = authenticate_user(
            login_value,
            password
        )


        # -------------------------------------------------
        # LOGIN FAILED
        # -------------------------------------------------

        if user is None:

            return render_template(
                "login.html",
                error="Invalid Employee ID/email or password."
            )


        # -------------------------------------------------
        # CLEAR OLD SESSION
        # -------------------------------------------------

        session.clear()


        # -------------------------------------------------
        # CREATE USER SESSION
        # -------------------------------------------------

        session["employee_id"] = (
            user["employeeID"]
        )


        session["employee_name"] = (
            user["fName"]
            + " "
            + user["lName"]
        )


        session["position"] = (
            user["position"]
        )


        session["email"] = (
            user["email"]
        )


        session["role"] = (
            user["role"]
        )


        # -------------------------------------------------
        # LOGIN SUCCESS
        # -------------------------------------------------

        print(
            "LOGIN SUCCESS:",
            user["employeeID"],
            "ROLE:",
            user["role"]
        )


        return redirect(
            url_for("dashboard")
        )


    # -----------------------------------------------------
    # SHOW LOGIN PAGE
    # -----------------------------------------------------

    return render_template(
        "login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )
    
# =========================================================
# DASHBOARD
# =========================================================

@app.route("/")
@login_required
def dashboard():

    connection = get_db_connection()

    # -----------------------------------------------------
    # DATABASE CONNECTION FAILED
    # -----------------------------------------------------

    if not connection:

        return render_template(
            "dashboard.html",
            total_products=0,
            low_stock=0,
            total_customers=0,
            total_suppliers=0,
            total_categories=0,
            out_of_stock=0,
            error="Database connection failed."
        )

    cursor = connection.cursor()

    try:

        # -------------------------------------------------
        # TOTAL PRODUCTS
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM Product
        """)

        total_products = cursor.fetchone()[0]


        # -------------------------------------------------
        # LOW STOCK
        # Products above 0 but at or below reorder level
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM Inventory
            WHERE quantity > 0
            AND quantity <= reorderLevel
        """)

        low_stock = cursor.fetchone()[0]


        # -------------------------------------------------
        # TOTAL CUSTOMERS
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM Customer
        """)

        total_customers = cursor.fetchone()[0]


        # -------------------------------------------------
        # TOTAL SUPPLIERS
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM Supplier
        """)

        total_suppliers = cursor.fetchone()[0]


        # -------------------------------------------------
        # TOTAL CATEGORIES
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM Category
        """)

        total_categories = cursor.fetchone()[0]


        # -------------------------------------------------
        # OUT OF STOCK
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM Inventory
            WHERE quantity = 0
        """)

        out_of_stock = cursor.fetchone()[0]


        # -------------------------------------------------
        # SHOW DASHBOARD
        # -------------------------------------------------

        return render_template(
            "dashboard.html",

            total_products=total_products,

            low_stock=low_stock,

            total_customers=total_customers,

            total_suppliers=total_suppliers,

            total_categories=total_categories,

            out_of_stock=out_of_stock
        )


    except Exception as e:

        print(
            "DASHBOARD ERROR:",
            repr(e)
        )

        return render_template(
            "dashboard.html",

            total_products=0,

            low_stock=0,

            total_customers=0,

            total_suppliers=0,

            total_categories=0,

            out_of_stock=0,

            error="Could not load dashboard information."
        )


    finally:

        cursor.close()
        connection.close()
        
# =========================================================
# PRODUCTS
# =========================================================

@app.route("/products")
def products():

    connection = get_db_connection()

    search = request.args.get("search", "").strip()

    if not connection:
        return render_template(
            "products.html",
            products=[],
            search=search,
            error="Database connection failed."
        )

    cursor = connection.cursor()

    try:

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
            FROM Product p

            LEFT JOIN Category c
                ON p.categoryID = c.categoryID

            LEFT JOIN Supplier s
                ON p.supplierID = s.supplierID
        """

        params = []

        # SEARCH
        if search:

            query += """
                WHERE
                    p.productID LIKE %s
                    OR p.productName LIKE %s
                    OR c.categoryName LIKE %s
                    OR s.supplierName LIKE %s
            """

            search_value = f"%{search}%"

            params = [
                search_value,
                search_value,
                search_value,
                search_value
            ]

        query += """
            ORDER BY p.productID
        """

        cursor.execute(query, tuple(params))

        products = cursor.fetchall()

        return render_template(
            "products.html",
            products=products,
            search=search
        )

    except Exception as e:

        print("PRODUCTS ERROR:", repr(e))

        return render_template(
            "products.html",
            products=[],
            search=search,
            error=f"Could not load products: {e}"
        )

    finally:

        cursor.close()
        connection.close()


# =========================================================
# ADD PRODUCT
# =========================================================

@app.route("/products/add", methods=["GET"])
def add_product():

    connection = get_db_connection()

    if not connection:
        return "Database connection failed."

    cursor = connection.cursor()

    try:

        # GET CATEGORIES
        cursor.execute("""
            SELECT
                categoryID,
                categoryName
            FROM Category
            ORDER BY categoryName
        """)

        categories = cursor.fetchall()

        # GET SUPPLIERS
        cursor.execute("""
            SELECT
                supplierID,
                supplierName
            FROM Supplier
            ORDER BY supplierName
        """)

        suppliers = cursor.fetchall()

        return render_template(
            "add_product.html",
            categories=categories,
            suppliers=suppliers
        )

    except Exception as e:

        print("ADD PRODUCT ERROR:", repr(e))

        return f"""
        <h1>Could Not Open Add Product</h1>
        <p>{e}</p>
        <a href="/products">Back to Products</a>
        """

    finally:

        cursor.close()
        connection.close()


# =========================================================
# SAVE PRODUCT
# =========================================================

@app.route("/products/add", methods=["POST"])
@login_required
def save_product():

    product_id = request.form.get("productID", "").strip()
    product_name = request.form.get("productName", "").strip()
    category_id = request.form.get("categoryID", "").strip()
    supplier_id = request.form.get("supplierID", "").strip()
    unit_price = request.form.get("unitPrice", "").strip()
    cost_price = request.form.get("costPrice", "").strip()
    expiry_date = request.form.get("expiryDate") or None
    status = request.form.get("status", "").strip()
    barcode = request.form.get("barcode") or None

    if not product_id or not product_name:

        return "Product ID and Product Name are required."

    connection = get_db_connection()

    if not connection:
        return "Database connection failed."

    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT productID
            FROM Product
            WHERE productID = %s
        """, (product_id,))

        if cursor.fetchone():

            return f"""
            <h1>Product Already Exists</h1>

            <p>
                Product ID <strong>{product_id}</strong>
                already exists.
            </p>

            <a href="/products/add">
                Go Back
            </a>
            """

        cursor.execute("""
            INSERT INTO Product
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
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """, (
            product_id,
            category_id,
            supplier_id,
            product_name,
            unit_price,
            cost_price,
            expiry_date,
            status,
            barcode
        ))

        connection.commit()

        return redirect(url_for("products"))

    except Exception as e:

        connection.rollback()

        print("SAVE PRODUCT ERROR:", repr(e))

        return f"""
        <h1>Could Not Add Product</h1>

        <p>{e}</p>

        <br>

        <a href="/products/add">
            Go Back
        </a>
        """

    finally:

        cursor.close()
        connection.close()


# =========================================================
# EDIT PRODUCT
# =========================================================

@app.route("/products/edit/<product_id>", methods=["GET"])
@login_required
def edit_product(product_id):

    connection = get_db_connection()

    if not connection:
        return "Database connection failed."

    cursor = connection.cursor()

    try:

        # GET PRODUCT
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
            FROM Product
            WHERE productID = %s
        """, (product_id,))

        product = cursor.fetchone()

        if not product:

            return f"""
            <h1>Product Not Found</h1>

            <p>
                Product <strong>{product_id}</strong>
                does not exist.
            </p>

            <a href="/products">
                Back to Products
            </a>
            """

        # GET CATEGORIES
        cursor.execute("""
            SELECT
                categoryID,
                categoryName
            FROM Category
            ORDER BY categoryName
        """)

        categories = cursor.fetchall()

        # GET SUPPLIERS
        cursor.execute("""
            SELECT
                supplierID,
                supplierName
            FROM Supplier
            ORDER BY supplierName
        """)

        suppliers = cursor.fetchall()

        return render_template(
            "edit_product.html",
            product=product,
            categories=categories,
            suppliers=suppliers
        )

    except Exception as e:

        print("EDIT PRODUCT ERROR:", repr(e))

        return f"""
        <h1>Could Not Edit Product</h1>

        <p>{e}</p>

        <a href="/products">
            Back to Products
        </a>
        """

    finally:

        cursor.close()
        connection.close()


# =========================================================
# UPDATE PRODUCT
# =========================================================

@app.route("/products/edit/<product_id>", methods=["POST"])
@login_required
def update_product(product_id):

    product_name = request.form.get("productName", "").strip()
    category_id = request.form.get("categoryID", "").strip()
    supplier_id = request.form.get("supplierID", "").strip()
    unit_price = request.form.get("unitPrice", "").strip()
    cost_price = request.form.get("costPrice", "").strip()
    expiry_date = request.form.get("expiryDate") or None
    status = request.form.get("status", "").strip()
    barcode = request.form.get("barcode") or None

    connection = get_db_connection()

    if not connection:
        return "Database connection failed."

    cursor = connection.cursor()

    try:

        cursor.execute("""
            UPDATE Product
            SET
                categoryID = %s,
                supplierID = %s,
                productName = %s,
                unitPrice = %s,
                costPrice = %s,
                expiryDate = %s,
                status = %s,
                barcode = %s
            WHERE productID = %s
        """, (
            category_id,
            supplier_id,
            product_name,
            unit_price,
            cost_price,
            expiry_date,
            status,
            barcode,
            product_id
        ))

        connection.commit()

        return redirect(url_for("products"))

    except Exception as e:

        connection.rollback()

        print("UPDATE PRODUCT ERROR:", repr(e))

        return f"""
        <h1>Could Not Update Product</h1>

        <p>{e}</p>

        <br>

        <a href="/products/edit/{product_id}">
            Go Back
        </a>
        """

    finally:

        cursor.close()
        connection.close()


# =========================================================
# DELETE / DISCONTINUE PRODUCT
# =========================================================

@app.route("/products/delete/<product_id>", methods=["POST"])
@login_required
def delete_product(product_id):

    connection = get_db_connection()

    if not connection:
        return "Database connection failed."

    cursor = connection.cursor()

    try:

        # CHECK PURCHASE HISTORY
        cursor.execute("""
            SELECT COUNT(*)
            FROM PurchaseItem
            WHERE productID = %s
        """, (product_id,))

        purchase_count = cursor.fetchone()[0]

        # CHECK SALES HISTORY
        cursor.execute("""
            SELECT COUNT(*)
            FROM SaleItem
            WHERE productID = %s
        """, (product_id,))

        sale_count = cursor.fetchone()[0]

        # IF PRODUCT HAS HISTORY,
        # DISCONTINUE IT INSTEAD OF DELETING
        if purchase_count > 0 or sale_count > 0:

            cursor.execute("""
                UPDATE Product
                SET status = 'Discontinued'
                WHERE productID = %s
            """, (product_id,))

            connection.commit()

            return redirect(url_for("products"))

        # OTHERWISE DELETE PRODUCT
        cursor.execute("""
            DELETE FROM Product
            WHERE productID = %s
        """, (product_id,))

        connection.commit()

        return redirect(url_for("products"))

    except Exception as e:

        connection.rollback()

        print("DELETE PRODUCT ERROR:", repr(e))

        return f"""
        <h1>Could Not Delete Product</h1>

        <p>{e}</p>

        <br>

        <a href="/products">
            Back to Products
        </a>
        """

    finally:

        cursor.close()
        connection.close()


# ==========================================
# INVENTORY
# ==========================================

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
@login_required
@role_required("admin")
def add_employee():

    return render_template("add_employee.html")


# ==========================================
# VIEW EMPLOYEES
# ==========================================

@app.route("/employees")
@login_required
@role_required("admin")
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
@login_required
@role_required("admin")
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

        # ==========================================
        # CHECK INVENTORY MOVEMENTS
        # ==========================================

        cursor.execute("""
            SELECT COUNT(*)
            FROM inventorymovement
            WHERE employeeID = ?
        """, (
            employee_id,
        ))

        movement_count = cursor.fetchone()[0]


        # ==========================================
        # CHECK SALES
        # ==========================================

        cursor.execute("""
            SELECT COUNT(*)
            FROM sale
            WHERE employeeID = ?
        """, (
            employee_id,
        ))

        sale_count = cursor.fetchone()[0]


        # ==========================================
        # CHECK PURCHASES
        # ==========================================

        cursor.execute("""
            SELECT COUNT(*)
            FROM purchase
            WHERE employeeID = ?
        """, (
            employee_id,
        ))

        purchase_count = cursor.fetchone()[0]


        # ==========================================
        # IF EMPLOYEE HAS RELATED RECORDS
        # ==========================================
        #
        # We do NOT physically delete the employee.
        #
        # Instead, we deactivate the employee so that
        # historical sales, purchases and inventory
        # records remain valid.
        # ==========================================

        if (
            movement_count > 0
            or sale_count > 0
            or purchase_count > 0
        ):

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


        # ==========================================
        # NO RELATED RECORDS
        # ==========================================
        #
        # Safe to permanently delete employee.
        # ==========================================

        cursor.execute("""
            DELETE FROM employee
            WHERE employeeID = ?
        """, (
            employee_id,
        ))


        # ==========================================
        # CHECK WHETHER DELETE ACTUALLY HAPPENED
        # ==========================================

        if cursor.rowcount == 0:

            connection.rollback()

            cursor.close()
            connection.close()

            return """
            <h1>Employee Not Found</h1>

            <p>
                The employee could not be found.
            </p>

            <br>

            <a href="/employees">
                Back to Employees
            </a>
            """


        # ==========================================
        # SAVE CHANGES
        # ==========================================

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(
            url_for("employees")
        )


    # ==========================================
    # ERROR HANDLING
    # ==========================================

    except Exception as e:

        if connection:

            connection.rollback()
            connection.close()

        return f"""
        <h1>Could Not Delete Employee</h1>

        <p>
            {e}
        </p>

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
@login_required
@role_required("admin")
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
@login_required
@role_required("admin")
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
@login_required
@role_required("admin")
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
@login_required
@role_required("admin")
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

    except Exception as e:

        print("Error loading discounts:", e)

        return render_template(
            "discounts.html",
            discounts=[],
            search=search,
            error=str(e)
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
    # REQUIRED FIELD VALIDATION
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


    # -----------------------------------------------------
    # DISCOUNT TYPE VALIDATION
    # -----------------------------------------------------

    if discount_type not in [
        "Percentage",
        "Fixed"
    ]:

        return render_template(
            "add_discount.html",
            error="Invalid discount type."
        )


    # -----------------------------------------------------
    # DATE VALIDATION
    # -----------------------------------------------------

    if end_date < start_date:

        return render_template(
            "add_discount.html",
            error="End date cannot be earlier than start date."
        )


    # -----------------------------------------------------
    # NUMERIC VALIDATION
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
    # DISCOUNT TYPE LOGIC
    # -----------------------------------------------------

    if discount_type == "Percentage":

        if discount_percent < 0 or discount_percent > 100:

            return render_template(
                "add_discount.html",
                error="Percentage discount must be between 0 and 100."
            )

        # Fixed amount is not used for Percentage discounts
        fixed_amount = 0


    elif discount_type == "Fixed":

        if fixed_amount < 0:

            return render_template(
                "add_discount.html",
                error="Fixed discount cannot be negative."
            )

        # Percentage is not used for Fixed discounts
        discount_percent = 0


    # -----------------------------------------------------
    # DATABASE INSERT
    # -----------------------------------------------------

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

        print(
            "Error adding discount:",
            e
        )

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


    except Exception as e:

        print(
            "Error loading discount:",
            e
        )

        return redirect("/discounts")


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


    # -----------------------------------------------------
    # REQUIRED FIELD VALIDATION
    # -----------------------------------------------------

    if not discount_name:

        return render_template(
            "edit_discount.html",
            discount={
                "discountID": discount_id,
                "discountName": discount_name,
                "discountPercent": discount_percent,
                "startDate": start_date,
                "endDate": end_date,
                "discountType": discount_type,
                "fixedAmount": fixed_amount
            },
            error="Discount name is required."
        )


    if not start_date:

        return render_template(
            "edit_discount.html",
            discount={
                "discountID": discount_id,
                "discountName": discount_name,
                "discountPercent": discount_percent,
                "startDate": start_date,
                "endDate": end_date,
                "discountType": discount_type,
                "fixedAmount": fixed_amount
            },
            error="Start date is required."
        )


    if not end_date:

        return render_template(
            "edit_discount.html",
            discount={
                "discountID": discount_id,
                "discountName": discount_name,
                "discountPercent": discount_percent,
                "startDate": start_date,
                "endDate": end_date,
                "discountType": discount_type,
                "fixedAmount": fixed_amount
            },
            error="End date is required."
        )


    # -----------------------------------------------------
    # DISCOUNT TYPE VALIDATION
    # -----------------------------------------------------

    if discount_type not in [
        "Percentage",
        "Fixed"
    ]:

        return render_template(
            "edit_discount.html",
            error="Invalid discount type.",
            discount={
                "discountID": discount_id,
                "discountName": discount_name,
                "discountPercent": discount_percent,
                "startDate": start_date,
                "endDate": end_date,
                "discountType": discount_type,
                "fixedAmount": fixed_amount
            }
        )


    # -----------------------------------------------------
    # DATE VALIDATION
    # -----------------------------------------------------

    if end_date < start_date:

        return render_template(
            "edit_discount.html",
            error="End date cannot be earlier than start date.",
            discount={
                "discountID": discount_id,
                "discountName": discount_name,
                "discountPercent": discount_percent,
                "startDate": start_date,
                "endDate": end_date,
                "discountType": discount_type,
                "fixedAmount": fixed_amount
            }
        )


    # -----------------------------------------------------
    # NUMERIC VALIDATION
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
            "edit_discount.html",
            error="Discount values must be valid numbers.",
            discount={
                "discountID": discount_id,
                "discountName": discount_name,
                "discountPercent": discount_percent,
                "startDate": start_date,
                "endDate": end_date,
                "discountType": discount_type,
                "fixedAmount": fixed_amount
            }
        )


    # -----------------------------------------------------
    # DISCOUNT TYPE LOGIC
    # -----------------------------------------------------

    if discount_type == "Percentage":

        if discount_percent < 0 or discount_percent > 100:

            return render_template(
                "edit_discount.html",
                error="Percentage discount must be between 0 and 100.",
                discount={
                    "discountID": discount_id,
                    "discountName": discount_name,
                    "discountPercent": discount_percent,
                    "startDate": start_date,
                    "endDate": end_date,
                    "discountType": discount_type,
                    "fixedAmount": fixed_amount
                }
            )

        fixed_amount = 0


    elif discount_type == "Fixed":

        if fixed_amount < 0:

            return render_template(
                "edit_discount.html",
                error="Fixed discount cannot be negative.",
                discount={
                    "discountID": discount_id,
                    "discountName": discount_name,
                    "discountPercent": discount_percent,
                    "startDate": start_date,
                    "endDate": end_date,
                    "discountType": discount_type,
                    "fixedAmount": fixed_amount
                }
            )

        discount_percent = 0


    # -----------------------------------------------------
    # DATABASE UPDATE
    # -----------------------------------------------------

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

        return render_template(
            "edit_discount.html",
            error=str(e),
            discount={
                "discountID": discount_id,
                "discountName": discount_name,
                "discountPercent": discount_percent,
                "startDate": start_date,
                "endDate": end_date,
                "discountType": discount_type,
                "fixedAmount": fixed_amount
            }
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
# SALES MANAGEMENT
# =========================================================


# =========================================================
# VIEW ALL SALES
# =========================================================

@app.route("/sales", methods=["GET"])
def sales():

    search = request.args.get("search", "").strip()

    conn = get_db_connection()

    if conn is None:
        return "Database connection failed.", 500

    cursor = conn.cursor(dictionary=True)

    try:

        if search:

            search_value = f"%{search}%"

            cursor.execute(
                """
                SELECT
                    s.saleID,
                    s.saleDate,
                    s.customerID,
                    s.employeeID,
                    s.totalAmount,
                    s.paymentMethod,
                    s.taxAmount,
                    s.pointsRedeemed,
                    s.pointsAwarded,

                    CONCAT(c.fName, ' ', c.lName)
                        AS customerName,

                    CONCAT(e.fName, ' ', e.lName)
                        AS employeeName

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
                """
                SELECT
                    s.saleID,
                    s.saleDate,
                    s.customerID,
                    s.employeeID,
                    s.totalAmount,
                    s.paymentMethod,
                    s.taxAmount,
                    s.pointsRedeemed,
                    s.pointsAwarded,

                    CONCAT(c.fName, ' ', c.lName)
                        AS customerName,

                    CONCAT(e.fName, ' ', e.lName)
                        AS employeeName

                FROM Sale s

                LEFT JOIN Customer c
                    ON s.customerID = c.customerID

                INNER JOIN Employee e
                    ON s.employeeID = e.employeeID

                ORDER BY s.saleDate DESC
                """
            )

        sales_list = cursor.fetchall()

        return render_template(
            "sales.html",
            sales=sales_list,
            search=search
        )

    except Exception as e:

        print(
            "ERROR LOADING SALES:",
            repr(e)
        )

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

@app.route("/sales/add", methods=["GET"])
def add_sale():

    conn = get_db_connection()

    if conn is None:
        return "Database connection failed.", 500

    cursor = conn.cursor(dictionary=True)

    try:

        # -------------------------------------------------
        # EMPLOYEES
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                employeeID,
                fName,
                lName
            FROM Employee
            WHERE status = 'Active'
            ORDER BY fName, lName
            """
        )

        employees = cursor.fetchall()


        # -------------------------------------------------
        # CUSTOMERS
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                customerID,
                fName,
                lName
            FROM Customer
            ORDER BY fName, lName
            """
        )

        customers = cursor.fetchall()


        # -------------------------------------------------
        # PRODUCTS WITH AVAILABLE STOCK
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

            WHERE i.quantity > 0

            ORDER BY p.productName
            """
        )

        products = cursor.fetchall()


        return render_template(
            "add_sale.html",
            employees=employees,
            customers=customers,
            products=products,
            error=None
        )

    except Exception as e:

        print(
            "ERROR LOADING ADD SALE PAGE:",
            repr(e)
        )

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


# =========================================================
# CREATE / SAVE SALE
# =========================================================

@app.route("/sales/save", methods=["POST"])
def save_sale():

    # -----------------------------------------------------
    # GET FORM DATA
    # -----------------------------------------------------

    sale_id = request.form.get(
        "saleID",
        ""
    ).strip()

    employee_id = request.form.get(
        "employeeID",
        ""
    ).strip()

    customer_id = request.form.get(
        "customerID",
        ""
    ).strip()

    payment_method = request.form.get(
        "paymentMethod",
        ""
    ).strip()

    product_id = request.form.get(
        "productID",
        ""
    ).strip()

    quantity_text = request.form.get(
        "quantity",
        ""
    ).strip()

    discount_text = request.form.get(
        "discount",
        "0"
    ).strip()

    points_text = request.form.get(
        "pointsRedeemed",
        "0"
    ).strip()


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
    # CONVERT QUANTITY
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


    # -----------------------------------------------------
    # CONVERT DISCOUNT
    # -----------------------------------------------------

    try:

        discount = float(
            discount_text or 0
        )

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


    # -----------------------------------------------------
    # CONVERT POINTS
    # -----------------------------------------------------

    try:

        points_redeemed = int(
            points_text or 0
        )

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


    # -----------------------------------------------------
    # WALK-IN CUSTOMER
    # -----------------------------------------------------

    if customer_id == "":
        customer_id = None


    # -----------------------------------------------------
    # DATABASE CONNECTION
    # -----------------------------------------------------

    conn = get_db_connection()

    if conn is None:

        return render_template(
            "add_sale.html",
            employees=get_employees_for_sale(),
            customers=get_customers_for_sale(),
            products=get_products_for_sale(),
            error="Could not connect to MariaDB."
        )


    cursor = conn.cursor(dictionary=True)


    try:

        # -------------------------------------------------
        # 1. CHECK DUPLICATE SALE ID
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT saleID
            FROM Sale
            WHERE saleID = %s
            """,
            (sale_id,)
        )

        existing_sale = cursor.fetchone()


        if existing_sale:

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

        if customer_id is not None:

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
        # 4. GET PRODUCT + INVENTORY
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
                error=(
                    f"Product '{product_id}' "
                    f"was not found or has no inventory record."
                )
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

        gross_amount = (
            unit_price * quantity
        )

        discount_amount = (
            gross_amount * discount / 100
        )

        subtotal = (
            gross_amount - discount_amount
        )

        tax_amount = (
            subtotal * 0.03
        )

        total_amount = (
            subtotal + tax_amount
        )


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
        #
        # MariaDB triggers handle:
        #
        # BeforeSaleItemInsert
        # AfterSaleItemInsert
        # BeforeSaleItemDiscountInsert
        # AfterSaleItemInsertTotal
        #
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
        # 10. COMMIT
        # -------------------------------------------------

        conn.commit()


        print(
            f"SALE CREATED SUCCESSFULLY: {sale_id}"
        )


        # -------------------------------------------------
        # 11. SHOW SALE DETAILS
        # -------------------------------------------------

        return redirect(
            f"/sales/view/{sale_id}"
        )


    except Exception as e:

        conn.rollback()

        print(
            "ERROR CREATING SALE:",
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


# =========================================================
# SALE DETAILS
# =========================================================

@app.route(
    "/sales/view/<sale_id>",
    methods=["GET"]
)
def sale_details(sale_id):

    conn = get_db_connection()

    if conn is None:
        return "Database connection failed.", 500

    cursor = conn.cursor(dictionary=True)

    try:

        # -------------------------------------------------
        # GET SALE
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                s.saleID,
                s.saleDate,
                s.customerID,
                s.employeeID,
                s.totalAmount,
                s.paymentMethod,
                s.taxAmount,
                s.pointsRedeemed,
                s.pointsAwarded,

                CONCAT(c.fName, ' ', c.lName)
                    AS customerName,

                CONCAT(e.fName, ' ', e.lName)
                    AS employeeName

            FROM Sale s

            LEFT JOIN Customer c
                ON s.customerID = c.customerID

            INNER JOIN Employee e
                ON s.employeeID = e.employeeID

            WHERE s.saleID = %s
            """,
            (sale_id,)
        )

        sale = cursor.fetchone()


        if not sale:

            return (
                f"""
                <h2>Sale Not Found</h2>
                <p>Sale ID '{sale_id}' does not exist.</p>
                <a href="/sales">Back to Sales</a>
                """,
                404
            )


        # -------------------------------------------------
        # GET SALE ITEMS
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                si.saleID,
                si.productID,
                p.productName,
                si.quantity,
                si.unitPrice,
                si.discount,
                si.subTotal

            FROM SaleItem si

            INNER JOIN Product p
                ON si.productID = p.productID

            WHERE si.saleID = %s

            ORDER BY p.productName
            """,
            (sale_id,)
        )

        items = cursor.fetchall()


        return render_template(
            "sale_details.html",
            sale=sale,
            items=items
        )


    except Exception as e:

        print(
            "ERROR LOADING SALE DETAILS:",
            repr(e)
        )

        return str(e), 500


    finally:

        cursor.close()
        conn.close()


# =========================================================
# SALES HELPER FUNCTIONS
# =========================================================

def get_employees_for_sale():

    conn = get_db_connection()

    if conn is None:
        return []

    cursor = conn.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT
                employeeID,
                fName,
                lName
            FROM Employee
            WHERE status = 'Active'
            ORDER BY fName, lName
            """
        )

        return cursor.fetchall()

    except Exception as e:

        print(
            "ERROR GETTING EMPLOYEES FOR SALE:",
            repr(e)
        )

        return []

    finally:

        cursor.close()
        conn.close()


def get_customers_for_sale():

    conn = get_db_connection()

    if conn is None:
        return []

    cursor = conn.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT
                customerID,
                fName,
                lName
            FROM Customer
            ORDER BY fName, lName
            """
        )

        return cursor.fetchall()

    except Exception as e:

        print(
            "ERROR GETTING CUSTOMERS FOR SALE:",
            repr(e)
        )

        return []

    finally:

        cursor.close()
        conn.close()


def get_products_for_sale():

    conn = get_db_connection()

    if conn is None:
        return []

    cursor = conn.cursor(dictionary=True)

    try:

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

            WHERE i.quantity > 0

            ORDER BY p.productName
            """
        )

        return cursor.fetchall()

    except Exception as e:

        print(
            "ERROR GETTING PRODUCTS FOR SALE:",
            repr(e)
        )

        return []

    finally:

        cursor.close()
        conn.close()


# =========================================================
# EDIT SALE PAGE
# =========================================================

@app.route(
    "/sales/edit/<sale_id>",
    methods=["GET"]
)
def edit_sale(sale_id):

    conn = get_db_connection()

    if conn is None:
        return "Database connection failed.", 500

    cursor = conn.cursor(dictionary=True)

    try:

        # -------------------------------------------------
        # GET SALE
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                s.saleID,
                s.customerID,
                s.employeeID,
                s.saleDate,
                s.totalAmount,
                s.paymentMethod,
                s.taxAmount,
                s.pointsRedeemed,
                s.pointsAwarded

            FROM Sale s

            WHERE s.saleID = %s
            """,
            (sale_id,)
        )

        sale = cursor.fetchone()


        if not sale:

            return (
                f"""
                <h2>Sale Not Found</h2>
                <p>Sale ID '{sale_id}' does not exist.</p>
                <a href="/sales">Back to Sales</a>
                """,
                404
            )


        # -------------------------------------------------
        # GET SALE ITEM
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                si.saleID,
                si.productID,
                si.quantity,
                si.unitPrice,
                si.discount,
                si.subTotal,
                p.productName

            FROM SaleItem si

            INNER JOIN Product p
                ON si.productID = p.productID

            WHERE si.saleID = %s

            LIMIT 1
            """,
            (sale_id,)
        )

        item = cursor.fetchone()


        if not item:

            return (
                f"""
                <h2>No Sale Item</h2>
                <p>
                    Sale '{sale_id}' has no product recorded.
                </p>
                <a href="/sales">Back to Sales</a>
                """,
                404
            )


        # -------------------------------------------------
        # GET EMPLOYEES
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                employeeID,
                fName,
                lName

            FROM Employee

            WHERE status = 'Active'

            ORDER BY fName, lName
            """
        )

        employees = cursor.fetchall()


        # -------------------------------------------------
        # GET CUSTOMERS
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                customerID,
                fName,
                lName

            FROM Customer

            ORDER BY fName, lName
            """
        )

        customers = cursor.fetchall()


        # -------------------------------------------------
        # GET PRODUCTS
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

            ORDER BY p.productName
            """
        )

        products = cursor.fetchall()


        # -------------------------------------------------
        # ERROR MESSAGE
        # -------------------------------------------------

        error = request.args.get(
            "error",
            ""
        ).strip()


        return render_template(
            "edit_sale.html",
            sale=sale,
            item=item,
            employees=employees,
            customers=customers,
            products=products,
            error=error
        )


    except Exception as e:

        print(
            "ERROR LOADING EDIT SALE:",
            repr(e)
        )

        return str(e), 500


    finally:

        cursor.close()
        conn.close()


# =========================================================
# UPDATE SALE
# =========================================================

@app.route(
    "/sales/update/<sale_id>",
    methods=["POST"]
)
def update_sale(sale_id):

    # -----------------------------------------------------
    # GET FORM DATA
    # -----------------------------------------------------

    employee_id = request.form.get(
        "employeeID",
        ""
    ).strip()

    customer_id = request.form.get(
        "customerID",
        ""
    ).strip()

    payment_method = request.form.get(
        "paymentMethod",
        ""
    ).strip()

    product_id = request.form.get(
        "productID",
        ""
    ).strip()

    quantity_text = request.form.get(
        "quantity",
        ""
    ).strip()

    discount_text = request.form.get(
        "discount",
        "0"
    ).strip()

    points_text = request.form.get(
        "pointsRedeemed",
        "0"
    ).strip()


    # -----------------------------------------------------
    # BASIC VALIDATION
    # -----------------------------------------------------

    if not employee_id:

        return redirect(
            f"/sales/edit/{sale_id}"
            "?error=Please select an employee."
        )


    if not payment_method:

        return redirect(
            f"/sales/edit/{sale_id}"
            "?error=Please select a payment method."
        )


    if not product_id:

        return redirect(
            f"/sales/edit/{sale_id}"
            "?error=Please select a product."
        )


    # -----------------------------------------------------
    # QUANTITY
    # -----------------------------------------------------

    try:

        quantity = int(quantity_text)

        if quantity <= 0:
            raise ValueError

    except ValueError:

        return redirect(
            f"/sales/edit/{sale_id}"
            "?error=Quantity must be a positive whole number."
        )


    # -----------------------------------------------------
    # DISCOUNT
    # -----------------------------------------------------

    try:

        discount = float(
            discount_text or 0
        )

        if discount < 0 or discount > 100:
            raise ValueError

    except ValueError:

        return redirect(
            f"/sales/edit/{sale_id}"
            "?error=Discount must be between 0 and 100."
        )


    # -----------------------------------------------------
    # POINTS REDEEMED
    # -----------------------------------------------------

    try:

        points_redeemed = int(
            points_text or 0
        )

        if points_redeemed < 0:
            raise ValueError

    except ValueError:

        return redirect(
            f"/sales/edit/{sale_id}"
            "?error=Points redeemed cannot be negative."
        )


    # -----------------------------------------------------
    # WALK-IN CUSTOMER
    # -----------------------------------------------------

    if customer_id == "":
        customer_id = None


    # -----------------------------------------------------
    # DATABASE CONNECTION
    # -----------------------------------------------------

    conn = get_db_connection()

    if conn is None:
        return "Database connection failed.", 500

    cursor = conn.cursor(dictionary=True)


    try:

        # =================================================
        # 1. GET EXISTING SALE
        # =================================================

        cursor.execute(
            """
            SELECT
                saleID,
                customerID,
                employeeID,
                totalAmount,
                paymentMethod,
                pointsRedeemed,
                pointsAwarded

            FROM Sale

            WHERE saleID = %s

            FOR UPDATE
            """,
            (sale_id,)
        )

        sale = cursor.fetchone()


        if not sale:

            return (
                f"""
                <h2>Sale Not Found</h2>
                <p>Sale ID '{sale_id}' does not exist.</p>
                <a href="/sales">Back to Sales</a>
                """,
                404
            )


        # =================================================
        # 2. GET EXISTING SALE ITEM
        # =================================================

        cursor.execute(
            """
            SELECT
                saleID,
                productID,
                quantity,
                unitPrice,
                discount

            FROM SaleItem

            WHERE saleID = %s

            LIMIT 1

            FOR UPDATE
            """,
            (sale_id,)
        )

        old_item = cursor.fetchone()


        if not old_item:

            return (
                f"""
                <h2>No Sale Item</h2>
                <p>
                    Sale '{sale_id}' has no product.
                </p>
                <a href="/sales">Back to Sales</a>
                """,
                404
            )


        # =================================================
        # 3. CHECK EMPLOYEE
        # =================================================

        cursor.execute(
            """
            SELECT
                employeeID

            FROM Employee

            WHERE employeeID = %s
            """,
            (employee_id,)
        )

        employee = cursor.fetchone()


        if not employee:

            raise Exception(
                f"Employee '{employee_id}' does not exist."
            )


        # =================================================
        # 4. CHECK CUSTOMER
        # =================================================

        if customer_id is not None:

            cursor.execute(
                """
                SELECT
                    customerID

                FROM Customer

                WHERE customerID = %s
                """,
                (customer_id,)
            )

            customer = cursor.fetchone()


            if not customer:

                raise Exception(
                    f"Customer '{customer_id}' does not exist."
                )


        # =================================================
        # 5. CHECK PRODUCT
        # =================================================

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

            FOR UPDATE
            """,
            (product_id,)
        )

        new_product = cursor.fetchone()


        if not new_product:

            raise Exception(
                f"Product '{product_id}' "
                f"was not found or has no inventory record."
            )


        # =================================================
        # 6. GET UNIT PRICE
        # =================================================

        unit_price = float(
            new_product["unitPrice"]
        )


        # =================================================
        # 7. CALCULATE TOTAL
        # =================================================
        #
        # This value is placed into Sale temporarily.
        #
        # After SaleItem is updated,
        # AfterSaleItemUpdateTotal will calculate the
        # final total again from SaleItem.subTotal.
        #
        # =================================================

        gross_amount = (
            unit_price * quantity
        )

        discount_amount = (
            gross_amount * discount / 100
        )

        subtotal = (
            gross_amount - discount_amount
        )

        tax_amount = (
            subtotal * 0.03
        )

        total_amount = (
            subtotal + tax_amount
        )


        # =================================================
        # 8. UPDATE SALE HEADER
        # =================================================
        #
        # IMPORTANT:
        #
        # We DO NOT modify Inventory here.
        #
        # BeforeSaleUpdateLoyalty handles the loyalty
        # points adjustment when Sale is updated.
        #
        # =================================================

        cursor.execute(
            """
            UPDATE Sale

            SET
                customerID = %s,
                employeeID = %s,
                totalAmount = %s,
                paymentMethod = %s,
                taxAmount = %s,
                pointsRedeemed = %s

            WHERE saleID = %s
            """,
            (
                customer_id,
                employee_id,
                total_amount,
                payment_method,
                tax_amount,
                points_redeemed,
                sale_id
            )
        )


        # =================================================
        # 9. UPDATE SALE ITEM
        # =================================================
        #
        # MariaDB now handles:
        #
        # BeforeSaleItemUpdate
        #     -> stock validation
        #
        # BeforeSaleItemDiscountUpdate
        #     -> automatic percentage discount
        #
        # AfterSaleItemUpdate
        #     -> inventory adjustment
        #
        # AfterSaleItemUpdateTotal
        #     -> Sale.totalAmount
        #
        # =================================================

        cursor.execute(
            """
            UPDATE SaleItem

            SET
                productID = %s,
                quantity = %s,
                unitPrice = %s,
                discount = %s

            WHERE saleID = %s
            """,
            (
                product_id,
                quantity,
                unit_price,
                discount,
                sale_id
            )
        )


        # =================================================
        # 10. COMMIT
        # =================================================

        conn.commit()


        print(
            f"SALE UPDATED SUCCESSFULLY: {sale_id}"
        )


        # =================================================
        # 11. REDIRECT
        # =================================================

        return redirect(
            f"/sales/view/{sale_id}"
        )


    except Exception as e:

        conn.rollback()

        print(
            "ERROR UPDATING SALE:",
            repr(e)
        )

        error_message = str(e).replace(
            " ",
            "+"
        )


        return redirect(
            f"/sales/edit/{sale_id}"
            f"?error={error_message}"
        )


    finally:

        cursor.close()
        conn.close()


# =========================================================
# DELETE SALE
# =========================================================

@app.route(
    "/sales/delete/<sale_id>",
    methods=["POST"]
)
def delete_sale(sale_id):

    conn = get_db_connection()

    if conn is None:
        return "Database connection failed.", 500

    cursor = conn.cursor(dictionary=True)

    try:

        # =================================================
        # 1. CHECK SALE EXISTS
        # =================================================

        cursor.execute(
            """
            SELECT
                saleID

            FROM Sale

            WHERE saleID = %s

            FOR UPDATE
            """,
            (sale_id,)
        )

        sale = cursor.fetchone()


        if not sale:

            raise Exception(
                f"Sale '{sale_id}' does not exist."
            )


        # =================================================
        # 2. DELETE SALE ITEMS
        # =================================================
        #
        # IMPORTANT:
        #
        # We DO NOT manually restore inventory.
        #
        # AfterSaleItemDelete automatically restores the
        # inventory when the SaleItem is deleted.
        #
        # AfterSaleItemDeleteTotal also recalculates the
        # sale total.
        #
        # =================================================

        cursor.execute(
            """
            DELETE FROM SaleItem

            WHERE saleID = %s
            """,
            (sale_id,)
        )


        # =================================================
        # 3. DELETE SALE
        # =================================================
        #
        # BeforeSaleDeleteLoyalty automatically removes
        # the loyalty points awarded by this sale.
        #
        # =================================================

        cursor.execute(
            """
            DELETE FROM Sale

            WHERE saleID = %s
            """,
            (sale_id,)
        )


        if cursor.rowcount == 0:

            raise Exception(
                f"Unable to delete sale '{sale_id}'."
            )


        # =================================================
        # 4. COMMIT
        # =================================================

        conn.commit()


        print(
            f"SALE DELETED SUCCESSFULLY: {sale_id}"
        )


        return redirect("/sales")


    except Exception as e:

        conn.rollback()

        print(
            "ERROR DELETING SALE:",
            repr(e)
        )


        return (
            f"""
            <h2>Unable to Delete Sale</h2>
            <p>{str(e)}</p>
            <a href="/sales">Back to Sales</a>
            """,
            500
        )


    finally:

        cursor.close()
        conn.close()
        
# =========================================================
# PURCHASES
# =========================================================


# =========================================================
# VIEW ALL PURCHASES
# =========================================================

@app.route("/purchases")
@login_required
@role_required("admin")
def purchases():

    search = request.args.get("search", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        if search:

            search_value = f"%{search}%"

            cursor.execute("""
                SELECT
                    pu.purchaseID,
                    pu.purchaseDate,
                    pu.totalCost,
                    pu.status,

                    pu.supplierID,
                    pu.employeeID,

                    s.supplierName,

                    CONCAT(e.fName, ' ', e.lName) AS employeeName

                FROM Purchase pu

                INNER JOIN Supplier s
                    ON pu.supplierID = s.supplierID

                INNER JOIN Employee e
                    ON pu.employeeID = e.employeeID

                WHERE
                    pu.purchaseID LIKE %s
                    OR pu.supplierID LIKE %s
                    OR pu.employeeID LIKE %s
                    OR pu.status LIKE %s
                    OR s.supplierName LIKE %s
                    OR CONCAT(e.fName, ' ', e.lName) LIKE %s

                ORDER BY pu.purchaseDate DESC
            """, (
                search_value,
                search_value,
                search_value,
                search_value,
                search_value,
                search_value
            ))

        else:

            cursor.execute("""
                SELECT
                    pu.purchaseID,
                    pu.purchaseDate,
                    pu.totalCost,
                    pu.status,

                    pu.supplierID,
                    pu.employeeID,

                    s.supplierName,

                    CONCAT(e.fName, ' ', e.lName) AS employeeName

                FROM Purchase pu

                INNER JOIN Supplier s
                    ON pu.supplierID = s.supplierID

                INNER JOIN Employee e
                    ON pu.employeeID = e.employeeID

                ORDER BY pu.purchaseDate DESC
            """)

        purchases_list = cursor.fetchall()


        return render_template(
            "purchases.html",
            purchases=purchases_list,
            search=search
        )


    except Exception as e:

        print("Error loading purchases:", e)

        return render_template(
            "purchases.html",
            purchases=[],
            search=search,
            error=str(e)
        )


    finally:

        cursor.close()
        conn.close()


# =========================================================
# ADD PURCHASE PAGE
# =========================================================

@app.route("/purchases/add")
@login_required
@role_required("admin")
def add_purchase():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        # -------------------------------------------------
        # GET SUPPLIERS
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                supplierID,
                supplierName
            FROM Supplier
            ORDER BY supplierName
        """)

        suppliers = cursor.fetchall()


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
        # GET PRODUCTS
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                productID,
                productName,
                costPrice
            FROM Product
            WHERE status <> 'Discontinued'
            ORDER BY productName
        """)

        products = cursor.fetchall()


        return render_template(
            "add_purchase.html",
            suppliers=suppliers,
            employees=employees,
            products=products
        )


    except Exception as e:

        print("Error loading add purchase page:", e)

        return render_template(
            "add_purchase.html",
            suppliers=[],
            employees=[],
            products=[],
            error=str(e)
        )


    finally:

        cursor.close()
        conn.close()


# =========================================================
# SAVE PURCHASE
# =========================================================

@app.route("/purchases/save", methods=["POST"])
@login_required
@role_required("admin")
def save_purchase():

    purchase_id = request.form.get(
        "purchaseID",
        ""
    ).strip()

    supplier_id = request.form.get(
        "supplierID",
        ""
    ).strip()

    employee_id = request.form.get(
        "employeeID",
        ""
    ).strip()

    product_id = request.form.get(
        "productID",
        ""
    ).strip()

    purchase_date = request.form.get(
        "purchaseDate",
        ""
    ).strip()

    quantity_text = request.form.get(
        "quantity",
        ""
    ).strip()

    unit_cost_text = request.form.get(
        "unitCost",
        ""
    ).strip()

    status = request.form.get(
        "status",
        "Completed"
    ).strip()


    # -----------------------------------------------------
    # BASIC VALIDATION
    # -----------------------------------------------------

    if not purchase_id:

        return render_template(
            "add_purchase.html",
            suppliers=get_purchase_suppliers(),
            employees=get_purchase_employees(),
            products=get_purchase_products(),
            error="Purchase ID is required."
        )


    if not supplier_id:

        return render_template(
            "add_purchase.html",
            suppliers=get_purchase_suppliers(),
            employees=get_purchase_employees(),
            products=get_purchase_products(),
            error="Please select a supplier."
        )


    if not employee_id:

        return render_template(
            "add_purchase.html",
            suppliers=get_purchase_suppliers(),
            employees=get_purchase_employees(),
            products=get_purchase_products(),
            error="Please select an employee."
        )


    if not product_id:

        return render_template(
            "add_purchase.html",
            suppliers=get_purchase_suppliers(),
            employees=get_purchase_employees(),
            products=get_purchase_products(),
            error="Please select a product."
        )


    if not purchase_date:

        return render_template(
            "add_purchase.html",
            suppliers=get_purchase_suppliers(),
            employees=get_purchase_employees(),
            products=get_purchase_products(),
            error="Purchase date is required."
        )


    # -----------------------------------------------------
    # VALIDATE QUANTITY
    # -----------------------------------------------------

    try:

        quantity = int(quantity_text)

        if quantity <= 0:
            raise ValueError

    except ValueError:

        return render_template(
            "add_purchase.html",
            suppliers=get_purchase_suppliers(),
            employees=get_purchase_employees(),
            products=get_purchase_products(),
            error="Quantity must be a positive whole number."
        )


    # -----------------------------------------------------
    # VALIDATE UNIT COST
    # -----------------------------------------------------

    try:

        unit_cost = float(unit_cost_text)

        if unit_cost < 0:
            raise ValueError

    except ValueError:

        return render_template(
            "add_purchase.html",
            suppliers=get_purchase_suppliers(),
            employees=get_purchase_employees(),
            products=get_purchase_products(),
            error="Unit cost must be a valid positive number."
        )


    # -----------------------------------------------------
    # VALIDATE STATUS
    # -----------------------------------------------------

    allowed_statuses = [
        "Pending",
        "Completed",
        "Cancelled"
    ]

    if status not in allowed_statuses:

        return render_template(
            "add_purchase.html",
            suppliers=get_purchase_suppliers(),
            employees=get_purchase_employees(),
            products=get_purchase_products(),
            error="Invalid purchase status."
        )


    # -----------------------------------------------------
    # CALCULATE TOTAL
    # -----------------------------------------------------

    total_cost = quantity * unit_cost


    # -----------------------------------------------------
    # DATABASE
    # -----------------------------------------------------

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        # -------------------------------------------------
        # CHECK PURCHASE ID
        # -------------------------------------------------

        cursor.execute("""
            SELECT purchaseID
            FROM Purchase
            WHERE purchaseID = %s
        """, (purchase_id,))

        existing_purchase = cursor.fetchone()


        if existing_purchase:

            conn.rollback()

            return render_template(
                "add_purchase.html",
                suppliers=get_purchase_suppliers(),
                employees=get_purchase_employees(),
                products=get_purchase_products(),
                error=f"Purchase ID '{purchase_id}' already exists."
            )


        # -------------------------------------------------
        # CHECK PRODUCT
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                productID,
                productName
            FROM Product
            WHERE productID = %s
        """, (product_id,))

        product = cursor.fetchone()


        if not product:

            conn.rollback()

            return render_template(
                "add_purchase.html",
                suppliers=get_purchase_suppliers(),
                employees=get_purchase_employees(),
                products=get_purchase_products(),
                error="Selected product was not found."
            )


        # -------------------------------------------------
        # INSERT PURCHASE
        # -------------------------------------------------

        cursor.execute("""
            INSERT INTO Purchase
            (
                purchaseID,
                supplierID,
                employeeID,
                purchaseDate,
                totalCost,
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
        """, (
            purchase_id,
            supplier_id,
            employee_id,
            purchase_date,
            total_cost,
            status
        ))


        # -------------------------------------------------
        # INSERT PURCHASE ITEM
        # -------------------------------------------------

        cursor.execute("""
            INSERT INTO PurchaseItem
            (
                purchaseID,
                productID,
                quantity,
                unitCost
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s
            )
        """, (
            purchase_id,
            product_id,
            quantity,
            unit_cost
        ))


        # -------------------------------------------------
        # UPDATE INVENTORY
        # -------------------------------------------------

        cursor.execute("""
            UPDATE Inventory
            SET
                quantity = quantity + %s,
                lastUpdated = CURRENT_TIMESTAMP
            WHERE productID = %s
        """, (
            quantity,
            product_id
        ))


        # -------------------------------------------------
        # CREATE INVENTORY RECORD IF NECESSARY
        # -------------------------------------------------

        if cursor.rowcount == 0:

            cursor.execute("""
                SELECT
                    productID
                FROM Inventory
                WHERE productID = %s
            """, (product_id,))

            inventory_exists = cursor.fetchone()


            if not inventory_exists:

                cursor.execute("""
                    SELECT
                        COALESCE(
                            MAX(
                                CAST(
                                    SUBSTRING(inventoryID, 4)
                                    AS UNSIGNED
                                )
                            ),
                            0
                        ) + 1 AS nextNumber
                    FROM Inventory
                """)

                next_number = cursor.fetchone()["nextNumber"]

                inventory_id = f"INV{int(next_number):03d}"


                cursor.execute("""
                    INSERT INTO Inventory
                    (
                        inventoryID,
                        productID,
                        quantity,
                        reorderLevel,
                        lastUpdated
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        10,
                        CURRENT_TIMESTAMP
                    )
                """, (
                    inventory_id,
                    product_id,
                    quantity
                ))


        # -------------------------------------------------
        # COMMIT
        # -------------------------------------------------

        conn.commit()


        return redirect(
            url_for("purchases")
        )


    except Exception as e:

        conn.rollback()

        print("Error saving purchase:", e)

        return render_template(
            "add_purchase.html",
            suppliers=get_purchase_suppliers(),
            employees=get_purchase_employees(),
            products=get_purchase_products(),
            error=str(e)
        )


    finally:

        cursor.close()
        conn.close()


# =========================================================
# VIEW INDIVIDUAL PURCHASE
# =========================================================

@app.route("/purchases/view/<purchase_id>")
def view_purchase(purchase_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        # -------------------------------------------------
        # GET PURCHASE
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                pu.purchaseID,
                pu.purchaseDate,
                pu.totalCost,
                pu.status,

                pu.supplierID,
                pu.employeeID,

                s.supplierName,

                CONCAT(
                    e.fName,
                    ' ',
                    e.lName
                ) AS employeeName

            FROM Purchase pu

            INNER JOIN Supplier s
                ON pu.supplierID = s.supplierID

            INNER JOIN Employee e
                ON pu.employeeID = e.employeeID

            WHERE pu.purchaseID = %s
        """, (purchase_id,))

        purchase = cursor.fetchone()


        if not purchase:

            return redirect(
                url_for("purchases")
            )


        # -------------------------------------------------
        # GET PURCHASE ITEMS
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                pi.productID,
                pi.quantity,
                pi.unitCost,

                p.productName,

                (
                    pi.quantity * pi.unitCost
                ) AS itemTotal

            FROM PurchaseItem pi

            INNER JOIN Product p
                ON pi.productID = p.productID

            WHERE pi.purchaseID = %s

            ORDER BY p.productName
        """, (purchase_id,))

        items = cursor.fetchall()


        return render_template(
            "purchase_details.html",
            purchase=purchase,
            items=items
        )


    except Exception as e:

        print(
            "Error viewing purchase:",
            e
        )

        return render_template(
            "purchase_details.html",
            purchase=None,
            items=[],
            error=str(e)
        )


    finally:

        cursor.close()
        conn.close()


# =========================================================
# EDIT PURCHASE PAGE
# =========================================================

@app.route("/purchases/edit/<purchase_id>")
def edit_purchase(purchase_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        # -------------------------------------------------
        # GET PURCHASE
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                purchaseID,
                supplierID,
                employeeID,
                purchaseDate,
                totalCost,
                status

            FROM Purchase

            WHERE purchaseID = %s
        """, (purchase_id,))

        purchase = cursor.fetchone()


        if not purchase:

            return redirect(
                url_for("purchases")
            )


        # -------------------------------------------------
        # GET PURCHASE ITEM
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                productID,
                quantity,
                unitCost

            FROM PurchaseItem

            WHERE purchaseID = %s

            LIMIT 1
        """, (purchase_id,))

        item = cursor.fetchone()


        # -------------------------------------------------
        # GET SUPPLIERS
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                supplierID,
                supplierName

            FROM Supplier

            ORDER BY supplierName
        """)

        suppliers = cursor.fetchall()


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
        # GET PRODUCTS
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                productID,
                productName,
                costPrice

            FROM Product

            WHERE status <> 'Discontinued'

            ORDER BY productName
        """)

        products = cursor.fetchall()


        return render_template(
            "edit_purchase.html",
            purchase=purchase,
            item=item,
            suppliers=suppliers,
            employees=employees,
            products=products
        )


    except Exception as e:

        print(
            "Error loading edit purchase:",
            e
        )

        return render_template(
            "edit_purchase.html",
            purchase=None,
            item=None,
            suppliers=[],
            employees=[],
            products=[],
            error=str(e)
        )


    finally:

        cursor.close()
        conn.close()


# =========================================================
# UPDATE PURCHASE
# =========================================================

@app.route(
    "/purchases/update/<purchase_id>",
    methods=["POST"]
)
def update_purchase(purchase_id):

    supplier_id = request.form.get(
        "supplierID",
        ""
    ).strip()

    employee_id = request.form.get(
        "employeeID",
        ""
    ).strip()

    purchase_date = request.form.get(
        "purchaseDate",
        ""
    ).strip()

    product_id = request.form.get(
        "productID",
        ""
    ).strip()

    status = request.form.get(
        "status",
        ""
    ).strip()


    # -----------------------------------------------------
    # VALIDATE QUANTITY AND COST
    # -----------------------------------------------------

    try:

        quantity = int(
            request.form.get(
                "quantity",
                "0"
            )
        )

        unit_cost = float(
            request.form.get(
                "unitCost",
                "0"
            )
        )

    except ValueError:

        return redirect(
            url_for(
                "edit_purchase",
                purchase_id=purchase_id
            )
        )


    if quantity <= 0 or unit_cost < 0:

        return redirect(
            url_for(
                "edit_purchase",
                purchase_id=purchase_id
            )
        )


    # -----------------------------------------------------
    # VALIDATE REQUIRED FIELDS
    # -----------------------------------------------------

    if not supplier_id or not employee_id:

        return redirect(
            url_for(
                "edit_purchase",
                purchase_id=purchase_id
            )
        )


    if not product_id or not purchase_date:

        return redirect(
            url_for(
                "edit_purchase",
                purchase_id=purchase_id
            )
        )


    allowed_statuses = [
        "Pending",
        "Completed",
        "Cancelled"
    ]

    if status not in allowed_statuses:

        return redirect(
            url_for(
                "edit_purchase",
                purchase_id=purchase_id
            )
        )


    # -----------------------------------------------------
    # CALCULATE TOTAL
    # -----------------------------------------------------

    total_cost = quantity * unit_cost


    # -----------------------------------------------------
    # DATABASE
    # -----------------------------------------------------

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        # -------------------------------------------------
        # GET OLD PURCHASE ITEM
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                productID,
                quantity,
                unitCost

            FROM PurchaseItem

            WHERE purchaseID = %s

            LIMIT 1
        """, (purchase_id,))

        old_item = cursor.fetchone()


        if not old_item:

            raise Exception(
                "Purchase item was not found."
            )


        old_product_id = old_item["productID"]
        old_quantity = old_item["quantity"]


        # -------------------------------------------------
        # REVERSE OLD INVENTORY
        # -------------------------------------------------

        cursor.execute("""
            UPDATE Inventory

            SET
                quantity = quantity - %s,
                lastUpdated = CURRENT_TIMESTAMP

            WHERE productID = %s
        """, (
            old_quantity,
            old_product_id
        ))


        # -------------------------------------------------
        # UPDATE PURCHASE
        # -------------------------------------------------

        cursor.execute("""
            UPDATE Purchase

            SET
                supplierID = %s,
                employeeID = %s,
                purchaseDate = %s,
                totalCost = %s,
                status = %s

            WHERE purchaseID = %s
        """, (
            supplier_id,
            employee_id,
            purchase_date,
            total_cost,
            status,
            purchase_id
        ))


        # -------------------------------------------------
        # UPDATE PURCHASE ITEM
        # -------------------------------------------------

        cursor.execute("""
            UPDATE PurchaseItem

            SET
                productID = %s,
                quantity = %s,
                unitCost = %s

            WHERE purchaseID = %s
        """, (
            product_id,
            quantity,
            unit_cost,
            purchase_id
        ))


        # -------------------------------------------------
        # ADD NEW INVENTORY
        # -------------------------------------------------

        cursor.execute("""
            UPDATE Inventory

            SET
                quantity = quantity + %s,
                lastUpdated = CURRENT_TIMESTAMP

            WHERE productID = %s
        """, (
            quantity,
            product_id
        ))


        # -------------------------------------------------
        # CREATE INVENTORY IF NECESSARY
        # -------------------------------------------------

        if cursor.rowcount == 0:

            cursor.execute("""
                SELECT
                    productID

                FROM Inventory

                WHERE productID = %s
            """, (product_id,))

            inventory_exists = cursor.fetchone()


            if not inventory_exists:

                cursor.execute("""
                    SELECT
                        COALESCE(
                            MAX(
                                CAST(
                                    SUBSTRING(
                                        inventoryID,
                                        4
                                    ) AS UNSIGNED
                                )
                            ),
                            0
                        ) + 1 AS nextNumber

                    FROM Inventory
                """)

                next_number = cursor.fetchone()[
                    "nextNumber"
                ]

                inventory_id = (
                    f"INV{int(next_number):03d}"
                )


                cursor.execute("""
                    INSERT INTO Inventory
                    (
                        inventoryID,
                        productID,
                        quantity,
                        reorderLevel,
                        lastUpdated
                    )

                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        10,
                        CURRENT_TIMESTAMP
                    )
                """, (
                    inventory_id,
                    product_id,
                    quantity
                ))


        # -------------------------------------------------
        # COMMIT
        # -------------------------------------------------

        conn.commit()


        return redirect(
            url_for(
                "view_purchase",
                purchase_id=purchase_id
            )
        )


    except Exception as e:

        conn.rollback()

        print(
            "Error updating purchase:",
            e
        )

        return redirect(
            url_for(
                "edit_purchase",
                purchase_id=purchase_id
            )
        )


    finally:

        cursor.close()
        conn.close()


# =========================================================
# PURCHASE HELPER FUNCTIONS
# =========================================================

def get_purchase_suppliers():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT
                supplierID,
                supplierName

            FROM Supplier

            ORDER BY supplierName
        """)

        return cursor.fetchall()

    finally:

        cursor.close()
        conn.close()


def get_purchase_employees():

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


def get_purchase_products():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT
                productID,
                productName,
                costPrice

            FROM Product

            WHERE status <> 'Discontinued'

            ORDER BY productName
        """)

        return cursor.fetchall()

    finally:

        cursor.close()
        conn.close()

# =========================================================
# DELETE PURCHASE
# =========================================================

@app.route(
    "/purchases/delete/<purchase_id>",
    methods=["POST"]
)
@login_required
@role_required("admin")
def delete_purchase(purchase_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        # -------------------------------------------------
        # GET PURCHASE ITEM
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                productID,
                quantity
            FROM PurchaseItem
            WHERE purchaseID = %s
            LIMIT 1
        """, (purchase_id,))

        item = cursor.fetchone()


        # -------------------------------------------------
        # CHECK PURCHASE EXISTS
        # -------------------------------------------------

        if not item:

            return redirect(
                url_for("purchases")
            )


        product_id = item["productID"]
        quantity = item["quantity"]


        # -------------------------------------------------
        # REVERSE INVENTORY
        # -------------------------------------------------

        cursor.execute("""
            UPDATE Inventory
            SET
                quantity = quantity - %s,
                lastUpdated = CURRENT_TIMESTAMP
            WHERE productID = %s
        """, (
            quantity,
            product_id
        ))


        # -------------------------------------------------
        # DELETE PURCHASE ITEM
        # -------------------------------------------------

        cursor.execute("""
            DELETE FROM PurchaseItem
            WHERE purchaseID = %s
        """, (purchase_id,))


        # -------------------------------------------------
        # DELETE PURCHASE
        # -------------------------------------------------

        cursor.execute("""
            DELETE FROM Purchase
            WHERE purchaseID = %s
        """, (purchase_id,))


        # -------------------------------------------------
        # COMMIT
        # -------------------------------------------------

        conn.commit()


        return redirect(
            url_for("purchases")
        )


    except Exception as e:

        conn.rollback()

        print(
            "Error deleting purchase:",
            e
        )

        return redirect(
            url_for(
                "purchases",
                error=str(e)
            )
        )


    finally:

        cursor.close()
        conn.close()

# =========================================================
# REPORTS
# =========================================================

@app.route("/reports")
@login_required
@role_required("admin")
def reports():

    period = request.args.get("period", "all").strip().lower()

    conn = get_db_connection()

    if conn is None:
        return "Database connection failed.", 500

    cursor = conn.cursor(dictionary=True)

    try:

        # =================================================
        # DETERMINE REPORT PERIOD
        # =================================================

        period_labels = {
            "today": "Today",
            "week": "This Week",
            "month": "This Month",
            "all": "All Time"
        }

        period_label = period_labels.get(
            period,
            "All Time"
        )

        # -------------------------------------------------
        # DATE FILTER
        # -------------------------------------------------

        if period == "today":

            date_filter = """
                DATE(s.saleDate) = CURDATE()
            """

            purchase_date_filter = """
                DATE(pu.purchaseDate) = CURDATE()
            """

        elif period == "week":

            date_filter = """
                YEARWEEK(s.saleDate, 1)
                = YEARWEEK(CURDATE(), 1)
            """

            purchase_date_filter = """
                YEARWEEK(pu.purchaseDate, 1)
                = YEARWEEK(CURDATE(), 1)
            """

        elif period == "month":

            date_filter = """
                YEAR(s.saleDate) = YEAR(CURDATE())
                AND MONTH(s.saleDate) = MONTH(CURDATE())
            """

            purchase_date_filter = """
                YEAR(pu.purchaseDate) = YEAR(CURDATE())
                AND MONTH(pu.purchaseDate) = MONTH(CURDATE())
            """

        else:

            date_filter = "1 = 1"

            purchase_date_filter = "1 = 1"


        # =================================================
        # SALES REPORT
        # =================================================

        cursor.execute(f"""
            SELECT

                COUNT(*) AS total_transactions,

                COALESCE(
                    SUM(totalAmount),
                    0
                ) AS total_sales,

                COALESCE(
                    AVG(totalAmount),
                    0
                ) AS average_sale

            FROM Sale s

            WHERE {date_filter}
        """)

        sales_report = cursor.fetchone()


        # =================================================
        # PURCHASE REPORT
        # =================================================

        cursor.execute(f"""
            SELECT

                COUNT(*) AS total_purchases,

                COALESCE(
                    SUM(totalCost),
                    0
                ) AS total_purchase_cost

            FROM Purchase pu

            WHERE {purchase_date_filter}
        """)

        purchase_report = cursor.fetchone()


        # =================================================
        # INVENTORY REPORT
        # =================================================
        # Inventory is current, so it does not change
        # according to the selected date.

        cursor.execute("""
            SELECT

                COUNT(*) AS total_products,

                COALESCE(
                    SUM(
                        CASE
                            WHEN quantity <= 5
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS low_stock_products,

                COALESCE(
                    SUM(
                        CASE
                            WHEN quantity <= 0
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS out_of_stock_products

            FROM Inventory
        """)

        inventory_report = cursor.fetchone()


        # =================================================
        # CUSTOMER REPORT
        # =================================================

        cursor.execute("""
            SELECT
                COUNT(*) AS total_customers
            FROM Customer
        """)

        customer_report = cursor.fetchone()


        # =================================================
        # SUPPLIER REPORT
        # =================================================

        cursor.execute("""
            SELECT
                COUNT(*) AS total_suppliers
            FROM Supplier
        """)

        supplier_report = cursor.fetchone()


        # =================================================
        # CATEGORY REPORT
        # =================================================

        cursor.execute("""
            SELECT
                COUNT(*) AS total_categories
            FROM Category
        """)

        category_report = cursor.fetchone()


        # =================================================
        # PAYMENT METHOD REPORT
        # =================================================

        cursor.execute(f"""
            SELECT

                s.paymentMethod,

                COUNT(*) AS transaction_count,

                COALESCE(
                    SUM(s.totalAmount),
                    0
                ) AS total_amount

            FROM Sale s

            WHERE {date_filter}

            GROUP BY s.paymentMethod

            ORDER BY total_amount DESC
        """)

        payment_methods = cursor.fetchall()


        # =================================================
        # RECENT SALES
        # =================================================

        cursor.execute(f"""
            SELECT

                s.saleID,

                s.saleDate,

                s.totalAmount,

                s.paymentMethod,

                CONCAT(
                    c.fName,
                    ' ',
                    c.lName
                ) AS customerName

            FROM Sale s

            LEFT JOIN Customer c

                ON s.customerID =
                   c.customerID

            WHERE {date_filter}

            ORDER BY s.saleDate DESC

            LIMIT 10
        """)

        recent_sales = cursor.fetchall()


        # =================================================
        # LOW STOCK PRODUCTS
        # =================================================

        cursor.execute("""
            SELECT

                p.productID,

                p.productName,

                i.quantity

            FROM Inventory i

            INNER JOIN Product p

                ON i.productID =
                   p.productID

            WHERE i.quantity <= 5

            ORDER BY i.quantity ASC
        """)

        low_stock_products = cursor.fetchall()


        # =================================================
        # RENDER REPORT
        # =================================================

        return render_template(

            "reports.html",

            period=period,

            period_label=period_label,

            sales_report=sales_report,

            purchase_report=purchase_report,

            inventory_report=inventory_report,

            customer_report=customer_report,

            supplier_report=supplier_report,

            category_report=category_report,

            payment_methods=payment_methods,

            recent_sales=recent_sales,

            low_stock_products=low_stock_products

        )


    except Exception as e:

        print(
            "ERROR LOADING REPORTS:",
            repr(e)
        )

        return render_template(

            "reports.html",

            period=period,

            period_label=period_label,

            error=str(e)

        )


    finally:

        cursor.close()
        conn.close()
# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)