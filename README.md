# AI-Assisted-Expense-Claims-Reimbursement-Portal
Absolutely. Here is a **full, submission-ready `README.md`** for your Expense Claims hackathon project. It covers the items the task specifically asks for: how to run it, decisions/assumptions, AI tools and where they are used, and what you would do with another week. 

You can copy everything below into your `README.md`.

````markdown
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
````

Therefore:

```text
Rahul's claim → Arjun
Priya's claim → Arjun
Arjun's claim → Neha
```

---

## 3. Finance

Finance can:

* View suspicious claims
* Review claims flagged by the system
* Verify suspicious claims
* Reject suspicious claims
* View approved claims waiting for payment
* Mark claims as paid
* Monitor monthly spending
* View spending by employee
* View spending by category
* Identify employees over their monthly limit
* Identify employees approaching their monthly limit

No real payment gateway is used.

The Finance "Pay / Mark as Paid" action only changes the claim status in the database.

---

# 🔄 Claim Workflow

The main workflow is:

```text
Employee
   │
   ▼
Upload Receipt / Paste Receipt
   │
   ▼
OCR / Receipt Parsing
   │
   ▼
Extract Receipt Information
   │
   ├── Merchant
   ├── Date
   ├── Time
   ├── Amount
   ├── Receipt Number
   ├── GST / Tax
   └── Category
   │
   ▼
Employee Reviews & Corrects
   │
   ▼
Duplicate Check
   │
   ▼
Policy Check
   │
   ├───────────────┐
   │               │
Normal          Suspicious
   │               │
   ▼               ▼
Manager          Finance
Approval         Review
   │               │
   │          ┌────┴────┐
   │          │         │
   │       Verify     Reject
   │          │
   └──────────┘
         │
         ▼
   Manager Approval
         │
         ▼
      Finance
         │
         ▼
   Mark as Paid
         │
         ▼
       PAID
```

Once a claim becomes `PAID`, it is considered final.

---

# 📷 Receipt Processing

Employees can upload:

* JPG
* JPEG
* PNG

The system uses OCR to read the receipt.

The extracted information is displayed back to the employee before submission.

Example:

```text
Merchant:
Uber India

Date:
2026-09-05

Time:
18:42

Amount:
₹450

Receipt Number:
ABC123

GST:
₹22.50

Category:
Transportation
```

The employee can correct any extracted field before submitting.

This is important because OCR is not guaranteed to be perfect.

---

# 🔍 Receipt Verification

The prototype performs several checks.

## Merchant

Attempts to identify the merchant/company name.

Example:

```text
UBER INDIA PVT LTD
```

---

## Date

Attempts to extract the receipt date.

Supported examples include:

```text
05/09/2026
05-09-2026
2026-09-05
05 Sep 2026
```

---

## Time

Attempts to identify receipt time where available.

Example:

```text
18:42
06:42 PM
```

Time is optional because many receipts do not contain a visible time.

---

## Amount

Attempts to identify the total amount.

Examples:

```text
₹450
Rs. 450
INR 450
Total: ₹450
Amount Due: ₹450
```

---

## Receipt / Invoice Number

The system attempts to identify:

* Receipt number
* Invoice number
* Bill number
* Transaction ID
* Trip ID
* Order ID

---

## GST / Tax

The system attempts to identify:

* GST
* CGST
* SGST
* Tax

---

# 🧠 AI / Automation Approach

This prototype intentionally uses a lightweight approach rather than requiring a large AI infrastructure.

The receipt-processing pipeline is:

```text
Receipt Image
      ↓
OCR
      ↓
Text Extraction
      ↓
Rule-Based Field Extraction
      ↓
Validation
      ↓
Duplicate Detection
      ↓
Policy Checks
```

## OCR

The prototype uses:

**Tesseract OCR**

The Python application uses `pytesseract` to communicate with the Tesseract OCR engine.

OCR is responsible for converting the receipt image into text.

---

## Receipt Parsing

The extracted text is processed using Python rules and regular expressions.

The parser looks for patterns such as:

```text
₹450
Rs 450
Total: ₹450
05/09/2026
05 Sep 2026
18:42
GST: ₹22
```

---

## Category Detection

The prototype uses keyword-based classification.

Examples:

```text
Uber / Ola / Taxi / Cab
        ↓
Transportation
```

```text
Restaurant / Food / Cafe / Dinner
        ↓
Food
```

```text
Hotel / Room / Stay
        ↓
Hotel
```

```text
Flight / Airlines / Travel
        ↓
Travel
```

```text
Office / Stationery / Supplies
        ↓
Office Supplies
```

If no known keyword is found:

```text
Other
```

---

# 🔁 Duplicate Receipt Detection

Duplicate claims are an important business requirement.

The system does not rely only on the exact receipt date.

For example, the following can represent the same receipt:

