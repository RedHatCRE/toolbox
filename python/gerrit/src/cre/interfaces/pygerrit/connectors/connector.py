from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass


class APIException(Exception):
    pass


@dataclass
class Query:
    patch_sets: str = None


class Connector(ABC):
    @abstractmethod
    def query(self, query: Query) -> list[str]:
        pass
