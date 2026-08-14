# =========================================================
# AUTHENTICATION MODULE
# Supermarket Management System
# =========================================================

from functools import wraps

from flask import (
    session,
    redirect,
    url_for,
    flash
)

from werkzeug.security import check_password_hash

from services.database import get_db_connection


# =========================================================
# AUTHENTICATE USER
# =========================================================

def authenticate_user(login_value, password):

    conn = get_db_connection()

    if conn is None:
        return None

    cursor = conn.cursor(dictionary=True)

    try:

        # -------------------------------------------------
        # FIND EMPLOYEE BY ID OR EMAIL
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                employeeID,
                fName,
                lName,
                position,
                email,
                passwordHash,
                status

            FROM Employee

            WHERE
                employeeID = %s
                OR email = %s

            LIMIT 1
            """,
            (
                login_value,
                login_value
            )
        )

        user = cursor.fetchone()

        # -------------------------------------------------
        # USER NOT FOUND
        # -------------------------------------------------

        if not user:

            print("AUTH ERROR: Employee not found.")

            return None

        # -------------------------------------------------
        # CHECK ACCOUNT STATUS
        # -------------------------------------------------

        if user["status"] != "Active":

            print("AUTH ERROR: Employee account is inactive.")

            return None

        # -------------------------------------------------
        # CHECK PASSWORD
        # -------------------------------------------------

        password_hash = user["passwordHash"]

        if not password_hash:

            print("AUTH ERROR: No password hash found.")

            return None

        if not check_password_hash(
            password_hash,
            password
        ):

            print("AUTH ERROR: Incorrect password.")

            return None

        # -------------------------------------------------
        # DETERMINE ROLE
        # -------------------------------------------------

        role = get_user_role(
            user["position"]
        )

        # -------------------------------------------------
        # RETURN USER INFORMATION
        # -------------------------------------------------

        return {

            "employeeID":
                user["employeeID"],

            "fName":
                user["fName"],

            "lName":
                user["lName"],

            "position":
                user["position"],

            "email":
                user["email"],

            "role":
                role
        }

    except Exception as e:

        print(
            "AUTHENTICATION ERROR:",
            repr(e)
        )

        return None

    finally:

        cursor.close()
        conn.close()


# =========================================================
# ROLE DETECTION
# =========================================================

def get_user_role(position):

    if not position:

        return "staff"

    position = (
        position
        .strip()
        .lower()
    )

    # -----------------------------------------------------
    # ADMINISTRATOR
    # -----------------------------------------------------

    if position in [
        "admin",
        "administrator",
        "system administrator"
    ]:

        return "admin"

    # -----------------------------------------------------
    # MANAGER
    # -----------------------------------------------------

    if position in [
        "manager",
        "general manager",
        "supervisor"
    ]:

        return "manager"

    # -----------------------------------------------------
    # SALES
    # -----------------------------------------------------

    if position in [
        "cashier",
        "sales",
        "sales officer",
        "salesperson"
    ]:

        return "sales"

    # -----------------------------------------------------
    # INVENTORY
    # -----------------------------------------------------

    if position in [
        "inventory",
        "inventory officer",
        "storekeeper",
        "warehouse officer"
    ]:

        return "inventory"

    # -----------------------------------------------------
    # DEFAULT
    # -----------------------------------------------------

    return "staff"


# =========================================================
# LOGIN REQUIRED
# =========================================================

def login_required(function):

    @wraps(function)
    def decorated_function(
        *args,
        **kwargs
    ):

        if "employee_id" not in session:

            flash(
                "Please login to access the system.",
                "warning"
            )

            return redirect(
                url_for("login")
            )

        return function(
            *args,
            **kwargs
        )

    return decorated_function


# =========================================================
# ROLE REQUIRED
# =========================================================

def role_required(*allowed_roles):

    def decorator(function):

        @wraps(function)
        def decorated_function(
            *args,
            **kwargs
        ):

            # -------------------------------------------------
            # CHECK LOGIN
            # -------------------------------------------------

            if "employee_id" not in session:

                flash(
                    "Please login to access the system.",
                    "warning"
                )

                return redirect(
                    url_for("login")
                )

            # -------------------------------------------------
            # GET USER ROLE
            # -------------------------------------------------

            user_role = session.get(
                "role"
            )

            # -------------------------------------------------
            # CHECK ROLE
            # -------------------------------------------------

            if user_role not in allowed_roles:

                flash(
                    "You do not have permission to access this page.",
                    "danger"
                )

                return redirect(
                    url_for("dashboard")
                )

            # -------------------------------------------------
            # ACCESS GRANTED
            # -------------------------------------------------

            return function(
                *args,
                **kwargs
            )

        return decorated_function

    return decorator