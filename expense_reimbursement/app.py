import hashlib
import re
from datetime import date, datetime
from difflib import SequenceMatcher

import pandas as pd
import streamlit as st

from database import get_connection, create_tables, log_action
from receipt_parser import parse_receipt
from receipt_ocr import parse_receipt_image, OCR_AVAILABLE

st.set_page_config(
    page_title="Expense Claims",
    page_icon="💳",
    layout="wide",
)

create_tables()

CATEGORIES = [
    "Transportation",
    "Food",
    "Hotel",
    "Travel",
    "Office Supplies",
    "Other",
]

CATEGORY_LIMITS = {
    "Transportation": 5000,
    "Food": 20000,
    "Hotel": 8000,
    "Travel": 30000,
    "Office Supplies": 10000,
    "Other": 10000,
}


def normalize_text(value):
    if not value:
        return ""
    value = value.lower()
    replacements = {
        "private limited": "",
        "pvt ltd": "",
        "pvt. ltd.": "",
        "private": "",
        "limited": "",
        "ltd": "",
        "llp": "",
        "inc": "",
        "india": "",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    value = re.sub(r"[^a-z0-9]", "", value)
    return value


def merchant_similarity(a, b):
    a = normalize_text(a)
    b = normalize_text(b)
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def receipt_fingerprint(merchant, amount, expense_date, receipt_number, tax_amount):
    raw = "|".join([
        normalize_text(merchant),
        f"{float(amount):.2f}",
        expense_date or "",
        normalize_text(receipt_number),
        f"{float(tax_amount or 0):.2f}",
    ])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def find_duplicate(conn, employee_id, merchant, amount, expense_date, receipt_number, tax_amount):
    rows = conn.execute("""
        SELECT *
        FROM claims
        WHERE employee_id = ?
          AND final_status != 'DECLINED'
    """, (employee_id,)).fetchall()

    new_merchant = normalize_text(merchant)
    new_number = normalize_text(receipt_number)

    for row in rows:
        amount_close = abs(float(row["amount"]) - float(amount)) <= 1.0
        sim = merchant_similarity(merchant, row["merchant"])

        number_match = (
            bool(new_number)
            and bool(normalize_text(row["receipt_number"]))
            and new_number == normalize_text(row["receipt_number"])
        )

        date_match = bool(expense_date and row["expense_date"] == expense_date)

        # Strong duplicate: same receipt number + same/similar merchant + amount.
        if number_match and amount_close and sim >= 0.65:
            return row, "Receipt/invoice number + amount + merchant match", sim

        # Same receipt date + amount + very similar merchant.
        if date_match and amount_close and sim >= 0.80:
            return row, "Date + amount + merchant match", sim

        # Later submission: same amount + highly similar merchant, regardless of date.
        if amount_close and sim >= 0.90:
            return row, "Amount + highly similar merchant match", sim

    return None, "", 0.0


def get_employee(employee_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM employees WHERE employee_id = ?",
        (employee_id,),
    ).fetchone()
    conn.close()
    return row


def monthly_spend(conn, employee_id, year_month):
    row = conn.execute("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM claims
        WHERE employee_id = ?
          AND substr(expense_date, 1, 7) = ?
          AND final_status IN ('APPROVED', 'PAID')
    """, (employee_id, year_month)).fetchone()
    return float(row["total"] or 0)


def check_policy(amount, category):
    if category == "Hotel" and amount > 8000:
        return False, "Hotel claim exceeds ₹8,000 policy limit."
    if category == "Food" and amount > 2000:
        return False, "Food claim exceeds ₹2,000 policy limit."
    return True, "Policy check passed."


def employee_interface():
    st.header("👤 Employee Interface")
    st.caption("Submit a receipt, review extracted information, and track payment status.")

    conn = get_connection()
    employees = conn.execute("""
        SELECT employee_id, name, role, manager_id
        FROM employees
        ORDER BY name
    """).fetchall()
    conn.close()

    options = {
        f"{r['name']} ({r['employee_id']}){' - Manager' if r['role'] == 'Manager' else ''}":
        r["employee_id"]
        for r in employees
        if r["role"] in ("Employee", "Manager")
    }

    selected = st.selectbox("Select Employee", list(options.keys()))
    employee_id = options[selected]
    employee = get_employee(employee_id)

    manager_name = "None"
    if employee["manager_id"]:
        manager = get_employee(employee["manager_id"])
        manager_name = manager["name"] if manager else "None"

    c1, c2, c3 = st.columns(3)
    c1.info(f"**Employee**\n\n{employee['name']}")
    c2.info(f"**Employee ID**\n\n{employee['employee_id']}")
    c3.info(f"**Manager**\n\n{manager_name}")

    st.divider()
    st.subheader("📄 Receipt")

    uploaded = st.file_uploader(
        "Upload receipt photo / screenshot",
        type=["png", "jpg", "jpeg"],
        key="receipt_upload",
    )

    pasted = st.text_area(
        "Or paste receipt text",
        height=140,
        placeholder="Paste whatever is written on the receipt...",
    )

    extracted = None

    if uploaded and st.button("🔍 Analyze Receipt Photo"):
        if not OCR_AVAILABLE:
            st.error(
                "OCR package is not available. Install it with "
                "`python -m pip install pytesseract pillow` and install Tesseract OCR on Windows."
            )
        else:
            try:
                from PIL import Image
                image = Image.open(uploaded)
                st.image(image, caption="Uploaded receipt", width=500)
                with st.spinner("Reading receipt..."):
                    extracted = parse_receipt_image(image)
                st.session_state["extracted_receipt"] = extracted
                st.success("Receipt analyzed.")
            except Exception as exc:
                st.error(f"OCR could not read this receipt: {exc}")

    if pasted and st.button("🔍 Analyze Pasted Receipt"):
        extracted = parse_receipt(pasted)
        st.session_state["extracted_receipt"] = extracted
        st.success("Receipt text analyzed.")

    if "extracted_receipt" not in st.session_state:
        extracted = None
    else:
        extracted = st.session_state["extracted_receipt"]

    if extracted:
        st.subheader("🔎 Review & Correct Receipt Details")
        st.caption("OCR/rules are not final. Correct anything before submitting.")

        left, right = st.columns(2)

        with left:
            merchant = st.text_input(
                "Merchant / Company",
                value=extracted.get("merchant") or "",
                key="review_merchant",
            )
            expense_date = st.text_input(
                "Date (YYYY-MM-DD)",
                value=extracted.get("expense_date") or "",
                key="review_date",
            )
            expense_time = st.text_input(
                "Time",
                value=extracted.get("expense_time") or "",
                key="review_time",
            )
            receipt_number = st.text_input(
                "Receipt / Invoice / Trip Number",
                value=extracted.get("receipt_number") or "",
                key="review_number",
            )

        with right:
            amount = st.number_input(
                "Amount (₹)",
                min_value=0.0,
                value=float(extracted.get("amount") or 0),
                step=1.0,
                key="review_amount",
            )
            current_category = extracted.get("category") or "Other"
            category = st.selectbox(
                "Category",
                CATEGORIES,
                index=CATEGORIES.index(current_category)
                if current_category in CATEGORIES else len(CATEGORIES) - 1,
                key="review_category",
            )
            tax_amount = st.number_input(
                "GST / Tax (₹)",
                min_value=0.0,
                value=float(extracted.get("tax_amount") or 0),
                step=1.0,
                key="review_tax",
            )

        st.subheader("✅ Verification")

        checks = [
            ("Merchant/company", bool(merchant)),
            ("Date", bool(expense_date)),
            ("Amount", amount > 0),
        ]

        for label, ok in checks:
            if ok:
                st.success(f"✓ {label} detected")
            else:
                st.error(f"✗ {label} missing")

        policy_ok, policy_reason = check_policy(amount, category)
        if policy_ok:
            st.success(f"✓ {policy_reason}")
        else:
            st.warning(f"⚠️ {policy_reason}")

        conn = get_connection()
        duplicate, reason, similarity = find_duplicate(
            conn,
            employee_id,
            merchant,
            amount,
            expense_date,
            receipt_number,
            tax_amount,
        )
        conn.close()

        if duplicate:
            st.error(
                f"⚠️ Possible duplicate of claim #{duplicate['id']} — "
                f"{reason} (merchant similarity {similarity:.0%})."
            )
        else:
            st.success("✓ No matching previous receipt found.")

        if st.button("🚀 Submit Claim", type="primary"):
            if not merchant or not expense_date or amount <= 0:
                st.error("Merchant, date, and amount are required.")
            elif duplicate:
                st.error("Claim blocked because a possible duplicate was found.")
            else:
                conn = get_connection()
                employee = conn.execute(
                    "SELECT * FROM employees WHERE employee_id = ?",
                    (employee_id,),
                ).fetchone()

                current_month = expense_date[:7]
                spend_before = monthly_spend(conn, employee_id, current_month)
                monthly_limit = float(employee["monthly_limit"] or 20000)
                spend_after = spend_before + amount

                ai_status = "NORMAL" if policy_ok else "SUSPICIOUS"
                human_review_status = "NOT_REQUIRED" if policy_ok else "PENDING"
                ai_reason = policy_reason
                approver_id = employee["manager_id"]

                if not policy_ok:
                    manager_status = "PENDING"
                    final_status = "SUBMITTED"
                else:
                    manager_status = "PENDING"
                    final_status = "SUBMITTED"

                fingerprint = receipt_fingerprint(
                    merchant, amount, expense_date, receipt_number, tax_amount
                )

                cur = conn.execute("""
                    INSERT INTO claims (
                        employee_id, merchant, amount, expense_date, expense_time,
                        category, description, receipt_text, receipt_file,
                        receipt_number, tax_amount, receipt_fingerprint,
                        ai_status, ai_reason, duplicate_status,
                        human_review_status, approver_id, manager_status,
                        final_status, payment_status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    employee_id,
                    merchant,
                    amount,
                    expense_date,
                    expense_time,
                    category,
                    "",
                    extracted.get("raw_text", ""),
                    uploaded.name if uploaded else None,
                    receipt_number,
                    tax_amount,
                    fingerprint,
                    ai_status,
                    ai_reason,
                    "CLEAR",
                    human_review_status,
                    approver_id,
                    manager_status,
                    final_status,
                    "NOT_PAID",
                ))

                claim_id = cur.lastrowid
                conn.commit()
                conn.close()

                log_action(
                    claim_id,
                    "CLAIM_SUBMITTED",
                    employee_id,
                    f"AI status={ai_status}; {ai_reason}",
                )

                st.success(f"Claim #{claim_id} submitted successfully.")
                st.session_state.pop("extracted_receipt", None)

    st.divider()
    st.subheader("📋 My Claims")

    conn = get_connection()
    claims = conn.execute("""
        SELECT *
        FROM claims
        WHERE employee_id = ?
        ORDER BY created_at DESC
    """, (employee_id,)).fetchall()
    conn.close()

    if claims:
        for claim in claims:
            with st.expander(
                f"Claim #{claim['id']} — {claim['merchant']} — ₹{claim['amount']:.2f}"
            ):
                st.write(f"**Date:** {claim['expense_date']}")
                st.write(f"**Category:** {claim['category']}")
                st.write(f"**AI:** {claim['ai_status']} — {claim['ai_reason']}")
                st.write(f"**Finance review:** {claim['human_review_status']}")
                st.write(f"**Manager:** {claim['manager_status']}")
                st.write(f"**Payment:** {claim['payment_status']}")
                st.write(f"**Final status:** {claim['final_status']}")
    else:
        st.info("No claims yet.")


def manager_interface():
    st.header("👨‍💼 Manager Interface")
    st.caption("Manage your team and approve team expense claims.")

    manager_options = {
        r["name"]: r["employee_id"]
        for r in get_manager_rows()
    }
    selected_manager = st.selectbox("Manager", list(manager_options.keys()))
    manager_id = manager_options[selected_manager]

    st.info(f"Acting as **{selected_manager}**")

    st.subheader("➕ Add New Employee")

    with st.form("add_employee_form"):
        new_id = st.text_input("Employee ID", placeholder="EMP003")
        new_name = st.text_input("Employee Name", placeholder="Amit Sharma")
        new_role = st.selectbox("Role", ["Employee", "Manager"])

        conn = get_connection()
        managers = conn.execute("""
            SELECT employee_id, name
            FROM employees
            WHERE role IN ('Manager', 'Finance Manager')
            ORDER BY name
        """).fetchall()
        conn.close()

        manager_choices = {
            f"{r['name']} ({r['employee_id']})": r["employee_id"]
            for r in managers
        }
        manager_labels = list(manager_choices.keys())
        default = next(
            (i for i, label in enumerate(manager_labels)
             if manager_choices[label] == manager_id),
            0,
        )

        reporting = st.selectbox(
            "Reporting Manager",
            manager_labels,
            index=default,
        )

        submitted = st.form_submit_button("➕ Add Employee")

        if submitted:
            new_id = new_id.strip().upper()
            new_name = new_name.strip()

            if not new_id or not new_name:
                st.error("Employee ID and name are required.")
            else:
                conn = get_connection()
                exists = conn.execute(
                    "SELECT 1 FROM employees WHERE employee_id = ?",
                    (new_id,),
                ).fetchone()

                if exists:
                    st.error("That Employee ID already exists.")
                else:
                    conn.execute("""
                        INSERT INTO employees
                        (employee_id, name, role, manager_id, monthly_limit)
                        VALUES (?, ?, ?, ?, ?)
                    """, (new_id, new_name, new_role,
                          manager_choices[reporting], 20000))
                    conn.commit()
                    st.success(f"{new_name} added successfully.")
                    conn.close()
                    st.rerun()
                conn.close()

    st.subheader("👥 My Team")
    conn = get_connection()
    team = conn.execute("""
        SELECT employee_id, name, role, monthly_limit
        FROM employees
        WHERE manager_id = ?
        ORDER BY name
    """, (manager_id,)).fetchall()
    conn.close()

    if team:
        st.dataframe(
            pd.DataFrame([dict(x) for x in team]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No team members yet.")

    st.subheader("📋 Approval Queue")

    conn = get_connection()
    queue = conn.execute("""
        SELECT c.*, e.name AS employee_name
        FROM claims c
        JOIN employees e ON e.employee_id = c.employee_id
        WHERE c.approver_id = ?
          AND c.manager_status = 'PENDING'
          AND c.final_status != 'PAID'
        ORDER BY c.created_at DESC
    """, (manager_id,)).fetchall()
    conn.close()

    if not queue:
        st.info("No claims waiting for your approval.")
    else:
        for claim in queue:
            with st.expander(
                f"Claim #{claim['id']} — {claim['employee_name']} — "
                f"{claim['merchant']} — ₹{claim['amount']:.2f}"
            ):
                st.write(f"Date: {claim['expense_date']}")
                st.write(f"Category: {claim['category']}")
                st.write(f"AI status: {claim['ai_status']}")
                st.write(f"Finance review: {claim['human_review_status']}")

                if claim["employee_id"] == manager_id:
                    st.error("You cannot approve your own claim.")
                    continue

                if claim["human_review_status"] == "PENDING":
                    st.warning("Finance review is still required before approval.")
                    continue

                a, b = st.columns(2)
                with a:
                    if st.button("✅ Approve", key=f"approve_{claim['id']}"):
                        conn = get_connection()
                        conn.execute("""
                            UPDATE claims
                            SET manager_status='APPROVED',
                                final_status='APPROVED'
                            WHERE id=?
                              AND manager_status='PENDING'
                              AND final_status != 'PAID'
                        """, (claim["id"],))
                        conn.commit()
                        conn.close()
                        log_action(claim["id"], "MANAGER_APPROVED", manager_id)
                        st.rerun()

                with b:
                    reason = st.text_input(
                        "Decline reason",
                        key=f"reason_{claim['id']}",
                    )
                    if st.button("❌ Decline", key=f"decline_{claim['id']}"):
                        if not reason.strip():
                            st.error("Enter a reason.")
                        else:
                            conn = get_connection()
                            conn.execute("""
                                UPDATE claims
                                SET manager_status='DECLINED',
                                    final_status='DECLINED',
                                    decline_reason=?
                                WHERE id=?
                                  AND manager_status='PENDING'
                                  AND final_status != 'PAID'
                            """, (reason.strip(), claim["id"]))
                            conn.commit()
                            conn.close()
                            log_action(
                                claim["id"],
                                "MANAGER_DECLINED",
                                manager_id,
                                reason.strip(),
                            )
                            st.rerun()


def get_manager_rows():
    conn = get_connection()
    rows = conn.execute("""
        SELECT employee_id, name
        FROM employees
        WHERE role IN ('Manager', 'Finance Manager')
        ORDER BY name
    """).fetchall()
    conn.close()
    return rows


def finance_interface():
    st.header("💰 Finance Interface")
    st.caption("Review suspicious claims, pay approved claims, and monitor monthly spend.")

    current_month = date.today().strftime("%Y-%m")

    conn = get_connection()

    awaiting = conn.execute("""
        SELECT COUNT(*) AS n
        FROM claims
        WHERE manager_status='APPROVED'
          AND payment_status='NOT_PAID'
    """).fetchone()["n"]

    paid = conn.execute("""
        SELECT COUNT(*) AS n
        FROM claims
        WHERE payment_status='PAID'
    """).fetchone()["n"]

    reviews = conn.execute("""
        SELECT COUNT(*) AS n
        FROM claims
        WHERE human_review_status='PENDING'
    """).fetchone()["n"]

    spend = conn.execute("""
        SELECT COALESCE(SUM(amount),0) AS total
        FROM claims
        WHERE substr(expense_date,1,7)=?
          AND final_status IN ('APPROVED','PAID')
    """, (current_month,)).fetchone()["total"]

    conn.close()

    a, b, c, d = st.columns(4)
    a.metric("Awaiting Payment", awaiting)
    b.metric("Paid Claims", paid)
    c.metric("Human Reviews", reviews)
    d.metric("Monthly Spend", f"₹{float(spend):,.0f}")

    st.subheader("🔎 Human Review Queue")

    conn = get_connection()
    review_queue = conn.execute("""
        SELECT c.*, e.name AS employee_name
        FROM claims c
        JOIN employees e ON e.employee_id=c.employee_id
        WHERE c.human_review_status='PENDING'
        ORDER BY c.created_at DESC
    """).fetchall()
    conn.close()

    if review_queue:
        for claim in review_queue:
            with st.expander(
                f"Claim #{claim['id']} — {claim['employee_name']} — "
                f"{claim['merchant']} — ₹{claim['amount']:.2f}"
            ):
                st.write(f"Reason: {claim['ai_reason']}")
                st.write(f"Date: {claim['expense_date']}")
                st.write(f"Category: {claim['category']}")

                v, r = st.columns(2)
                with v:
                    if st.button("✅ Verify", key=f"verify_{claim['id']}"):
                        conn = get_connection()
                        conn.execute("""
                            UPDATE claims
                            SET human_review_status='VERIFIED',
                                ai_status='VERIFIED'
                            WHERE id=? AND final_status != 'PAID'
                        """, (claim["id"],))
                        conn.commit()
                        conn.close()
                        log_action(claim["id"], "FINANCE_VERIFIED", "FINANCE")
                        st.rerun()

                with r:
                    if st.button("❌ Reject", key=f"reject_{claim['id']}"):
                        conn = get_connection()
                        conn.execute("""
                            UPDATE claims
                            SET human_review_status='REJECTED',
                                manager_status='DECLINED',
                                final_status='DECLINED',
                                decline_reason='Rejected by Finance review'
                            WHERE id=? AND final_status != 'PAID'
                        """, (claim["id"],))
                        conn.commit()
                        conn.close()
                        log_action(claim["id"], "FINANCE_REJECTED", "FINANCE")
                        st.rerun()
    else:
        st.success("No suspicious claims waiting for review.")

    st.subheader("💳 Payment Queue")

    conn = get_connection()
    payments = conn.execute("""
        SELECT c.*, e.name AS employee_name
        FROM claims c
        JOIN employees e ON e.employee_id=c.employee_id
        WHERE c.manager_status='APPROVED'
          AND c.payment_status='NOT_PAID'
          AND c.final_status != 'PAID'
        ORDER BY c.created_at DESC
    """).fetchall()
    conn.close()

    if payments:
        for claim in payments:
            with st.expander(
                f"Claim #{claim['id']} — {claim['employee_name']} — "
                f"{claim['merchant']} — ₹{claim['amount']:.2f}"
            ):
                if claim["human_review_status"] == "PENDING":
                    st.warning("Cannot pay until Finance review is completed.")
                    continue

                if st.button(
                    "💳 Pay / Mark as Paid",
                    key=f"pay_{claim['id']}",
                    type="primary",
                ):
                    conn = get_connection()
                    conn.execute("""
                        UPDATE claims
                        SET payment_status='PAID',
                            final_status='PAID'
                        WHERE id=?
                          AND manager_status='APPROVED'
                          AND payment_status='NOT_PAID'
                          AND final_status != 'PAID'
                    """, (claim["id"],))
                    conn.commit()
                    conn.close()
                    log_action(claim["id"], "PAID", "FINANCE")
                    st.success(f"Claim #{claim['id']} marked as paid.")
                    st.rerun()
    else:
        st.info("No approved claims waiting for payment.")

    st.subheader("📊 Monthly Spend & Limits")

    conn = get_connection()
    rows = conn.execute("""
        SELECT
            e.employee_id,
            e.name,
            e.monthly_limit,
            COALESCE(SUM(
                CASE
                    WHEN substr(c.expense_date,1,7)=?
                     AND c.final_status IN ('APPROVED','PAID')
                    THEN c.amount
                    ELSE 0
                END
            ),0) AS monthly_spend
        FROM employees e
        LEFT JOIN claims c ON c.employee_id=e.employee_id
        WHERE e.role IN ('Employee','Manager')
        GROUP BY e.employee_id, e.name, e.monthly_limit
        ORDER BY monthly_spend DESC
    """, (current_month,)).fetchall()

    category_rows = conn.execute("""
        SELECT category, SUM(amount) AS spend
        FROM claims
        WHERE substr(expense_date,1,7)=?
          AND final_status IN ('APPROVED','PAID')
        GROUP BY category
        ORDER BY spend DESC
    """, (current_month,)).fetchall()

    conn.close()

    data = []
    for row in rows:
        spend_value = float(row["monthly_spend"] or 0)
        limit_value = float(row["monthly_limit"] or 0)
        data.append({
            "Employee": row["name"],
            "Employee ID": row["employee_id"],
            "Monthly Spend": spend_value,
            "Limit": limit_value,
            "Remaining": max(limit_value - spend_value, 0),
            "Status": "OVER LIMIT" if spend_value > limit_value else (
                "NEAR LIMIT" if limit_value and spend_value >= limit_value * 0.8
                else "WITHIN LIMIT"
            ),
        })

    if data:
        df = pd.DataFrame(data)
        st.dataframe(
            df.style.format({
                "Monthly Spend": "₹{:,.0f}",
                "Limit": "₹{:,.0f}",
                "Remaining": "₹{:,.0f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

        over = df[df["Status"] == "OVER LIMIT"]
        if len(over):
            st.error(
                "⚠️ Employees over their monthly limit: "
                + ", ".join(over["Employee"].tolist())
            )
        else:
            st.success("No employees are currently over their monthly limit.")

    if category_rows:
        st.bar_chart(
            pd.DataFrame(
                [{"Category": r["category"], "Spend": r["spend"]} for r in category_rows]
            ).set_index("Category")
        )


interface = st.sidebar.radio(
    "Select Interface",
    ["👤 Employee", "👨‍💼 Manager", "💰 Finance"],
)

if interface == "👤 Employee":
    employee_interface()
elif interface == "👨‍💼 Manager":
    manager_interface()
else:
    finance_interface()
