import pytest
import typing
import pydantic
import hamcrest
from reiter.arango.connector import Database


class Document(pydantic.BaseModel):
    name: str
    body: typing.Optional[str] = ""


def test_API(arangodb):

    database = Database(arangodb)
    database(Document).create_collection()

    doc = database(Document).fetch('test')
    assert doc is None

    doc = Document(name="test", body="My document")
    response = database.add(doc)
    doc_key = response['_key']

    doc = database(Document).fetch(doc_key)
    assert doc is not None

    response = database.update(doc, body='I changed the body')
    assert doc.body == 'I changed the body'
    hamcrest.assert_that(response, hamcrest.has_entries({
        '_id': 'docs/test',
        '_key': 'test',
        '_rev': hamcrest.instance_of(str),
        '_old_rev': hamcrest.instance_of(str)
    }))

    doc = database(Document).fetch('test')
    assert doc.body == 'I changed the body'

    doc.body = 'I changed the body again'
    response = database.save(doc)
    hamcrest.assert_that(response, hamcrest.has_entries({
        '_id': 'docs/test',
        '_key': 'test',
        '_rev': hamcrest.instance_of(str),
        '_old_rev': hamcrest.instance_of(str)
    }))

    doc = database(Document).fetch('test')
    assert doc.body == 'I changed the body again'

    database.delete(doc)
    doc = database(Document).fetch('test')
    assert doc is None
