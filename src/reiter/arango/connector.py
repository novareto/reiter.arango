import arango
from typing import NamedTuple
from reiter.arango.transaction import transaction
from reiter.arango.binding import DBBinding


class Config(NamedTuple):
    url: str
    user: str
    password: str
    database: str


class Database(NamedTuple):

    database: arango.database.StandardDatabase

    def query(self, model):
        return DBBinding(model, self.database)

    def add(self, item):
        assert not item.bound
        try:
            with transaction(self.session, self.collection) as txn:
                collection = txn.collection(self.collection)
                response = collection.insert(item.dict())
                item.bind(
                    DBBinding(item.__class__, self.database),
                    id=response["_id"],
                    key=response["_key"],
                    rev=response["_rev"]
                )
        except arango.exceptions.DocumentInsertError as exc:
            raise horseman.http.HTTPError(exc.http_code, exc.message)
        return item

    def replace(self, item):
        try:
            with transaction(self.session, self.collection) as txn:
                collection = txn.collection(self.collection)
                data = item.dict()
                response = collection.replace(data)
                item.rev = response["_rev"]
                item.bind(
                    DBBinding(item.__class__, self.database),
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
    def system_database(self):
        return self.client.db(
            '_system',
            username=self.config.user,
            password=self.config.password
        )

    @property
    def database(self):
        return self.client.db(
            self.config.database,
            username=self.config.user,
            password=self.config.password
        )

    def ensure_database(self):
        sys_db = self.system_database
        if not sys_db.has_database(self.config.database):
            sys_db.create_database(self.config.database)

    def delete_database(self):
        sys_db = self.system_database
        if not sys_db.has_database(self.config.database):
            sys_db.delete_database(self.config.database)
