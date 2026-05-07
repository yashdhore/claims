import os
from dotenv import load_dotenv
from azure.cosmos import CosmosClient

# --------------------------------------------------
# Load environment variables from .env
# --------------------------------------------------
load_dotenv()

COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DATABASE = os.getenv("COSMOS_DATABASE", "claimsdb")

# --------------------------------------------------
# Print configuration information
# --------------------------------------------------
print(f"COSMOS_ENDPOINT: {COSMOS_ENDPOINT}")

if COSMOS_KEY:
    print(f"COSMOS_KEY: {COSMOS_KEY[:10]}...")
else:
    print("COSMOS_KEY: Not found")

print(f"COSMOS_DATABASE: {COSMOS_DATABASE}")

# --------------------------------------------------
# Connect to Cosmos DB
# --------------------------------------------------
print("Connecting to Cosmos DB...")

client = CosmosClient(
    COSMOS_ENDPOINT,
    credential=COSMOS_KEY
)

database = client.get_database_client(COSMOS_DATABASE)

# --------------------------------------------------
# Get claims container
# --------------------------------------------------
claims_container = database.get_container_client("claims")

# --------------------------------------------------
# Query all claims
# --------------------------------------------------
query = "SELECT * FROM c"

claims = list(
    claims_container.query_items(
        query=query,
        enable_cross_partition_query=True
    )
)

# --------------------------------------------------
# Print summary
# --------------------------------------------------
print(f"\nFound {len(claims)} claims in the database.\n")

if not claims:
    print("No claims found in the database.")

else:

    # --------------------------------------------------
    # Print each claim
    # --------------------------------------------------
    for idx, claim in enumerate(claims, start=1):

        print("-" * 50)

        print(f"{idx}. ID: {claim.get('id', 'N/A')}")
        print(f"   Claim ID: {claim.get('claim_id', 'N/A')}")
        print(f"   Status: {claim.get('claim_status', 'N/A')}")
        print(f"   Policy ID: {claim.get('policy_id', 'N/A')}")
        print(f"   Customer ID: {claim.get('customer_id', 'N/A')}")
        print(f"   Country: {claim.get('country', 'N/A')}")
        print(f"   State: {claim.get('state', 'N/A')}")
        print(f"   Claim Date: {claim.get('claim_date', 'N/A')}")
        print(f"   Claim Type: {claim.get('claim_type', 'N/A')}")
        print(f"   Loss Cause: {claim.get('loss_cause', 'N/A')}")
        print(f"   Estimated Loss: {claim.get('estimated_loss', 'N/A')}")
        print(f"   Deductible: {claim.get('deductible', 'N/A')}")
        print(f"   Coverage Limit: {claim.get('coverage_limit', 'N/A')}")
        print(f"   Coverage Valid: {claim.get('coverage_valid', 'N/A')}")
        print(f"   Severity Score: {claim.get('severity_score', 'N/A')}")
        print(f"   Fraud Risk Score: {claim.get('fraud_risk_score', 'N/A')}")
        print(f"   Adjuster ID: {claim.get('adjuster_id', 'N/A')}")

print("\nCosmos DB test completed successfully.")