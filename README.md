# cre

Code Reliability Engineering Toolbox

## Get the last comment in Gerrit by ID

This tool is used to extract the information in the last comment of a Gerrit revision. We should pass the server where gerrit is hosted, the ID number of the revision and the path of the SSH key to connect to the given server.

`jq` command is required to parse the JSON reply of the gerrit server.

Usage:

```
$ ./get_gerrit_last_comment_by_id.sh -h
Usage: ./get_gerrit_last_comment_by_id.sh [-u|--gerrit_server] [-p|--port] [-i|--id] [-s|--ssh_key_path]
```
