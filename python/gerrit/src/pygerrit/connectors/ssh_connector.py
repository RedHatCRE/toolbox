from dataclasses import dataclass

from paramiko import SSHClient

from .connector import APIException, Connector, Query


@dataclass
class SSHTarget:
    host: str
    port: int = 29418
    user: str = None
    password: str = None


class SSHConnector(Connector):
    def __init__(self, client: SSHClient, target: SSHTarget) -> None:
        self.client = client
        self.target = target

    def __enter__(self) -> Connector:
        try:
            self.client.connect(
                self.target.host,
                self.target.port,
                self.target.user,
                self.target.password
            )
        except Exception as ex:
            raise APIException() from ex

        return self

    def __exit__(self, *_) -> None:
        self.client.close()

    def query(self, query: Query) -> list[str]:
        result = []
        command = self._generate_query(query)

        try:
            stdin, stdout, stderr = self.client.exec_command(command)

            # Retrieve host's answer
            result += stdout.readlines()
            result += stderr.readlines()

            # These are files and their handles needs to be closed
            stdin.close()
            stdout.close()
            stderr.close()
        except Exception as ex:
            raise APIException() from ex

        return result

    # TODO: Move this method to its own class -> For easier testing
    @staticmethod
    def _generate_query(query: Query) -> str:
        command = 'gerrit query'

        if query.patch_sets:
            command += \
                ' --patch-sets {change}'.format(change=query.patch_sets)

        return command
