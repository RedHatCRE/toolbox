# cre

Code Reliability Engineering Toolbox

## Get the last comment in Gerrit by Data

This tool is used to extract the information in the last comment of a Gerrit revision. We should pass the server where gerrit is hosted, the gerrit change number of the revision, the gerrit username and the path of the SSH key to connect to the given server.

`jq` command is required to parse the JSON reply of the gerrit server.

Usage:

```
$ ./get_gerrit_last_comment_by_data.sh --help
Usage: ./get_gerrit_last_comment_by_data.sh [-H|--gerrit_host HOST] [-p|--port NUM] [-c|--change_number NUM] [-s|--ssh_key_path PATH] [-u|--gerrit_username USERNAME]
```


