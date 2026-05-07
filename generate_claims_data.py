# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 08:45:02 2026

@author: ydhor
"""

# generate_claims_data.py

import os
import random
from datetime import datetime, timedelta
import pandas as pd

random.seed(42)

OUTPUT_DIR = "./data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

NUM_POLICIES = 120
NUM_CLAIMS = 100
NUM_ADJUSTERS = 12

first_names = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Jamie", "Avery", "Cameron", "Quinn"]
last_names = ["Smith", "Johnson", "Brown", "Garcia", "Miller", "Davis", "Wilson", "Moore", "Taylor", "Anderson"]

country_state_map = {
    "USA": ["TX", "CA", "FL", "NY", "IL", "GA", "AZ", "NC"],
    "Australia": ["NSW", "VIC", "QLD", "WA", "SA", "TAS"],
    "UK": ["England", "Scotland", "Wales", "Northern Ireland"]
}

vehicle_makes = ["Toyota", "Honda", "Ford", "Chevrolet", "Nissan", "Hyundai", "Kia", "Subaru", "Tesla"]
claim_types = ["Collision", "Comprehensive", "Bodily Injury", "Property Damage"]
loss_causes = ["Rear-end accident", "Hail damage", "Theft", "Vandalism", "Side collision", "Parking lot damage"]
statuses = ["New", "Under Review", "Approved", "Denied", "Paid", "Closed"]


def random_date(days_back=365):
    return datetime.today() - timedelta(days=random.randint(1, days_back))


def get_country_and_state():
    country = random.choice(list(country_state_map.keys()))
    state = random.choice(country_state_map[country])
    return country, state


# -----------------------
# Adjusters
# -----------------------
adjusters = []

for i in range(1, NUM_ADJUSTERS + 1):
    country, state = get_country_and_state()

    adjusters.append({
        "adjuster_id": f"ADJ{i:03d}",
        "adjuster_name": f"{random.choice(first_names)} {random.choice(last_names)}",
        "country": country,
        "state": state,
        "specialty": random.choice(claim_types),
        "max_open_claims": random.choice([10, 15, 20, 25])
    })

adjusters_df = pd.DataFrame(adjusters)


# -----------------------
# Policies
# -----------------------
policies = []

for i in range(1, NUM_POLICIES + 1):
    country, state = get_country_and_state()

    start_date = random_date(900)
    end_date = start_date + timedelta(days=365)

    policies.append({
        "policy_id": f"POL{i:05d}",
        "customer_id": f"CUST{i:05d}",
        "customer_name": f"{random.choice(first_names)} {random.choice(last_names)}",
        "country": country,
        "state": state,
        "policy_status": random.choices(
            ["Active", "Expired", "Cancelled"],
            weights=[0.82, 0.12, 0.06]
        )[0],
        "policy_start_date": start_date.date(),
        "policy_end_date": end_date.date(),
        "coverage_type": random.choice(["Liability Only", "Standard", "Full Coverage"]),
        "deductible": random.choice([250, 500, 1000, 1500]),
        "coverage_limit": random.choice([25000, 50000, 100000, 250000]),
        "vehicle_year": random.randint(2012, 2025),
        "vehicle_make": random.choice(vehicle_makes),
        "vehicle_model": random.choice(["Sedan", "SUV", "Truck", "Coupe", "Van"])
    })

policies_df = pd.DataFrame(policies)


# -----------------------
# Claims
# -----------------------
claims = []

for i in range(1, NUM_CLAIMS + 1):
    policy = policies_df.sample(1).iloc[0]
    claim_date = random_date(180)

    claim_type = random.choice(claim_types)
    status = random.choices(
        statuses,
        weights=[0.15, 0.25, 0.15, 0.10, 0.20, 0.15]
    )[0]

    estimated_loss = round(random.uniform(750, 30000), 2)

    coverage_valid = (
        policy["policy_status"] == "Active"
        and datetime.strptime(str(policy["policy_start_date"]), "%Y-%m-%d").date() <= claim_date.date()
        and datetime.strptime(str(policy["policy_end_date"]), "%Y-%m-%d").date() >= claim_date.date()
    )

    severity_score = min(
        100,
        int((estimated_loss / 30000) * 100) + random.randint(0, 15)
    )

    fraud_risk_score = random.randint(1, 100)

    if estimated_loss > 20000:
        fraud_risk_score += random.randint(5, 15)

    if not coverage_valid:
        fraud_risk_score += random.randint(5, 20)

    fraud_risk_score = min(100, fraud_risk_score)

    same_region_adjusters = adjusters_df[
        (adjusters_df["country"] == policy["country"]) &
        (adjusters_df["state"] == policy["state"])
    ]

    if len(same_region_adjusters) > 0:
        assigned_adjuster = same_region_adjusters.sample(1).iloc[0]
    else:
        same_country_adjusters = adjusters_df[
            adjusters_df["country"] == policy["country"]
        ]

        if len(same_country_adjusters) > 0:
            assigned_adjuster = same_country_adjusters.sample(1).iloc[0]
        else:
            assigned_adjuster = adjusters_df.sample(1).iloc[0]

    claims.append({
        "claim_id": f"CLM{i:05d}",
        "policy_id": policy["policy_id"],
        "customer_id": policy["customer_id"],
        "country": policy["country"],
        "state": policy["state"],
        "claim_date": claim_date.date(),
        "claim_type": claim_type,
        "loss_cause": random.choice(loss_causes),
        "claim_status": status,
        "estimated_loss": estimated_loss,
        "deductible": policy["deductible"],
        "coverage_limit": policy["coverage_limit"],
        "coverage_valid": coverage_valid,
        "severity_score": severity_score,
        "fraud_risk_score": fraud_risk_score,
        "adjuster_id": assigned_adjuster["adjuster_id"]
    })

claims_df = pd.DataFrame(claims)


# -----------------------
# Payments
# -----------------------
payments = []

for _, claim in claims_df.iterrows():
    if claim["claim_status"] in ["Approved", "Paid", "Closed"] and claim["coverage_valid"]:
        payment_amount = max(
            0,
            min(claim["estimated_loss"], claim["coverage_limit"]) - claim["deductible"]
        )

        claim_date = datetime.strptime(str(claim["claim_date"]), "%Y-%m-%d")

        payments.append({
            "payment_id": f"PAY{len(payments) + 1:05d}",
            "claim_id": claim["claim_id"],
            "country": claim["country"],
            "state": claim["state"],
            "payment_date": (claim_date + timedelta(days=random.randint(5, 45))).date(),
            "payment_amount": round(payment_amount, 2),
            "payment_status": random.choice(["Issued", "Pending", "Cleared"]),
            "payment_method": random.choice(["ACH", "Check", "Virtual Card"])
        })

payments_df = pd.DataFrame(payments)


# -----------------------
# Claim Notes
# -----------------------
notes = []

note_templates = [
    "Claim opened and initial review started.",
    "Customer contacted for additional information.",
    "Photos and damage details reviewed.",
    "Coverage verification completed.",
    "Adjuster requested supporting documents.",
    "Claim moved to next review stage.",
    "Potential fraud indicator reviewed.",
    "Payment recommendation prepared."
]

for _, claim in claims_df.iterrows():
    claim_date = datetime.strptime(str(claim["claim_date"]), "%Y-%m-%d")

    for _ in range(random.randint(1, 4)):
        notes.append({
            "note_id": f"NOTE{len(notes) + 1:05d}",
            "claim_id": claim["claim_id"],
            "adjuster_id": claim["adjuster_id"],
            "note_date": (claim_date + timedelta(days=random.randint(1, 30))).date(),
            "note_text": random.choice(note_templates)
        })

notes_df = pd.DataFrame(notes)


# -----------------------
# Documents
# -----------------------
documents = []

doc_types = [
    "Police Report",
    "Damage Photos",
    "Repair Estimate",
    "Medical Bill",
    "Customer Statement"
]

for _, claim in claims_df.iterrows():
    claim_date = datetime.strptime(str(claim["claim_date"]), "%Y-%m-%d")

    for _ in range(random.randint(1, 3)):
        documents.append({
            "document_id": f"DOC{len(documents) + 1:05d}",
            "claim_id": claim["claim_id"],
            "document_type": random.choice(doc_types),
            "uploaded_date": (claim_date + timedelta(days=random.randint(0, 20))).date(),
            "file_name": f"{claim['claim_id']}_{random.randint(1000,9999)}.pdf"
        })

documents_df = pd.DataFrame(documents)


# -----------------------
# Tasks
# -----------------------
tasks = []

task_types = [
    "Verify coverage",
    "Contact customer",
    "Review documents",
    "Estimate damages",
    "Approve payment",
    "Fraud review"
]

for _, claim in claims_df.iterrows():
    claim_date = datetime.strptime(str(claim["claim_date"]), "%Y-%m-%d")

    for _ in range(random.randint(1, 3)):
        tasks.append({
            "task_id": f"TASK{len(tasks) + 1:05d}",
            "claim_id": claim["claim_id"],
            "assigned_to": claim["adjuster_id"],
            "task_type": random.choice(task_types),
            "task_status": random.choice(["Open", "In Progress", "Completed"]),
            "due_date": (claim_date + timedelta(days=random.randint(3, 30))).date()
        })

tasks_df = pd.DataFrame(tasks)


# -----------------------
# Save CSVs
# -----------------------
adjusters_df.to_csv(f"{OUTPUT_DIR}/adjusters.csv", index=False)
policies_df.to_csv(f"{OUTPUT_DIR}/policies.csv", index=False)
claims_df.to_csv(f"{OUTPUT_DIR}/claims.csv", index=False)
payments_df.to_csv(f"{OUTPUT_DIR}/payments.csv", index=False)
notes_df.to_csv(f"{OUTPUT_DIR}/claim_notes.csv", index=False)
documents_df.to_csv(f"{OUTPUT_DIR}/documents.csv", index=False)
tasks_df.to_csv(f"{OUTPUT_DIR}/tasks.csv", index=False)

print("Synthetic multinational claims data created successfully.")
print(f"Files saved in: {OUTPUT_DIR}/")
print(f"Policies: {len(policies_df)}")
print(f"Claims: {len(claims_df)}")
print(f"Adjusters: {len(adjusters_df)}")
print(f"Payments: {len(payments_df)}")
print(f"Notes: {len(notes_df)}")
print(f"Documents: {len(documents_df)}")
print(f"Tasks: {len(tasks_df)}")