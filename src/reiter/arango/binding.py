import arango
import pydantic
from typing import List, Optional
from reiter.arango.transaction import transaction


class DBBinding:

    def __init__(self, model, db):
        self.db = db
        self.model = model

    def find(self, **filters) -> List[pydantic.BaseModel]:
        collection = self.db.collection(self.model.__collection__)
        return [self.model.spawn(self, **data)
                for data in collection.find(filters)]

    def find_one(self, **filters) -> Optional[pydantic.BaseModel]:
        collection = self.db.collection(self.model.__collection__)
        found = collection.find(filters, limit=1)
        if not found.count():
            return None
        data = found.next()
        return self.model.spawn(self, **data)

    def fetch(self, key) -> Optional[pydantic.BaseModel]:
        collection = self.db.collection(self.model.__collection__)
        if (data := collection.get(key)) is not None:
            return self.model.spawn(self, **data)

    def exists(self, key) -> bool:
        collection = self.db.collection(self.model.__collection__)
        return collection.has({"_key": key})

    def delete(self, key) -> bool:
        try:
            with transaction(self.db, self.model.__collection__) as txn:
                collection = txn.collection(self.model.__collection__)
                collection.delete(key)
        except arango.exceptions.DocumentDeleteError as exc:
            raise horseman.http.HTTPError(exc.http_code, exc.message)

    def update(self, key, **data) -> str:
        try:
            with transaction(self.db, self.model.__collection__) as txn:
                collection = txn.collection(self.model.__collection__)
                data = {'_key': key, **data}
                response = collection.update(data)
                return response["_rev"]
        except arango.exceptions.DocumentUpdateError as exc:
            raise horseman.http.HTTPError(exc.http_code, exc.message)
