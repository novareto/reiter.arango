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

    doc, response = database(Document).create(
        name="test", body="My document")
    doc_key = response['_key']

    doc = database(Document).fetch(doc_key)
    assert doc is not None

    response = database(Document).update(doc_key, body='I changed the body')
    hamcrest.assert_that(response, hamcrest.has_entries({
        '_id': f'document/{doc_key}',
        '_key': doc_key,
        '_rev': hamcrest.instance_of(str),
        '_old_rev': hamcrest.instance_of(str)
    }))

    doc = database(Document).fetch(doc_key)
    assert doc.body == 'I changed the body'

    doc.body = 'I changed the body again'
    response = database(Document).replace(doc_key, **doc.dict())
    hamcrest.assert_that(response, hamcrest.has_entries({
        '_id': f'document/{doc_key}',
        '_key': doc_key,
        '_rev': hamcrest.instance_of(str),
        '_old_rev': hamcrest.instance_of(str)
    }))

    doc = database(Document).fetch(doc_key)
    assert doc.body == 'I changed the body again'

    database(Document).delete(doc_key)
    doc = database(Document).fetch(doc_key)
    assert doc is None
