from collections.abc import Iterable
from configparser import ConfigParser

CFG_SECTION = 'gerrit'

CFG_HOST_OPTION = 'host'
CFG_PORT_OPTION = 'port'
CFG_USER_OPTION = 'user'
CFG_PASS_OPTION = 'password'
CFG_BRANCH_OPTION = 'branch'

CFG_DEFAULT_PORT = 22
CFG_DEFAULT_USER = None
CFG_DEFAULT_PASS = None


class ConfigException(Exception):
    pass


def _print_missed_files(
    candidates: Iterable[str], found: Iterable[str]
) -> None:
    for missed in (set(candidates) - set(found)):
        print('File not found: %s' % missed)


def _parse_files(
    parser: ConfigParser, candidates: Iterable[str]
) -> Iterable[str]:
    found = parser.read(candidates)

    _print_missed_files(candidates, found)

    return found


def _validate_config(parser: ConfigParser) -> None:
    if not parser.has_section(CFG_SECTION):
        raise ConfigException('Missing section: %s' % CFG_SECTION)

    for key in [CFG_HOST_OPTION, CFG_BRANCH_OPTION]:
        if not parser.has_option(CFG_SECTION, key):
            raise ConfigException('Missing key: %s' % key)


def _extract_config(parser: ConfigParser) -> dict[str, str]:
    config = {
        CFG_HOST_OPTION: parser.get(CFG_SECTION, CFG_HOST_OPTION),
        CFG_PORT_OPTION: CFG_DEFAULT_PORT,
        CFG_USER_OPTION: CFG_DEFAULT_USER,
        CFG_PASS_OPTION: CFG_DEFAULT_PASS,
        CFG_BRANCH_OPTION: parser.get(CFG_SECTION, CFG_BRANCH_OPTION)
    }

    if parser.has_option(CFG_SECTION, CFG_PORT_OPTION):
        config[CFG_PORT_OPTION] = parser.get(CFG_SECTION, CFG_PORT_OPTION)

    if parser.has_option(CFG_SECTION, CFG_USER_OPTION):
        config[CFG_USER_OPTION] = parser.get(CFG_SECTION, CFG_USER_OPTION)

    if parser.has_option(CFG_SECTION, CFG_PASS_OPTION):
        config[CFG_PASS_OPTION] = parser.get(CFG_SECTION, CFG_PASS_OPTION)

    return config


def load_config(file: str) -> dict[str, str]:
    parser = ConfigParser()

    _parse_files(parser, [file])
    _validate_config(parser)

    return _extract_config(parser)
