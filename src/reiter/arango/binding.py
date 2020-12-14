import arango
import pydantic
import horseman.http
from typing import List, Optional, Type
from reiter.arango.transaction import transaction


class DBBinding:

    db: arango.database.StandardDatabase
    model: Type[pydantic.BaseModel]

    def __init__(self, db, model):
        self.db = db
        self.model = model
        if hasattr(self.model, '__collection__'):
            self.collection = self.model.__collection__
        else:
            self.collection = self.model.__name__.lower()

    def create_collection(self):
        self.db.create_collection(self.collection)

    def find(self, **filters) -> List[pydantic.BaseModel]:
        collection = self.db.collection(self.collection)
        return [self.model(**data) for data in collection.find(filters)]

    def find_one(self, **filters) -> Optional[pydantic.BaseModel]:
        collection = self.db.collection(self.collection)
        found = collection.find(filters, limit=1)
        if not found.count():
            return None
        data = found.next()
        return self.model(**data)

    def fetch(self, key) -> Optional[pydantic.BaseModel]:
        collection = self.db.collection(self.collection)
        if (data := collection.get(key)) is not None:
            return self.model(**data)

    def exists(self, key) -> bool:
        collection = self.db.collection(self.collection)
        return collection.has({"_key": key})

    def delete(self, key) -> bool:
        try:
            with transaction(self.db, self.collection) as txn:
                collection = txn.collection(self.collection)
                collection.delete(key)
        except arango.exceptions.DocumentDeleteError as exc:
            raise horseman.http.HTTPError(exc.http_code, exc.message)

    def update(self, key, **data) -> str:
        try:
            with transaction(self.db, self.collection) as txn:
                collection = txn.collection(self.collection)
                data = {'_key': key, **data}
                response = collection.update(data)
                return response
        except arango.exceptions.DocumentUpdateError as exc:
            raise horseman.http.HTTPError(exc.http_code, exc.message)
