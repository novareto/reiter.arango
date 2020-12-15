import typing
import pydantic
from reiter.arango.meta import Model, ModelMetadata


class ArangoModel(Model, ModelMetadata, pydantic.BaseModel):

    id: typing.Optional[str] = pydantic.Field(alias="_id")
    key: typing.Optional[str] = pydantic.Field(alias="_key")
    rev: typing.Optional[str] = pydantic.Field(alias="_rev")

    def dict(self, by_alias=True, **kwargs):
        if hasattr(self, '__key__'):
            self.key = self.__key__
        return super().dict(by_alias=by_alias, **kwargs)

    def json(self, by_alias=True, **kwargs):
        return super().json(by_alias=by_alias, **kwargs)
