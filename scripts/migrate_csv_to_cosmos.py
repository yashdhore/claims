"""
migrate_csv_to_cosmos.py

Migrates all CSV data files into Azure Cosmos DB containers.
Reads from the data/ folder and upserts into the corresponding containers.
"""

import os
import csv
import uuid
from dotenv import load_dotenv
from azure.cosmos import CosmosClient

load_dotenv()

COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DATABASE = os.getenv("COSMOS_DATABASE", "claimsdb")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# Map CSV file -> container name
CSV_CONTAINERS = {
    "claims.csv":       "claims",
    "policies.csv":     "policies",
    "adjusters.csv":    "adjusters",
    "payments.csv":     "payments",
    "tasks.csv":        "tasks",
    "documents.csv":    "documents",
    "claim_notes.csv":  "claim_notes",
    "agent_events.csv": "agent_events",
}

print(f"COSMOS_ENDPOINT: {COSMOS_ENDPOINT}")
print(f"COSMOS_KEY: {COSMOS_KEY[:10]}..." if COSMOS_KEY else "COSMOS_KEY: Not found")
print(f"COSMOS_DATABASE: {COSMOS_DATABASE}")
print("Connecting to Cosmos DB...")

client = CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)
database = client.get_database_client(COSMOS_DATABASE)


def migrate_csv(csv_file: str, container_name: str):
    filepath = os.path.join(DATA_DIR, csv_file)
    if not os.path.exists(filepath):
        print(f"  SKIPPED — file not found: {filepath}")
        return 0

    container = database.get_container_client(container_name)
    count = 0

    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Ensure every document has an 'id' field (required by Cosmos DB)
            if "id" not in row or not row["id"]:
                row["id"] = str(uuid.uuid4())

            # Convert numeric strings to numbers where possible
            for key, value in row.items():
                try:
                    if "." in str(value):
                        row[key] = float(value)
                    else:
                        row[key] = int(value)
                except (ValueError, TypeError):
                    pass

            container.upsert_item(row)
            count += 1

    return count


print("\nStarting migration...\n")
total = 0

for csv_file, container_name in CSV_CONTAINERS.items():
    print(f"Migrating {csv_file} -> {container_name}...")
    count = migrate_csv(csv_file, container_name)
    print(f"  {count} records loaded.")
    total += count

print(f"\nMigration complete. Total records loaded: {total}")
