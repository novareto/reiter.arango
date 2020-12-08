from abc import abstractmethod
from typing import Optional, ClassVar
import pydantic
from reiter.arango.meta import Factory


class DBModel(Factory, pydantic.BaseModel):

    id: Optional[str] = pydantic.Field(alias="_id")
    key: Optional[str] = pydantic.Field(alias="_key")
    rev: Optional[str] = pydantic.Field(alias="_rev")

    _binding = pydantic.PrivateAttr(default=None)

    def bind(self, binding, id=None, key=None, rev=None):
        assert not self.bound
        if id is not None:
            self.id = id
        if key is not None:
            self.key = key
        if rev is not None:
            self.rev = rev
        self._binding = binding

    def unbind(self):
        self.id = None
        self.key = None
        self.rev = None
        self._binding = None

    @property
    def bound(self):
        return (self._binding is not None
                and self.id is not None
                and self.key is not None
                and self.rev is not None)

    @classmethod
    def spawn(cls, binding, **data):
        assert '_key' in data
        assert '_id' in data
        assert '_rev' in data
        item = cls(**data)
        item.bind(binding)
        return item

    def delete(self):
        assert self.bound
        self._binding.delete(self.key)
        self.unbind()

    def save(self):
        self._binding.db.replace(self)

    def update(self, **data) -> str:
        assert self.bound
        for key, value in data.items():
            setattr(self, key, value)
        self.rev = self._binding.update(self.key, **data)

    def dict(self, by_alias=True, **kwargs):
        if hasattr(self, '__key__'):
            self.key = self.__key__
        return super().dict(by_alias=by_alias, **kwargs)

    def json(self, by_alias=True, **kwargs):
        return super().json(by_alias=by_alias, **kwargs)


class PluggableModel(Factory):

    @abstractmethod
    def lookup(self, **data) -> DBModel:
        pass

    @classmethod
    def spawn(cls, binding, **data):
        assert '_key' in data
        assert '_id' in data
        assert '_rev' in data
        model_class = self.lookup(**data)
        item = model_class(**data)
        item.bind(binding)
        return item


class arango_model:

    def __init__(self, collection):
        self.collection = collection

    def __call__(self, model_class):
        model = type(
            f"Arango{model_class.__name__}", (DBModel, model_class), {
                "__collection__": self.collection,
                "__modelclass__": model_class
            })
        return model
