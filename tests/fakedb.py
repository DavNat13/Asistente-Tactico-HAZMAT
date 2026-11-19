"""MongoDB mínimo en memoria para pruebas (solo los operadores que usa el proyecto)."""

from __future__ import annotations

import copy
from types import SimpleNamespace

from pymongo.errors import DuplicateKeyError

_MISSING = object()


_OPS = {
    "$exists": lambda v, a: (v is not _MISSING) == a,
    "$lt": lambda v, a: v is not _MISSING and v < a,
    "$gte": lambda v, a: v is not _MISSING and v >= a,
    "$in": lambda v, a: v in a,
    "$ne": lambda v, a: v != a,
    "$type": lambda v, a: isinstance(v, str),
}


def _match_value(value, cond) -> bool:
    if isinstance(cond, dict) and any(k.startswith("$") for k in cond):
        return all(_OPS[op](value, arg) for op, arg in cond.items())
    if cond is None:
        return value is _MISSING or value is None
    return value == cond


def matches(doc: dict, flt: dict) -> bool:
    return all(_match_value(doc.get(k, _MISSING), c) for k, c in (flt or {}).items())


class FakeCollection:
    def __init__(self, unique: tuple[str, ...] = ()):
        self.docs: dict = {}
        self.unique = unique

    def create_index(self, *a, **k):
        return "ok"

    def _check_unique(self, doc: dict) -> None:
        for field in self.unique:
            value = doc.get(field)
            if value is not None and any(
                d.get(field) == value and d["_id"] != doc["_id"]
                for d in self.docs.values()
            ):
                raise DuplicateKeyError(f"dup {field}_unique")

    def insert_one(self, doc):
        doc = copy.deepcopy(doc)
        doc.setdefault("_id", f"id{len(self.docs) + 1}")
        if doc["_id"] in self.docs:
            raise DuplicateKeyError("dup _id")
        self._check_unique(doc)
        self.docs[doc["_id"]] = doc
        return SimpleNamespace(inserted_id=doc["_id"])

    def find_one(self, flt=None, projection=None):
        for d in self.docs.values():
            if matches(d, flt):
                return copy.deepcopy(d)
        return None

    def find(self, flt=None, projection=None):
        return [copy.deepcopy(d) for d in self.docs.values() if matches(d, flt)]

    def count_documents(self, flt):
        return len(self.find(flt))

    def replace_one(self, flt, doc, upsert=False):
        current = self.find_one(flt)
        if current:
            del self.docs[current["_id"]]
        elif not upsert:
            return SimpleNamespace(matched_count=0, modified_count=0)
        self.insert_one({**doc, "_id": doc.get("_id", flt.get("_id"))})
        return SimpleNamespace(matched_count=int(bool(current)), modified_count=1)

    def _apply(self, doc: dict, update: dict, inserting: bool) -> None:
        for k, v in update.get("$set", {}).items():
            doc[k] = v
        for k in update.get("$unset", {}):
            doc.pop(k, None)
        for k, v in update.get("$inc", {}).items():
            doc[k] = doc.get(k, 0) + v
        if inserting:
            doc.update(update.get("$setOnInsert", {}))
        self._check_unique(doc)

    def update_many(self, flt, update, upsert=False, _limit=None):
        hits = [d for d in self.docs.values() if matches(d, flt)][:_limit]
        for d in hits:
            self._apply(d, update, False)
        if not hits and upsert:
            doc = {k: v for k, v in flt.items() if not isinstance(v, dict)}
            self._apply(doc, update, True)
            self.insert_one(doc)
        return SimpleNamespace(matched_count=len(hits), modified_count=len(hits))

    def update_one(self, flt, update, upsert=False):
        return self.update_many(flt, update, upsert, _limit=1)

    def find_one_and_update(self, flt, update, upsert=False, return_document=True):
        self.update_one(flt, update, upsert)
        return self.find_one(flt)

    def delete_many(self, flt):
        ids = [d["_id"] for d in self.docs.values() if matches(d, flt)]
        for i in ids:
            del self.docs[i]
        return SimpleNamespace(deleted_count=len(ids))

    def delete_one(self, flt):
        doc = self.find_one(flt)
        return self.delete_many({"_id": doc["_id"]} if doc else {"_id": _MISSING})


class FakeDB(dict):
    def __missing__(self, name):
        col = FakeCollection(unique=("email",) if name == "users" else ())
        self[name] = col
        return col
