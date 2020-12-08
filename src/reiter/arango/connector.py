import arango
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

    arango_db: arango.database.StandardDatabase

    def bind(self, model):
        return DBBinding(model, self.arango_db)

    def add(self, item):
        assert not item.bound
        try:
            with transaction(self.arango_db, item.__collection__) as txn:
                collection = txn.collection(item.__collection__)
                response = collection.insert(item.dict())
                item.bind(
                    DBBinding(item.__class__, self.arango_db),
                    id=response["_id"],
                    key=response["_key"],
                    rev=response["_rev"]
                )
        except arango.exceptions.DocumentInsertError as exc:
            raise horseman.http.HTTPError(exc.http_code, exc.message)
        return item

    def replace(self, item):
        try:
            with transaction(self.arango_db, item.__collection__) as txn:
                collection = txn.collection(item.__collection__)
                data = item.dict()
                response = collection.replace(data)
                item.rev = response["_rev"]
                item.bind(
                    DBBinding(item.__class__, self.arango_db),
                    rev=response["_rev"]
                )
        except arango.exceptions.DocumentUpdateError as exc:
            raise horseman.http.HTTPError(exc.http_code, exc.message)
        return item


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
        return Database(arango_db=self.client.db(
            self.config.database,
            username=self.config.user,
            password=self.config.password
        ))