```text
UBER INDIA PVT LTD
₹450
05/09/2026
```

and:

```text
Uber India
Rs 450
05-Sep-2026
```

The system normalizes merchant names and compares multiple receipt attributes.

It considers:

* Employee
* Amount
* Merchant similarity
* Receipt/invoice number
* Date
* Receipt information

A receipt submitted weeks later can still be flagged if the important information is sufficiently similar.

---

# 🛡️ Policy Checks

The prototype contains example expense policy limits.

Current examples include:

```text
Hotel > ₹8,000
        ↓
Suspicious
```

```text
Food > ₹2,000
        ↓
Suspicious
```

Suspicious claims are sent to Finance for human review.

These limits are prototype assumptions and can be configured differently for a real company.

---

# 👨‍💼 Manager Approval

Normal claims are routed to the employee's manager.

The employee record contains:

```text
employee_id
name
role
manager_id
```

This allows the system to determine the correct approver.

A manager cannot approve their own claim.

Example:

```text
Arjun
Manager ID = MGR001
Manager's manager = MGR002
```

If Arjun submits an expense:

```text
Arjun
   ↓
Neha
```

The system therefore does not allow Arjun to approve that claim.

---

# 💰 Finance Payment

Finance is responsible for payment.

The prototype does not integrate with a real payment gateway.

Instead:

```text
Approved
   ↓
Finance
   ↓
Pay / Mark as Paid
   ↓
PAID
```

The database records:

```text
payment_status = PAID
final_status = PAID
```

A SQLite trigger prevents a paid claim from moving back to another final status.

---

# 📊 Monthly Spend Monitoring

Finance has a monthly spending dashboard.

It shows:

* Employee
* Employee ID
* Monthly spend
* Monthly limit
* Remaining amount
* Status

Example:

```text
Employee     Spend       Limit       Status
------------------------------------------------
Rahul        ₹18,500     ₹20,000     NEAR LIMIT
Priya        ₹12,000     ₹20,000     WITHIN LIMIT
Arjun        ₹27,000     ₹25,000     OVER LIMIT
```

The dashboard explicitly identifies employees who are:

```text
OVER LIMIT
NEAR LIMIT
WITHIN LIMIT
```

Finance can also view spending grouped by category.

---

# 🗄️ Database

The prototype uses:

**SQLite**

The database contains three main tables.

## employees

Stores employee information.

Important fields:

```text
employee_id
name
role
manager_id
monthly_limit
```

---

## claims

Stores expense claims.

Important fields include:

```text
id
employee_id
merchant
amount
expense_date
expense_time
category
receipt_text
receipt_file
receipt_number
tax_amount
receipt_fingerprint
ai_status
ai_reason
duplicate_status
human_review_status
approver_id
manager_status
final_status
payment_status
```

---

## audit_log

Stores important actions such as:

```text
CLAIM_SUBMITTED
MANAGER_APPROVED
MANAGER_DECLINED
FINANCE_VERIFIED
FINANCE_REJECTED
PAID
```

This provides a basic history of important workflow events.

---

# 🛠️ Technology Stack

## Frontend

**Streamlit**

Used to create the web interface for:

* Employee
* Manager
* Finance

---

## Backend

**Python**

Used for:

* Business logic
* Receipt processing
* Validation
* Duplicate detection
* Workflow processing

---

## Database

**SQLite**

Used for:

* Employees
* Claims
* Audit logs

---

## Data Processing

**Pandas**

Used for:

* Monthly reporting
* Spend tables
* Finance dashboard

---

## OCR

**Tesseract OCR**

Used to extract text from receipt images.

Python communicates with Tesseract through:

```text
pytesseract
```

---

# 📁 Project Structure

```text
expense_reimbursement/
│
├── app.py
│
├── database.py
│
├── receipt_parser.py
│
├── receipt_ocr.py
│
├── requirements.txt
│
├── README.md
│
└── expense.db
```

### app.py

Main Streamlit application.

Contains:

* Employee interface
* Manager interface
* Finance interface
* Workflow logic

---

### database.py

Creates and manages the SQLite database.

Contains:

* Database connection
* Table creation
* Employee seed data
* Audit logging
* Paid-claim protection

---

### receipt_parser.py

Processes pasted receipt text.

---

### receipt_ocr.py

Processes receipt images through OCR and extracts fields.

---

### requirements.txt

Contains the Python dependencies.

---

### expense.db

SQLite database created when the application is initialized.

It is generated locally and does not need to be committed to GitHub if the project is configured to create it automatically.

---

# 🚀 How to Run

## 1. Install Python

Recommended:

```text
Python 3.11+
```

---

## 2. Clone the repository

```bash
git clone <YOUR-GITHUB-REPOSITORY-URL>
```

Then:

```bash
cd expense_reimbursement
```

---

## 3. Install Python dependencies

