# 💳 AI-Assisted Expense Claims & Reimbursement Portal

A prototype expense reimbursement platform that helps employees submit expense claims from receipts, automatically extracts receipt information, detects potential duplicates and policy violations, routes claims through manager and Finance review, and tracks payment status.

This project was built as a hackathon prototype based on the Expense Claims build task.

---

## 📌 Problem

Employees spend their own money on:

- Travel
- Meals
- Office supplies
- Taxis / transportation
- Hotels
- Other business expenses

They then need to submit receipts, get manager approval, and wait for Finance to reimburse them.

The goal of this prototype is to make the process faster and reduce manual data entry and duplicate payments.

The original task describes three primary users:

1. Staff member
2. Manager
3. Finance

Managers are also employees and therefore need to be able to submit their own expense claims. However, a manager must never be able to approve their own claim.

---

# 🎯 Project Goals

The prototype focuses on the following goals:

- Reduce manual receipt data entry
- Extract information from receipt photos
- Allow employees to review and correct extracted information
- Detect duplicate receipts
- Identify policy violations
- Route suspicious claims for Finance review
- Route normal claims to the appropriate manager
- Prevent managers from approving their own claims
- Allow Finance to mark approved claims as paid
- Prevent paid claims from going backwards
- Provide monthly spending visibility
- Identify employees who exceed their monthly spending limit

---

# 👥 User Roles

## 1. Employee

Employees can:

- Select their employee profile
- Upload a receipt photo
- Paste receipt text
- Analyze a receipt
- Review extracted information
- Correct incorrect OCR results
- Select an expense category
- Submit an expense claim
- Track claim status
- See whether a claim is paid

Managers are also represented as employees and can submit their own claims.

---

## 2. Manager

Managers can:

- View their team
- Add new employees
- Assign employees to a reporting manager
- View claims assigned to them
- Approve claims
- Decline claims with a reason

A manager cannot approve their own expense claim.

If a manager submits a claim, it is routed to their own manager.

For example:

```text
Rahul  → Arjun
Priya  → Arjun
Arjun  → Neha

