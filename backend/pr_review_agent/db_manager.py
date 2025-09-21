# backend/pr_review_agent/db_manager.py

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self._driver = None
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER")
        self.password = os.getenv("NEO4J_PASSWORD")

    def connect(self):
        if not self._driver and self.uri and self.user and self.password:
            try:
                self._driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
                print("Successfully connected to Neo4j AuraDB.")
            except Exception as e:
                print(f"Failed to connect to Neo4j: {e}")
                self._driver = None

    def get_driver(self):
        if not self._driver:
            self.connect()
        return self._driver

    def close(self):
        if self._driver is not None:
            self._driver.close()
            self._driver = None
            print("Neo4j connection closed.")

# Create a single, global instance of the DatabaseManager
db_manager = DatabaseManager()
