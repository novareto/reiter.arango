class DBModel(pydantic.BaseModel):

    id: Optional[str] = pydantic.Field(alias="_id")
    key: Optional[str] = pydantic.Field(alias="_key")
    rev: Optional[str] = pydantic.Field(alias="_rev")

    __collection__: ClassVar[str]
    _binding = pydantic.PrivateAttr(default=None)

    def bind(self, binding, id=..., key=..., rev=...):
        assert not self.bound
        if self.id != ...:
            self.id = id
        if self.key != ...:
            self.key = key
        if self.rev != ...:
            self.rev = rev
        self._binding = binding

    def unbind(self):
        self.id = None
        self.key = None
        self.rev = None
        self._binding = None

    @property
    def bound(self):
        return (self._binding is not None and
                self.id and self.key and self.rev)

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

    def update(self, **data) -> str:
        assert self.bound
        for key, value in data.items():
            setattr(self, key, value)
        self.rev = self._binding.update(self.key, **data)


class arango_model:

    def __init__(self, collection):
        self.collection = collection

    def __call__(self, model_class):
        model = type(
            f"Arango{model_class.__name__}", (DBModel, model_class), {
                "__collection__": self.collection
            })
        return model
