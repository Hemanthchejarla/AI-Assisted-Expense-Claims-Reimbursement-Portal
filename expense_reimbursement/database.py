import sqlite3

DB_NAME = "expense.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            employee_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            manager_id TEXT,
            monthly_limit REAL DEFAULT 20000
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            merchant TEXT NOT NULL,
            amount REAL NOT NULL,
            expense_date TEXT NOT NULL,
            expense_time TEXT,
            category TEXT NOT NULL,
            description TEXT,
            receipt_text TEXT,
            receipt_file TEXT,
            receipt_number TEXT,
            tax_amount REAL,
            receipt_fingerprint TEXT,
            ai_status TEXT DEFAULT 'PENDING',
            ai_reason TEXT,
            duplicate_status TEXT DEFAULT 'CLEAR',
            human_review_status TEXT DEFAULT 'NOT_REQUIRED',
            approver_id TEXT,
            manager_status TEXT DEFAULT 'PENDING',
            final_status TEXT DEFAULT 'SUBMITTED',
            decline_reason TEXT,
            payment_status TEXT DEFAULT 'NOT_PAID',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            claim_id INTEGER,
            action TEXT,
            performed_by TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Add columns safely if an older prototype database already exists.
    existing = {
        row["name"]
        for row in cursor.execute("PRAGMA table_info(employees)").fetchall()
    }
    if "monthly_limit" not in existing:
        cursor.execute(
            "ALTER TABLE employees ADD COLUMN monthly_limit REAL DEFAULT 20000"
        )

    claim_columns = {
        row["name"]
        for row in cursor.execute("PRAGMA table_info(claims)").fetchall()
    }
    additions = {
        "expense_time": "TEXT",
        "receipt_number": "TEXT",
        "tax_amount": "REAL",
        "receipt_fingerprint": "TEXT",
    }
    for column, definition in additions.items():
        if column not in claim_columns:
            cursor.execute(
                f"ALTER TABLE claims ADD COLUMN {column} {definition}"
            )

    employees = [
        ("EMP001", "Rahul", "Employee", "MGR001", 20000),
        ("EMP002", "Priya", "Employee", "MGR001", 20000),
        ("MGR001", "Arjun", "Manager", "MGR002", 25000),
        ("MGR002", "Neha", "Finance Manager", None, 30000),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO employees
        (employee_id, name, role, manager_id, monthly_limit)
        VALUES (?, ?, ?, ?, ?)
    """, employees)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS prevent_paid_claim_changes
        BEFORE UPDATE ON claims
        WHEN OLD.final_status = 'PAID'
             AND NEW.final_status != 'PAID'
        BEGIN
            SELECT RAISE(ABORT, 'Paid claims cannot be changed.');
        END;
    """)

    conn.commit()
    conn.close()


def log_action(claim_id, action, performed_by, details=""):
    conn = get_connection()
    conn.execute("""
        INSERT INTO audit_log
        (claim_id, action, performed_by, details)
        VALUES (?, ?, ?, ?)
    """, (claim_id, action, performed_by, details))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_tables()
    print("Database created successfully!")
