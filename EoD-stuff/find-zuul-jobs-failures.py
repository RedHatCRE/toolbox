#!/usr/bin/env python3
#
# I need your love
# I need your time
# When everything's wrong
# You make it... visible in a spreadsheet!
#
from dataclasses import dataclass
from datetime import datetime
import html
import os
from string import Template
import textwrap
from zipfile import ZipFile

import requests


API_URL = input('API URL: ')
API_TENANT = input('Tenant: ')

BRANCHES = [
    'rhos-17.0-trunk-patches',
    'rhos-17.1-trunk-patches',
]

JOBS = [
    'osp-rpm-py39',
    'osp-tox-pep8',
]

PIPELINES = [
    'weekly',
]

api_base = os.path.join(API_URL, 'tenant', API_TENANT)
builds_endpoint = os.path.join(api_base, 'builds')
projects_endpoint = os.path.join(api_base, 'projects')


@dataclass
class Build:
    project: str
    branch: str
    pipeline: str
    job: str
    date: str
    uuid: str
    result: str
    log_url: str
    voting: str
    logs: str = ''


def progress(current: int = 0, total: int = 100):
    length = 40
    boxes = int(current / total * length) * '#'
    togo = (length - len(boxes)) * '-'

    print(f'\r[{boxes}{togo}] {current}/{total}', end='')

    if current >= total:
        print()


def get_projects() -> list:
    resp = requests.get(projects_endpoint)
    projects = [project.get('name') for project in resp.json()]

    return projects


def get_last_build(project=None, branch=None, pipeline=None, job=None) -> dict:
    params = {'limit': 1}

    if project:
        params['project'] = project
    if branch:
        params['branch'] = branch
    if job:
        params['job_name'] = job
    if pipeline:
        params['pipeline'] = pipeline

    resp = requests.get(builds_endpoint, params=params)
    try:
        return resp.json().pop()
    except IndexError:
        return {}


def get_builds() -> list:
    builds = []
    projects = get_projects()

    i = 0
    end = len(BRANCHES) * len(JOBS) * len(PIPELINES) * len(projects)
    progress(i, end)

    for project in projects:
        for branch in BRANCHES:
            for pipeline in PIPELINES:
                for job in JOBS:
                    build = get_last_build(project, branch, pipeline, job)
                    date = build.get('start_time', '')

                    if date and (datetime.now()
                                 - datetime.fromisoformat(date)).days > 14:
                        build['result'] = '---'
                        build['log_url'] = ''

                    builds.append(Build(
                        project=project,
                        branch=branch,
                        pipeline=pipeline,
                        job=job,
                        date=build.get('start_time', ''),
                        uuid=build.get('uuid', ''),
                        result=build.get('result', '---'),
                        log_url=build.get('log_url', ''),
                        voting=build.get('voting', True),
                    ))

                    i += 1
                    progress(i, end)

    return builds


def truncate(text: str, N: int = 100):
    if len(text) > N:
        return '...\n' + text[-N:]
    else:
        return text


def produce_task_output(status):
    output = []

    # General
    if status.get('action'):
        output.append(f'ACTION: {status.get("action")}')
    if status.get('item'):
        output.append(f'ITEM: {status.get("item")}')
    if status.get('msg'):
        output.append(f'MSG: {status.get("msg")}')

    # For Ansible loop
    if status.get('results'):
        for result in status.get('results'):
            if result.get('failed'):
                output.append(produce_task_output(result))

    # For: get_url
    if status.get('url'):
        output.append(f'URL: {status.get("url")}')
    if status.get('response'):
        output.append(f'RESPONSE: {status.get("resposne")}')

    # For: command, shell
    if status.get('cmd'):
        output.append(f'CMD: {status.get("cmd")}')
    if status.get('stderr'):
        output.append('STDERR:')
        output.append(truncate(status.get("stderr"), 1024))
    if status.get('stdout'):
        output.append('STDOUT:')
        output.append(truncate(status.get("stdout"), 1024))

    # For: package
    if status.get('failures'):
        output.append('FAILURES:')
        output.append('\n'.join(status.get('failures')))

    return '\n'.join(output)


