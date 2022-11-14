# Provision

## roles

### docker

`docker` role to automate the installation of the docker service in Fedora and Debian based distributions. It has been tested on Fedora 35 and Ubuntu 22.

```
$ ansible-playbook playbooks/docker/run.yaml -kK
SSH password: 

...
```

### gitlab-runner

`gitlab-runner` role to register a a runner via the GitLab API. We require a token provided by GitLab to perform all the operations of the role.

```
$ ansible-playbook playbooks/gitlab-runner/run.yaml -kK
SSH password: 

...
```

We should modify the `vars/main.yml` file with the right token and URL:

```
$ cat roles/gitlab_runner/vars/main.yml 
---
gitlab_url: "http://gitlab.example.com"
runner_registration_token: "token"
```
