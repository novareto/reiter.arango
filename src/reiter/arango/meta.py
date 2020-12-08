from abc import ABC, abstractmethod
from typing import Iterable, Optional, ClassVar, Type


class Model(ABC):

    id: Optional[str]
    key: Optional[str]
    rev: Optional[str]

    @abstractmethod
    def delete(self, key) -> bool:
        pass

    @abstractmethod
    def update(self, item) -> bool:
        pass


class Factory(ABC):

    __collection__: ClassVar[str]

    @abstractmethod
    def spawn(self, **data) -> Model:
        pass


class Binding(ABC):

    factory: Type[Factory]

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
    def update(self, key, **data) -> str:
        pass


class Database(ABC):

    @abstractmethod
    def query(self, model) -> Binding:
        pass

    @abstractmethod
    def add(self, item) -> Model:
        pass

    @abstractmethod
    def replace(self, item) -> Model:
        pass
