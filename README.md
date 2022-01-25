# cre

Code Reliability Engineering Toolbox

## Get the last comment in Gerrit by Data

This tool is used to extract the information in the last comment of a Gerrit revision. We should pass the server where gerrit is hosted, the gerrit change number of the revision, the gerrit username and the path of the SSH key to connect to the given server.

`jq` command is required to parse the JSON reply of the gerrit server.

Usage:

```
$ ./get_gerrit_last_comment_by_data.sh --help
Usage: ./get_gerrit_last_comment_by_data.sh [-u|--ssh_user USERNAME] [-p|--port NUM] [-s|--ssh_key_path PATH] [-H|--gerrit_host HOST] [-U|--gerrit_username USERNAME] [-C|--change_number NUM] [-g|--get-failure-jobs]
```

