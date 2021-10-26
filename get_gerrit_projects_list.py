#!/usr/bin/env python
# coding=utf-8

# Get projects from Gerrit based on packages names in the repositories
import argparse
from bs4 import BeautifulSoup
import json
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


def create_argparse_instance():
    parser = argparse.ArgumentParser()
    parser.add_argument('--component', '-c', dest="component",
                        required=False,
                        help="component name")
    parser.add_argument('--gerrit', '-g', dest="gerrit",
                        required=True,
                        help="gerrit endpoint URL (https://.../gerrit)")
    return parser.parse_args()


def get_components(soup):
    components = []
    for a in soup.find_all('a', href=True):
        if re.match("^[a-zA-Z]+.*", a['href']):
            components.append(a['href'].rstrip('/'))
    return components


def print_components_menu(components):
    for i, comp in enumerate(components):
        print("[{}] {}".format(i, comp))


def get_component_input(components):
    comp = ""
    while not comp:
        comp = input("Which component to use? Specify number: ")
        if not comp.isdigit() or int(comp) > len(components) - 1:
            print("Invalid number! Try again...")
            comp = ""
    return components[int(comp)]


def get_packages(component_packages_url):
    packages = []
    packages_page = requests.get(component_packages_url)
    soup = BeautifulSoup(packages_page.content, "html.parser")
    for a in soup.find_all('a', href=True):
        names = re.findall(r'(\w+(?:-\w+)*)\-', a['href'])
        if names:
            packages.append(names[0])
    return packages


def load_gerrit_projects(response):
    magic_json_prefix = ")]}'\n"
    content = response.content.strip()
    content = content[len(magic_json_prefix):]
    return json.loads(content)


def compare_packages_to_gerrit_projects(gerrit_url, packages):
    projects = []
    LOG.info("Obtaining projects from Gerrit...")
    projects_response = requests.get(gerrit_url + "/projects/?all")
    gerrit_projects_json = load_gerrit_projects(projects_response)
    for project in gerrit_projects_json.keys():
        for package in packages:
            if project in package and project not in PROJECTS_EXCLUDE:
                projects.append(project)
    return set(projects)


def main():
    setup_logging()
    args = create_argparse_instance()
    if not args.component:
        components_page = requests.get(
            "https://trunk.rdoproject.org/centos8-master/component")
        soup = BeautifulSoup(components_page.content, "html.parser")
        components = get_components(soup)
        print_components_menu(components)
        component = get_component_input(components)
    else:
        component = args.component
    component_packages_url = "https://trunk.rdoproject.org/\
centos8-master/component/{}/current".format(component)
    LOG.info("Getting list of packages...")
    packages = get_packages(component_packages_url)
    LOG.info("Obtained list of packages")
    projects = compare_packages_to_gerrit_projects(
        gerrit_url=args.gerrit, packages=packages)
    if projects:
        LOG.info("Found the following projects in Gerrit:\n{}".format(
            "\n".join(projects)))
    else:
        LOG.info("No relevant projects have been found...")


if __name__ == '__main__':
    main()