```bash
python -m pip install -r requirements.txt
```

---

## 4. Install Tesseract OCR

Tesseract OCR needs to be installed separately from the Python package.

On Windows, install the Tesseract OCR engine and make sure the executable is available at the expected installation location.

Typical path:

```text
C:\Program Files\Tesseract-OCR\tesseract.exe
```

The application uses:

```python
pytesseract
```

to access it.

---

## 5. Create the database

Run:

```bash
python database.py
```

Expected output:

```text
Database created successfully!
```

---

## 6. Start Streamlit

Run:

```bash
python -m streamlit run app.py
```

The application will normally open at:

```text
http://localhost:8501
```

---

# 🧪 Demo Users

The prototype contains example users.

| Employee | ID     | Role            | Manager |
| -------- | ------ | --------------- | ------- |
| Rahul    | EMP001 | Employee        | Arjun   |
| Priya    | EMP002 | Employee        | Arjun   |
| Arjun    | MGR001 | Manager         | Neha    |
| Neha     | MGR002 | Finance Manager | None    |

These are demo users only.

There is no real authentication in this prototype.

---

# 🧪 Suggested Demo Scenarios

## Scenario 1 — Normal Employee Claim

1. Open Employee interface.
2. Select Rahul.
3. Upload a taxi receipt.
4. Analyze the receipt.
5. Review merchant, date, amount and category.
6. Correct any OCR errors.
7. Submit the claim.
8. Switch to Manager.
9. Select Arjun.
10. Approve Rahul's claim.
11. Switch to Finance.
12. Mark the claim as paid.
13. Return to Employee.
14. Show the claim as paid.

---

## Scenario 2 — Manager Submits Own Claim

1. Open Employee interface.
2. Select Arjun.
3. Upload an expense receipt.
4. Submit the claim.
5. Switch to Manager.
6. Select Arjun.
7. The system must not allow Arjun to approve his own claim.
8. The claim should be routed to Neha.

This demonstrates the self-approval protection.

---

## Scenario 3 — Suspicious Claim

1. Upload a hotel receipt above the prototype hotel limit.
2. Submit the claim.
3. The system flags it as suspicious.
4. Finance sees it in the Human Review Queue.
5. Finance verifies or rejects it.
6. If verified, it continues to manager approval.

---

## Scenario 4 — Duplicate Receipt

Submit a receipt such as:

```text
UBER INDIA PVT LTD
Total ₹450
05/09/2026
Trip ID ABC123
```

Then submit another version:

```text
Uber India
Rs 450
05-Sep-2026
Trip ABC123
```

The second submission should be flagged as a potential duplicate.

---

## Scenario 5 — Monthly Limit

Create several approved/paid claims for an employee until their monthly spending exceeds the configured limit.

Finance should then see:

```text
OVER LIMIT
```

The dashboard also identifies employees who are close to their limit.

---

# ⚙️ Decisions and Assumptions

The original task leaves some implementation decisions open, so the following assumptions were made.

## Authentication

Real authentication is not implemented.

The prototype uses employee/manager selection to simulate different users.

A production system would use:

* Company SSO
* Role-based access control
* Secure sessions
* Server-side authorization

---

## Payment

No real payment integration is used.

The task explicitly allows payment to be emulated.

Therefore Finance's payment action changes the claim status rather than transferring money.

---

## Expense Limits

The task requires Finance to identify people who exceed their limit but does not specify exact limits.

The prototype therefore uses demo limits.

These values should be treated as configurable assumptions rather than company policy.

---

## Receipt Authenticity

OCR does not prove that a receipt is genuine.

The system verifies the information it can extract and compares it with existing claims.

A production system could add stronger verification such as:

* Merchant verification
* Tax validation
* Invoice verification
* External accounting integrations
* Fraud detection models

---

## Duplicate Detection

No single field is treated as sufficient to prove a duplicate.

The prototype compares multiple attributes and uses merchant similarity.

This is intended to catch cases where the same receipt is typed differently.

A production system would use a more sophisticated receipt fingerprint and potentially an ML/embedding-based similarity model.

---

## Human Review

Automation is used to assist Finance rather than completely replace human review.

Suspicious claims are intentionally routed to Finance.

This reduces the risk of automatically rejecting legitimate expenses because of OCR or rule errors.

---

# 🤖 AI Tools Used

## Tesseract OCR

Used for:

```text
Receipt image
      ↓
Text
```

This allows the application to read receipt photos.

---

## Python Parsing Rules

Regular expressions and text normalization are used to extract:

* Amount
* Date
* Time
* Merchant
* Receipt number
* GST/tax
* Category

---

## Similarity Matching

Python's text similarity functionality is used to compare merchant names.

For example:

```text
UBER INDIA PVT LTD
```

and:

```text
Uber India
```

can be treated as similar.

---

## AI Development Assistance

