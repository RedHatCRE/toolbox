import pytest
from git import Repo as GitRepo

from cre.interfaces.pygit.client import Repository


@pytest.fixture
def git(mocker, monkeypatch):
    monkeypatch.setattr(GitRepo, 'git', lambda: mocker.Mock())

    return Repository(mocker.Mock())


def test_add(git):
    pattern = '.'

    git.add(pattern)

    git.repo.git.add.assert_called_with(pattern)


def test_checkout(git):
    branch = 'main'

    git.checkout(branch)

    git.repo.git.checkout.assert_called_with(branch)


def test_commit(git):
    message = 'commit_message'

    git.commit(message)

    git.repo.git.commit.assert_called_with('-m', message)


def test_review(git):
    git.review()

    git.repo.git.execute.assert_called_with(['git', 'review'])
