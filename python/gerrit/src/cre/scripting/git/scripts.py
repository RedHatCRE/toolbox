import os
import shutil
from urllib.parse import urlparse

from cre.interfaces.pygit.client import Repository
from cre.interfaces.pygit.client import clone
from cre.scripting import files


def _get_projects_base_path() -> str:
    return os.path.join(os.getcwd(), 'projects')


def _get_project_path(project: str) -> str:
    return os.path.join(_get_projects_base_path(), project)


def _get_project_url(
    host: str,
    project: str,
    user: str = None,
    password: str = None
) -> str:
    result = r'https://'

    if user:
        result += user

        if password:
            result += ':%s' % password

        result += '@'

    result += '%s/gerrit/%s' % (host, project)

    return result


def _create_file_on_repo(
    repo: Repository,
    name: str = 'foo',
    size: int = 40
) -> str:
    file = os.path.join(repo.get_working_dir(), name)
    files.touch(file, size)

    return file


def _generate_commit_message_from_file(repo: Repository, file: str) -> str:
    def get_repo_host() -> str:
        return urlparse(repo.get_remote_url()).hostname

    def get_change_id() -> str:
        return 'I%s' % repo.hash_object(file)

    return (
        'DNM [CRE] [OSPCRE-62] -'
        ' Downstream component jobs\n'
        '\n'
        'This change is going to be abandoned'
        ' after the zuul job verification.\n'
        '\n'
        'Depends-On:'
        ' https://{host}/gerrit/c/openstack/osp-internal-jobs/+/303197\n'
        '\n'
        'Change-Id: {change_id}'
    ).format(
        host=get_repo_host(),
        change_id=get_change_id()
    )


def _prepare_project_for_clone(project: str) -> None:
    def create_project_dir() -> None:
        projects_path = _get_projects_base_path()

        if not os.path.exists(projects_path):
            os.mkdir(projects_path)

    def clean_project_dir() -> None:
        project_path = _get_project_path(project)

        if os.path.exists(project_path):
            shutil.rmtree(project_path)

    create_project_dir()
    clean_project_dir()


def create_and_review_change_for(
    host: str,
    project: str,
    branch: str,
    user: str = None,
    password: str = None
) -> None:
    _prepare_project_for_clone(project)

    repo = clone(
        _get_project_url(host, project, user, password),
        _get_project_path(project)
    )

    repo.checkout(branch)

    file = _create_file_on_repo(repo)

    repo.add(file)
    repo.commit(_generate_commit_message_from_file(repo, file))

    repo.review()
