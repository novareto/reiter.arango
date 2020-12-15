from contextlib import contextmanager


@contextmanager
def transaction(db, collection):
    transaction = db.begin_transaction(exclusive=collection)
    try:
        yield transaction
        transaction.commit_transaction()
    except Exception:
        transaction.abort_transaction()
        raise
