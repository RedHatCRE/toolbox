from git import Repo as GitRepo


class Repository:
    def __init__(self, repo: GitRepo) -> None:
        self.repo = repo

    def add(self, pattern: str) -> None:
        self.repo.git.add(pattern)

    def checkout(self, branch: str) -> None:
        self.repo.git.checkout(branch)

    def commit(self, message: str) -> None:
        self.repo.git.commit('-m', message)

    def review(self) -> None:
        self.repo.git.execute(['git', 'review'])


def clone(url: str, working_dir: str) -> Repository:
    return Repository(
        GitRepo.clone_from(url, working_dir)
    )
