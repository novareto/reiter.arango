import arango
import pydantic
import orjson
from typing import NamedTuple
from reiter.arango.transaction import transaction
from reiter.arango.binding import DBBinding


class Config(NamedTuple):
    url: str
    user: str
    password: str
    database: str


class Database(NamedTuple):

    db: arango.database.StandardDatabase

    def __call__(self, model):
        return DBBinding(self.db, model)

    def add(self, item):
        try:
            with transaction(self.db, item.__collection__) as txn:
                collection = txn.collection(item.__collection__)
                response = collection.insert(item.dict())
        except arango.exceptions.DocumentInsertError as exc:
            raise horseman.http.HTTPError(exc.http_code, exc.message)
        return response

    def save(self, item):
        try:
            with transaction(self.db, item.__collection__) as txn:
                collection = txn.collection(item.__collection__)
                data = item.dict()
                if '_rev' in data:
                    del data['_rev']
                response = collection.replace(data)
                item.rev = response["_rev"]
        except arango.exceptions.DocumentUpdateError as exc:
            raise horseman.http.HTTPError(exc.http_code, exc.message)
        return response

    def delete(self, item) -> bool:
        binding = DBBinding(self.db, item.__class__)
        return binding.delete(item.key)

    def update(self, item, **data) -> str:
        binding = DBBinding(self.db, item.__class__)
        response = binding.update(item.key, **data)
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
