"""
CRE - Detect-Submit

Usage:
    detect_submit.py CFG_FILE
    detect_submit.py (-h | --help)
    detect_submit.py --version

Options:
    -h --help       Show this screen.
    --version       Show version.

Others:
    Structure of a config file:
        [gerrit]
        host=(...)
        port=[...]
        user=[...]
        pass=[...]
        branch=(...)
"""
from collections.abc import Iterable

from docopt import docopt

from cre.interfaces.pygerrit.connectors.connector import Connector
from cre.interfaces.pygerrit.connectors.ssh_connector import SSHTarget
from cre.scripting.config import CFG_BRANCH_OPTION
from cre.scripting.config import CFG_HOST_OPTION
from cre.scripting.config import CFG_PASS_OPTION
from cre.scripting.config import CFG_PORT_OPTION
from cre.scripting.config import CFG_USER_OPTION
from cre.scripting.config import load_config
from cre.scripting.gerrit.scripts import get_components_not_in
from cre.scripting.gerrit.scripts import get_components_with_change_id
from cre.scripting.gerrit.scripts import open_ssh_session
from cre.scripting.git.scripts import create_and_review_change_for


def _open_gerrit_session(config: dict[str, str]) -> Connector:
    return open_ssh_session(
        SSHTarget(
            host=config[CFG_HOST_OPTION],
            port=int(config[CFG_PORT_OPTION]),
            user=config[CFG_USER_OPTION],
            password=config[CFG_PASS_OPTION]
        )
    )


def _get_components_without_change_id(session: Connector) -> Iterable[str]:
    return get_components_not_in(get_components_with_change_id(session))


def main(argv):
    cfg = load_config(argv['CFG_FILE'])

    with _open_gerrit_session(cfg) as session:
        for component in _get_components_without_change_id(session):
            create_and_review_change_for(
                host=cfg[CFG_HOST_OPTION],
                user=cfg[CFG_USER_OPTION],
                password=cfg[CFG_PASS_OPTION],
                project=component,
                branch=cfg[CFG_BRANCH_OPTION]
            )


if __name__ == '__main__':
    args = docopt(__doc__, version='CRE - Detect-Submit 1.0')

    main(args)
