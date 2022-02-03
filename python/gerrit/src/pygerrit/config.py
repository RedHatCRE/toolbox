from configparser import ConfigParser
from os.path import expanduser


def _get_user_home() -> str:
    return expanduser('~')


CFG_CANDIDATES = [
    '%s/.config/gerrit.conf' % _get_user_home()
]

CFG_SECTION = 'gerrit'

CFG_HOST_OPTION = 'host'
CFG_PORT_OPTION = 'port'
CFG_USER_OPTION = 'user'
CFG_PASS_OPTION = 'password'

CFG_DEFAULT_PORT = 22
CFG_DEFAULT_USER = None
CFG_DEFAULT_PASS = None


class ConfigException(Exception):
    pass


def _print_missed_files(found: list[str]) -> None:
    for missed in (set(CFG_CANDIDATES) - set(found)):
        print('File not found: %s' % missed)


def _parse_files(parser: ConfigParser) -> list[str]:
    found = parser.read(CFG_CANDIDATES)

    _print_missed_files(found)

    return found


def _validate_config(parser: ConfigParser) -> None:
    if not parser.has_section(CFG_SECTION):
        raise ConfigException('Missing section: %s' % CFG_SECTION)

    for key in [CFG_HOST_OPTION]:
        if not parser.has_option(CFG_SECTION, key):
            raise ConfigException('Missing key: %s' % key)


def _extract_config(parser: ConfigParser) -> dict[str, str]:
    config = {
        CFG_HOST_OPTION: parser.get(CFG_SECTION, CFG_HOST_OPTION),
        CFG_PORT_OPTION: CFG_DEFAULT_PORT,
        CFG_USER_OPTION: CFG_DEFAULT_USER,
        CFG_PASS_OPTION: CFG_DEFAULT_PASS
    }

    if parser.has_option(CFG_SECTION, CFG_PORT_OPTION):
        config[CFG_PORT_OPTION] = parser.get(CFG_SECTION, CFG_PORT_OPTION)

    if parser.has_option(CFG_SECTION, CFG_USER_OPTION):
        config[CFG_USER_OPTION] = parser.get(CFG_SECTION, CFG_USER_OPTION)

    if parser.has_option(CFG_SECTION, CFG_PASS_OPTION):
        config[CFG_PASS_OPTION] = parser.get(CFG_SECTION, CFG_PASS_OPTION)

    return config


def load_config() -> dict[str, str]:
    parser = ConfigParser()

    _parse_files(parser)
    _validate_config(parser)

    return _extract_config(parser)
