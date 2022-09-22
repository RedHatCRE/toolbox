from pytest_mock import MockerFixture

from cre.interfaces.pygerrit.connectors.connector import Query
from cre.interfaces.pygerrit.connectors.ssh_connector import SSHConnector
from cre.interfaces.pygerrit.connectors.ssh_connector import SSHTarget


def test_enter(mocker: MockerFixture):
    client = mocker.Mock()
    target = SSHTarget('localhost', 23, 'test', 'pass')

    connector = SSHConnector(client, target)

    # Check that it is compatible with the 'with' keyword
    assert connector == connector.__enter__()

    client.connect.assert_called_with(
        target.host,
        target.port,
        target.user,
        target.password
    )


def test_exit(mocker: MockerFixture):
    client = mocker.Mock()
    target = SSHTarget('localhost')

    connector = SSHConnector(client, target)
    connector.__exit__(None, None, None)

    client.close.assert_called()


class TestQuery:
    def test_with_patch_set(self, mocker: MockerFixture):
        # Set up
        stdin = mocker.Mock()
        stdout = mocker.Mock()
        stderr = mocker.Mock()

        client = mocker.Mock()
        target = SSHTarget('localhost', 23, 'test', 'pass')

        commit = 'commit'
        query = Query(patch_sets=commit)

        expected_result = ['answer']

        connector = SSHConnector(client, target)

        # Mock calls
        client.exec_command = mocker.Mock()
        client.exec_command.return_value = (stdin, stdout, stderr)

        stdout.readlines = mocker.Mock()
        stdout.readlines.return_value = expected_result

        stderr.readlines = mocker.Mock()
        stderr.readlines.return_value = []

        # Make the query
        result = connector.query(query)

        # Check what was called
        client.exec_command.assert_called_with(
            'gerrit query --patch-sets {set}'.format(set=commit)
        )

        stdout.readlines.assert_called()
        stderr.readlines.assert_called()

        stdin.close.assert_called()
        stdout.close.assert_called()
        stderr.close.assert_called()

        # Check result
        assert result == expected_result
