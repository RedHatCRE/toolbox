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

    def hash_object(self, file: str) -> str:
        return self.repo.git.execute(['git', 'hash-object', file])

    def review(self) -> None:
        self.repo.git.execute(['git', 'review'])

    def get_remote_url(self, remote: str = 'origin') -> str:
        return next(self.repo.remote(remote).urls)

    def get_working_dir(self) -> str:
        return self.repo.working_dir


def clone(url: str, working_dir: str) -> Repository:
    return Repository(
        GitRepo.clone_from(url, working_dir)
    )
