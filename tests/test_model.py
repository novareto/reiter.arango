import pytest
import typing
import pydantic
from reiter.arango.connector import Database
from reiter.arango.model import arango_model


class Document(pydantic.BaseModel):

    __collection__ = 'docs'

    name: str
    body: typing.Optional[str] = ""

    @property
    def __key__(self):
        return self.name


def test_API(arangodb):

    database = Database(arangodb)
    database(Document).create_collection()

    doc = database(Document).fetch('test')
    assert doc is None

    doc = Document(name="test", body="My document")
    database.add(doc)

    doc = database(Document).fetch('test')
    assert doc is not None

    database.update(doc, body='I changed the body')
    assert doc.body == 'I changed the body'

    doc = database(Document).fetch('test')
    assert doc.body == 'I changed the body'

    doc.body = 'I changed the body again'
    database.save(doc)

    doc = database(Document).fetch('test')
    assert doc.body == 'I changed the body again'

    database.delete(doc)
    doc = database(Document).fetch('test')
    assert doc is None
