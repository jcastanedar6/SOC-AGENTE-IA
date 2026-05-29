from __future__ import annotations

import os
import logging

os.environ["CHROMA_TELEMETRY_ENABLED"] = "false"

# Suppress chromadb telemetry noise on Python 3.14
logging.getLogger("chromadb.telemetry").setLevel(logging.ERROR)
logging.getLogger("chromadb.segment").setLevel(logging.WARNING)

import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings
import uuid

logger = logging.getLogger(__name__)

_client = None
_collection = None


def _get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def get_collection(name: str = "soc_incidents"):
    client = _get_client()
    return client.get_or_create_collection(name=name)


def add_document(text: str, metadata: dict, collection_name: str = "soc_incidents") -> str:
    col = get_collection(collection_name)
    doc_id = str(uuid.uuid4())
    col.add(documents=[text], metadatas=[metadata], ids=[doc_id])
    return doc_id


def query(text: str, n_results: int | None = None, collection_name: str = "soc_incidents") -> list[dict]:
    col = get_collection(collection_name)
    k = n_results or settings.rag_top_k
    results = col.query(query_texts=[text], n_results=k)

    docs = []
    for i, doc in enumerate(results["documents"][0]):
        docs.append({
            "text": doc,
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i] if results.get("distances") else None,
        })
    return docs


def add_incident_to_rag(incident: dict) -> str:
    text = (
        f"Incidente: {incident.get('title')}. "
        f"Tipo: {incident.get('attack_type')}. "
        f"Severidad: {incident.get('severity')}. "
        f"Descripción: {incident.get('description', '')}. "
        f"Recomendación: {incident.get('recommendation', '')}"
    )
    metadata = {
        "incident_id": str(incident.get("id", "")),
        "severity": incident.get("severity", ""),
        "attack_type": incident.get("attack_type", ""),
        "status": incident.get("status", ""),
    }
    return add_document(text, metadata)
