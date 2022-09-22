from paramiko.client import AutoAddPolicy
from paramiko.client import SSHClient

from cre.interfaces.pygerrit.client import CommandQueue
from cre.interfaces.pygerrit.client import GerritClient
from cre.interfaces.pygerrit.connectors.connector import Connector
from cre.interfaces.pygerrit.connectors.ssh_connector import SSHConnector
from cre.interfaces.pygerrit.connectors.ssh_connector import SSHTarget
from cre.scripting.gerrit.data import CHANGE_IDS
from cre.scripting.gerrit.data import COMPONENTS


def open_ssh_session(target: SSHTarget) -> SSHConnector:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())

    return SSHConnector(ssh, target)


def get_components_with_change_id(session: Connector) -> list[str]:
    result = []

    gerrit = GerritClient(CommandQueue(), session)

    # Create a command for each change
    for change_id in CHANGE_IDS:
        gerrit.request_project_of_change(change_id)

    # Consume commands
    while gerrit.invoker.has_next():
        component = gerrit.invoker.execute_next()

        if component:
            result.append(component)

    return result


def get_components_not_in(collection: list[str]) -> list[str]:
    result = []

    for component in COMPONENTS:
        if component not in collection:
            result.append(component)

    return result
