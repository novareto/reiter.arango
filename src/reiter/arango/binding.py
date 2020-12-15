import arango
import pydantic
import horseman.http
from typing import List, Optional, Type, Tuple
from reiter.arango.meta import ModelMetadata
from reiter.arango.transaction import transaction
from reiter.arango.validation import catch_pydantic_exception


class PydanticArango:

    db: arango.database.StandardDatabase
    model: Type[pydantic.BaseModel]
    collection: str

    def __init__(self, db, model):
        self.db = db
        self.model = model
        if hasattr(self.model, '__collection__'):
            self.collection = self.model.__collection__
        else:
            self.collection = self.model.__name__.lower()

    @catch_pydantic_exception
    def find(self, **filters) -> List[pydantic.BaseModel]:
        collection = self.db.collection(self.collection)
        return [self.model(**data) for data in collection.find(filters)]

    @catch_pydantic_exception
    def find_one(self, **filters) -> Optional[pydantic.BaseModel]:
        collection = self.db.collection(self.collection)
        found = collection.find(filters, limit=1)
        if not found.count():
            return None
        data = found.next()
        return self.model(**data)

    @catch_pydantic_exception
    def fetch(self, key) -> Optional[pydantic.BaseModel]:
        collection = self.db.collection(self.collection)
        if (data := collection.get(key)) is not None:
            return self.model(**data)

    @catch_pydantic_exception
    def create(self, key=None, **data) -> Tuple[pydantic.BaseModel, dict]:
        item = self.model(**data)
        try:
            with transaction(self.db, self.collection) as txn:
                collection = txn.collection(self.collection)
                if key is not None:
                    response = collection.insert(
                        {**item.dict(), '_key': key})
                else:
                    response = collection.insert(item.dict())
                if isinstance(item, ModelMetadata):
                    item.rev = response['_rev']
                    item.id = response['_id']
                return item, response
        except arango.exceptions.DocumentInsertError as exc:
            raise horseman.http.HTTPError(exc.http_code, exc.message)

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

    def replace(self, key, **data) -> str:
        try:
            with transaction(self.db, self.collection) as txn:
                collection = txn.collection(self.collection)
                data = {'_key': key, **data}
                response = collection.replace(data)
                return response
        except arango.exceptions.DocumentUpdateError as exc:
            raise horseman.http.HTTPError(exc.http_code, exc.message)

    def create_collection(self):
        self.db.create_collection(self.collection)
