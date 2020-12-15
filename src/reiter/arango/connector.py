import arango
import horseman.http
import orjson
import pydantic
from typing import NamedTuple
from reiter.arango.binding import PydanticArango
from reiter.arango.meta import Model, ModelMetadata
from reiter.arango.transaction import transaction


class Config(NamedTuple):
    url: str
    user: str
    password: str
    database: str


class Database:

    __slots__ = ('db',)

    def __init__(self, db: arango.database.StandardDatabase):
        self.db = db

    def __call__(self, model):
        return PydanticArango(self.db, model)

    def add(self, item: Model):
        assert isinstance(item, Model)
        try:
            with transaction(self.db, item.__collection__) as txn:
                collection = txn.collection(item.__collection__)
                response = collection.insert(item.dict())
        except arango.exceptions.DocumentInsertError as exc:
            raise horseman.http.HTTPError(exc.http_code, exc.message)
        return response

    def save(self, item: Model):
        assert isinstance(item, Model)
        try:
            with transaction(self.db, item.__collection__) as txn:
                collection = txn.collection(item.__collection__)
                data = item.dict()
                if '_rev' in data:
                    del data['_rev']
                response = collection.replace(data)
            if isinstance(item, ModelMetadata):
                item.rev = response["_rev"]
            return response
        except arango.exceptions.DocumentUpdateError as exc:
            raise horseman.http.HTTPError(exc.http_code, exc.message)

    def delete(self, item: Model) -> bool:
        assert isinstance(item, Model)
        binding = self(item.__class__)
        return binding.delete(item.key)

    def update(self, item: Model, **data) -> str:
        assert isinstance(item, Model)
        binding = self(item.__class__)
        response = binding.update(item.key, **data)
        if isinstance(item, ModelMetadata):
            item.rev = response["_rev"]
        for name, value in data.items():
            setattr(item, name, value)
        return response


class Connector:

    __slots__ = ('config', 'client')

    @staticmethod
    def json_dumps(v, *args, **kwargs):
        if 'password' in v:
            if isinstance(v['password'], pydantic.types.SecretStr):
                v['password'] = v['password'].get_secret_value()
        return orjson.dumps(v)

    def __init__(self, url: str = 'http://localhost:8529', **config):
        self.config = Config(url=url, **config)
        self.client = arango.ArangoClient(
            url,
            serializer=self.json_dumps,
            deserializer=orjson.loads
        )

    @property
    def _system(self):
        return self.client.db(
            '_system',
            username=self.config.user,
            password=self.config.password
        )

    def delete_database(self):
        sys = self._system
        if not sys.has_database(self.config.database):
            sys.delete_database(self.config.database)
            return True
        return False

    def get_database(self):
        sys = self._system
        if not sys.has_database(self.config.database):
            sys.create_database(self.config.database)
        return Database(db=self.client.db(
            self.config.database,
            username=self.config.user,
            password=self.config.password
        ))
