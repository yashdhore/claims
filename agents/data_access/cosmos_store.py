"""
Cosmos Store Module for Insurance Claims Processing System

This module provides a clean interface to interact with Azure Cosmos DB
for managing insurance claims data. It uses the azure.cosmos library to
connect to the database and perform CRUD operations on various containers.

Environment Variables Required:
- COSMOS_ENDPOINT: The endpoint URL for the Cosmos DB account
- COSMOS_KEY: The primary key for authentication
- COSMOS_DATABASE: The database name (should be 'claimsdb')

Containers in the database:
- claims: Stores claim documents (partition key: /claim_id)
- agent_events: Stores agent event logs (partition key: /claim_id)
- policies: Stores policy information (partition key: /policy_id)
- adjusters: Stores adjuster information (partition key: /adjuster_id)
- payments: Stores payment records (partition key: /claim_id)
- tasks: Stores task information (partition key: /claim_id)
- documents: Stores document metadata (partition key: /claim_id)
- claim_notes: Stores claim notes (partition key: /claim_id)
"""

import os
from azure.cosmos import CosmosClient, exceptions
from typing import Dict, List, Any, Optional


class CosmosStore:
    """
    A class to handle interactions with Azure Cosmos DB for the claims system.
    """

    def __init__(self):
        """
        Initialize the Cosmos DB client using environment variables.
        """
        self.endpoint = os.getenv('COSMOS_ENDPOINT')
        self.key = os.getenv('COSMOS_KEY')
        self.database_name = os.getenv('COSMOS_DATABASE', 'claimsdb')

        if not all([self.endpoint, self.key]):
            raise ValueError("COSMOS_ENDPOINT and COSMOS_KEY environment variables must be set")

        self.client = CosmosClient(self.endpoint, self.key)
        self.database = self.client.get_database_client(self.database_name)

    def get_container(self, container_name: str):
        """
        Get a container client for the specified container.

        Args:
            container_name (str): Name of the container

        Returns:
            ContainerProxy: The container client
        """
        return self.database.get_container_client(container_name)

    def get_claim(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific claim by its ID.

        Args:
            claim_id (str): The unique identifier of the claim

        Returns:
            dict or None: The claim document if found, None otherwise
        """
        try:
            container = self.get_container('claims')
            query = "SELECT * FROM c WHERE c.id = @claim_id"
            parameters = [{"name": "@claim_id", "value": claim_id}]
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            return items[0] if items else None
        except exceptions.CosmosHttpResponseError:
            return None

    def get_all_claims(self) -> List[Dict[str, Any]]:
        """
        Retrieve all claims from the database.

        Returns:
            list: List of all claim documents
        """
        container = self.get_container('claims')
        query = "SELECT * FROM c"
        return list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))

    def insert_claim(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert a new claim or update an existing one.

        Args:
            claim_data (dict): The claim data to insert/update

        Returns:
            dict: The inserted/updated claim document
        """
        container = self.get_container('claims')
        return container.upsert_item(claim_data)

    def update_claim(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing claim. This is an alias for insert_claim since
        Cosmos DB upsert handles both insert and update operations.

        Args:
            claim_data (dict): The claim data to update

        Returns:
            dict: The updated claim document
        """
        return self.insert_claim(claim_data)

    def insert_agent_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert a new agent event.

        Args:
            event_data (dict): The event data to insert

        Returns:
            dict: The inserted event document
        """
        container = self.get_container('agent_events')
        return container.upsert_item(event_data)

    def get_agent_events(self, claim_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all agent events for a specific claim.

        Args:
            claim_id (str): The claim ID to filter events

        Returns:
            list: List of agent event documents for the claim
        """
        container = self.get_container('agent_events')
        query = "SELECT * FROM c WHERE c.claim_id = @claim_id"
        parameters = [{"name": "@claim_id", "value": claim_id}]
        return list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))


# Global instance for easy access
cosmos_store = CosmosStore()