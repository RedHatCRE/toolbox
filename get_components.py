#!/usr/bin/env python
# coding=utf-8

# ===================================
# Get the list of supported component
# ===================================
from bs4 import BeautifulSoup
import logging
import re
import requests


LOG = logging.getLogger(__name__)
PROJECTS_EXCLUDE = ["ip", "work", "test", "ansible", "rox", "ada"]


def setup_logging(debug=False):
    """Sets the logging."""
    format = '%(message)s'
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format=format)


def get_components(soup):
    components = []
    for a in soup.find_all('a', href=True):
        if re.match("^[a-zA-Z]+.*", a['href']):
            components.append(a['href'].rstrip('/'))
    return components


def main():
    setup_logging()
    components_page = requests.get(
        "https://trunk.rdoproject.org/centos8-master/component")
    soup = BeautifulSoup(components_page.content, "html.parser")
    components = get_components(soup)
    LOG.info("\n".join(components))


if __name__ == '__main__':
    main()
