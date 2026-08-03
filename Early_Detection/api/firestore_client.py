"""
Minimal Firestore REST API client — no Firebase Admin SDK, no service account
key needed. Works because the Firestore database is in "test mode" (open
security rules), which is fine for a thesis project.

IMPORTANT (read before your final submission): test-mode rules automatically
expire ~30 days after the database was created. After that, Firestore will
reject these requests with a permission error until you update the rules in
the Firebase Console (Firestore Database -> Rules) to something like:

    rules_version = '2';
    service cloud.firestore {
      match /databases/{database}/documents {
        match /{document=**} {
          allow read, write: if true;   // fine for a course project, not for production
        }
      }
    }

No API key or credentials are required for this to work in test mode.
"""

import requests
import datetime

PROJECT_ID = "mindsense-1f132"
BASE_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"


# ---------------------------------------------------------------------------
# Convert between plain Python dicts and Firestore's typed JSON format
# ---------------------------------------------------------------------------
def _to_firestore_value(value):
    if isinstance(value, bool):
        return {"booleanValue": value}
    if isinstance(value, int):
        return {"integerValue": str(value)}
    if isinstance(value, float):
        return {"doubleValue": value}
    if isinstance(value, str):
        return {"stringValue": value}
    if value is None:
        return {"nullValue": None}
    raise TypeError(f"Unsupported type for Firestore: {type(value)}")


def _from_firestore_value(fv: dict):
    if "stringValue" in fv:
        return fv["stringValue"]
    if "integerValue" in fv:
        return int(fv["integerValue"])
    if "doubleValue" in fv:
        return float(fv["doubleValue"])
    if "booleanValue" in fv:
        return fv["booleanValue"]
    if "nullValue" in fv:
        return None
    return None


def _to_fields(data: dict) -> dict:
    return {k: _to_firestore_value(v) for k, v in data.items()}


def _from_document(doc: dict) -> dict:
    """Converts a raw Firestore REST document into a flat Python dict,
    plus adds an 'id' key extracted from the document's resource name."""
    result = {k: _from_firestore_value(v) for k, v in doc.get("fields", {}).items()}
    result["id"] = doc["name"].rsplit("/", 1)[-1]
    return result


# ---------------------------------------------------------------------------
# Basic operations
# ---------------------------------------------------------------------------
def create_document(collection: str, data: dict, doc_id: str = None, parent: str = None) -> dict:
    """Creates a new document. If doc_id is given, uses it as the document ID
    (e.g. for auth_tokens, where the token itself is the ID). Otherwise Firestore
    auto-generates one. `parent` lets you create inside a subcollection, e.g.
    parent='patients/abc123' + collection='health_metrics'."""
    base = f"{BASE_URL}/{parent}" if parent else BASE_URL
    url = f"{base}/{collection}"
    params = {"documentId": doc_id} if doc_id else {}
    body = {"fields": _to_fields(data)}

    resp = requests.post(url, params=params, json=body, timeout=10)
    resp.raise_for_status()
    return _from_document(resp.json())


def get_document(path: str):
    """path example: 'patients/abc123' or 'auth_tokens/<token>'."""
    url = f"{BASE_URL}/{path}"
    resp = requests.get(url, timeout=10)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return _from_document(resp.json())


def delete_document(path: str):
    url = f"{BASE_URL}/{path}"
    requests.delete(url, timeout=10)


def query_collection(collection: str, field: str = None, op: str = "EQUAL", value=None,
                      order_by: str = None, parent: str = None, limit: int = None):
    """Runs a query against a (sub)collection. parent example: 'patients/abc123'
    to query that patient's 'health_metrics' subcollection."""
    parent_path = f"{BASE_URL}/{parent}" if parent else BASE_URL
    url = f"{parent_path}:runQuery"

    structured_query = {"from": [{"collectionId": collection}]}

    if field is not None:
        structured_query["where"] = {
            "fieldFilter": {
                "field": {"fieldPath": field},
                "op": op,
                "value": _to_firestore_value(value),
            }
        }

    if order_by:
        structured_query["orderBy"] = [{"field": {"fieldPath": order_by}, "direction": "ASCENDING"}]

    if limit:
        structured_query["limit"] = limit

    resp = requests.post(url, json={"structuredQuery": structured_query}, timeout=10)
    resp.raise_for_status()

    results = []
    for item in resp.json():
        if "document" in item:
            results.append(_from_document(item["document"]))
    return results