AI-assisted development was used during the creation of the prototype to help with:

* Application architecture
* Python implementation
* SQLite schema design
* Streamlit UI
* Receipt extraction logic
* Duplicate detection logic
* Debugging
* Documentation

The final application logic remains explicit in the repository rather than depending on an opaque AI decision.

---

# 🔐 Security Considerations

This is a hackathon prototype and is not production-ready.

The following are intentionally simplified:

* Authentication
* Authorization
* Data encryption
* File storage security
* Database security
* Secrets management
* Payment security

A production system would require appropriate enterprise security controls.

---

# 📈 What I Would Build Next With Another Week

If I had another week, I would focus on the following improvements.

## 1. Better OCR

Improve image processing before OCR:

* Crop receipt
* Deskew image
* Improve contrast
* Remove background noise
* Rotate automatically
* Handle low-quality photos

---

## 2. PDF Support

Allow users to upload:

```text
JPG
PNG
PDF
```

and process PDF receipts.

---

## 3. Better Duplicate Detection

Build a stronger receipt fingerprint using:

* Merchant
* Amount
* Date
* Time
* Receipt number
* Tax
* Line items
* Raw receipt text

I would also test fuzzy matching against a larger set of realistic duplicate examples.

---

## 4. Confidence Scores

Instead of simply saying:

```text
Merchant detected
```

the system could show:

```text
Merchant       96%
Amount         99%
Date           94%
Receipt No.    88%
```

Low-confidence fields could be highlighted for employee correction.

---

## 5. Better AI Classification

Replace keyword-based category detection with an AI classification model that understands receipt context.

For example:

```text
"Business lunch with client"
```

could automatically be classified as:

```text
Food
```

while:

```text
"Airport transfer"
```

could be:

```text
Transportation
```

---

## 6. Configurable Company Policies

Instead of hard-coded limits, Finance would be able to configure:

```text
Food       ₹2,000/day
Hotel      ₹8,000/night
Taxi       ₹5,000/month
Travel     ₹30,000/month
```

The policy engine could also support:

* Employee grade
* Department
* Location
* Currency
* Date ranges

---

## 7. Authentication

Add company login and role-based permissions.

For example:

```text
Employee → Own claims
Manager  → Team claims
Finance  → Finance operations
Admin    → Configuration
```

---

## 8. Better Audit Trail

The audit log could capture:

* Who changed a field
* Previous value
* New value
* Timestamp
* Reason
* IP/session information

This would make the system more suitable for financial auditing.

---

## 9. Production Database

Replace SQLite with a production database such as PostgreSQL.

---

## 10. Deployment

Deploy the application so reviewers can open it directly without installing Python.

The target architecture would be:

```text
Browser
   ↓
Deployed Streamlit / Web App
   ↓
Application Backend
   ↓
PostgreSQL
   ↓
Receipt Storage
```

---

# 📊 Current Prototype Status

| Feature                    | Status                 |
| -------------------------- | ---------------------- |
| Employee interface         | ✅                      |
| Manager interface          | ✅                      |
| Finance interface          | ✅                      |
| Receipt text input         | ✅                      |
| Receipt photo input        | ✅                      |
| OCR                        | ✅                      |
| Merchant extraction        | ✅                      |
| Date extraction            | ✅                      |
| Time extraction            | ✅                      |
| Amount extraction          | ✅                      |
| Receipt number extraction  | ✅                      |
| GST/tax extraction         | ✅                      |
| Employee correction        | ✅                      |
| Duplicate detection        | ✅                      |
| Policy checking            | ✅                      |
| Suspicious claim review    | ✅                      |
| Manager approval           | ✅                      |
| Self-approval protection   | ✅                      |
| Add employee               | ✅                      |
| Finance payment simulation | ✅                      |
| Paid status finality       | ✅                      |
| Monthly spend reporting    | ✅                      |
| Over-limit identification  | ✅                      |
| Audit log                  | ✅                      |
| Real authentication        | ❌ Prototype limitation |
| Real payment gateway       | ❌ Not required         |
| Production deployment      | 🔄 Future improvement  |

---

# 📝 Conclusion

This prototype demonstrates an end-to-end expense reimbursement workflow:

```text
Receipt
   ↓
OCR
   ↓
Extraction
   ↓
Employee Correction
   ↓
Duplicate & Policy Checks
   ↓
Finance Review if Suspicious
   ↓
Manager Approval
   ↓
Finance Payment
   ↓
PAID
```

The main goal is to reduce manual entry while keeping humans involved where financial risk or ambiguity exists.

The prototype is intentionally lightweight and focuses on demonstrating the core business workflow rather than production infrastructure.

````

### A small recommendation before GitHub

Replace this:

```text
<YOUR-GITHUB-REPOSITORY-URL>
````

with your actual GitHub repository URL once you create it.

