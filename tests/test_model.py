import pytest
import typing
import pydantic
from reiter.arango.connector import Database
from reiter.arango.model import arango_model


@arango_model('docs')
class Document(pydantic.BaseModel):
    name: str
    body: typing.Optional[str] = ""

    @property
    def __key__(self):
        return self.name


def test_API(arangodb):

    database = Database(database=arangodb)
    database.database.create_collection('docs')

    doc = database.bind(Document).fetch('test')
    assert doc is None

    doc = Document(name="test", body="My document")
    database.add(doc)

    doc = database.bind(Document).fetch('test')
    assert doc is not None

    doc.delete()
    assert not doc.bound
    doc = database.bind(Document).fetch('test')
    assert doc is None
