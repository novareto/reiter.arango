from abc import ABC, abstractmethod
from typing import Iterable, Optional, ClassVar, Type


class Model(ABC):
    key: Optional[str]
    __collection__: ClassVar[str]


class ModelMetadata(ABC):
    id: Optional[str]
    rev: Optional[str]


class Binding(ABC):

    model: Type[Model]

    @abstractmethod
    def create_collection(self):
        pass

    @abstractmethod
    def find(self, **filters) -> Iterable[Model]:
        pass

    @abstractmethod
    def find_one(self, **filters) -> Optional[Model]:
        pass

    @abstractmethod
    def fetch(self, key) -> Optional[Model]:
        pass

    @abstractmethod
    def exists(self, key) -> bool:
        pass

    @abstractmethod
    def delete(self, key) -> None:
        pass

    @abstractmethod
    def update(self, key, **data) -> dict:
        pass


class Database(ABC):

    @abstractmethod
    def __call__(self, model: Type[Model]) -> Binding:
        pass

    @abstractmethod
    def add(self, item) -> dict:
        pass

    @abstractmethod
    def update(self, item, **data) -> dict:
        pass

    @abstractmethod
    def save(self, item) -> dict:
        pass

    @abstractmethod
    def delete(self, item) -> None:
        pass
