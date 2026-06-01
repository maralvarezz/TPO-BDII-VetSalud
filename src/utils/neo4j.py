from __future__ import annotations

import os

from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j._sync.driver import Driver


def get_neo4j_driver() -> Driver:
    load_dotenv()

    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password123")

    return GraphDatabase.driver(uri, auth=(user, password))