def find_failure_reason(url: str):
    resp = requests.get(url)
    if not resp.ok:
        return f'LOGS NOT FOUND [{resp.status_code}]'

    # Structure of job-output.json:
    # on top there is a list of playbooks dicts,
    # each playbook dict contains list of plays dicts,
    # each play dict contains list of tasks dicts,
    # each task dict contain host details to check for failures.
    playbooks = resp.json()
    for playbook in playbooks:
        for play in playbook.get('plays'):
            for task in play.get('tasks'):
                for status in task.get('hosts').values():
                    if status.get('failed'):
                        return produce_task_output(status)

    return 'REASON NOT FOUND'


def get_bad_results(builds: list[Build]) -> dict:
    builds = [build for build in builds
              if (build.result not in ('SUCCESS', '---')
                  and build.log_url != '')]
    results = []

    i = 0
    end = len(builds)
    progress(i, end)

    for build in builds:
        build.logs = find_failure_reason(f'{build.log_url}/job-output.json')

        results.append((
            build.project,
            build.branch,
            build.job,
            build.date,
            build.result,
            build.log_url,
            build.logs,
        ),)

        i += 1
        progress(i, end)

    print('Number of failed builds:', len(results))

    return results


def write_spreadsheet_file(path: str, content: list[list[str]]):
    # This function generates minimal working OpenDocument Spreadsheet,
    # containing only content.xml, mimetype and META-INF/manifest.xml files.
    # Typical ODS file contain also meta.xml, settings.xml and styles.xml,
    # but they appear not necessary, at least for LibreOffice.

    def remove_control_characters(text: str):
        # Not every UTF-8 character is accepted in XML file
        # Details: https://www.w3.org/TR/REC-xml/#charsets
        mapping = dict.fromkeys(range(32))
        del mapping[9]  # allow \t
        del mapping[10]  # allow \n
        del mapping[13]  # allow \r
        return text.translate(mapping)

    def make_cell(content: str):
        if not content:
            return '<table:table-cell />'
        output = '<table:table-cell>'
        output += f'<text:p>{html.escape(content)}</text:p>'
        output += '</table:table-cell>'
        return output

    def make_row(content: list[str]):
        if not content:
            return '<table:table-row />'
        output = '<table:table-row>'
        for cell in content:
            output += make_cell(cell)
        output += '</table:table-row>'
        return output

    def make_table(content: list[list[str]], name: str = 'Sheet1'):
        if not content:
            return f'<table:table table:name="{name}" />'
        output = f'<table:table table:name="{name}">'
        for row in content:
            output += make_row(row)
        output += '</table:table>'
        return output

    manifest_content = textwrap.dedent('''
        <?xml version="1.0" encoding="UTF-8" ?>
        <manifest:manifest
         xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"
         manifest:version="1.3">
            <manifest:file-entry
             manifest:full-path="/"
             manifest:version="1.3"
             manifest:media-type="application/vnd.oasis.opendocument.spreadsheet" />
            <manifest:file-entry
             manifest:full-path="content.xml"
             manifest:media-type="text/xml" />
        </manifest:manifest>
        '''.strip())  # noqa E501

    mimetype_content = 'application/vnd.oasis.opendocument.spreadsheet'

    spreadsheet_content_template = Template(textwrap.dedent('''
        <?xml version="1.0" encoding="UTF-8" ?>
        <office:document-content
         xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
         xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
         xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
         office:version="1.3">
            <office:body>
                <office:spreadsheet>
                    $table
                </office:spreadsheet>
            </office:body>
        </office:document-content>
        '''.strip()))

    spreadsheet_content = spreadsheet_content_template.substitute(
        table=remove_control_characters(make_table(content))
    )

    with ZipFile(path, 'w') as zipf:
        zipf.writestr('mimetype', mimetype_content)
        zipf.writestr('content.xml', spreadsheet_content)
        zipf.writestr('META-INF/manifest.xml', manifest_content)


def main() -> None:
    print('Fetching latest builds...')
    builds = get_builds()
    print('Fetching failures details...')
    results = get_bad_results(builds)
    print('Saving results...')
    filename = f'zuul-failures-{str(datetime.now()).replace(" ", "-")}.ods'
    write_spreadsheet_file(filename, results)
    print('DONE')


if __name__ == '__main__':
    main()
