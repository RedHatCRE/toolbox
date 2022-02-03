import re
from abc import ABC, abstractmethod
from queue import Queue

from .connectors.connector import Connector, Query


class Command(ABC):
    @abstractmethod
    def execute(self) -> None:
        pass


class RetrieveProjectCommand(Command):
    def __init__(self, connector: Connector, change_id: str) -> None:
        super().__init__()

        self.connector = connector
        self.change_id = change_id

    def execute(self) -> str | None:
        answer = self.connector.query(Query(patch_sets=self.change_id))

        for line in answer:
            match = re.search(r'(?<=project:\s).*$', line)

            if match:
                return match.group(0)

        return None


class CommandQueue:
    def __init__(self) -> None:
        self.queue = Queue()

    def add_command(self, command: Command) -> None:
        self.queue.put(command)

    def has_next(self) -> bool:
        return not self.queue.empty()

    def execute_next(self) -> str | None:
        if not self.has_next():
            return None

        return self.queue.get().execute()


class Client:
    def __init__(self, invoker: CommandQueue, receiver: Connector) -> None:
        self.invoker = invoker
        self.receiver = receiver

    def request_project_of_change(self, change_id: str) -> None:
        self.invoker.add_command(
            RetrieveProjectCommand(self.receiver, change_id)
        )
