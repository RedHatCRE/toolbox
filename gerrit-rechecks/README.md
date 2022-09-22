# Gerrit Rechecks

## Scripts

### Get the last comment in Gerrit by Data

This tool is used to extract the information in the last comment of a Gerrit revision. We should pass the server where gerrit is hosted, the gerrit change number of the revision, the gerrit username and the path of the SSH key to connect to the given server.

`jq` command is required to parse the JSON reply of the gerrit server.

Usage:

```
$ ./get_gerrit_last_comment_by_data.sh --help
Usage: ./get_gerrit_last_comment_by_data.sh [-u|--ssh_user USERNAME] [-p|--port NUM] [-s|--ssh_key_path PATH] [-H|--gerrit_host HOST] [-U|--gerrit_username USERNAME] [-C|--change_number NUM] [-g|--get-failure-jobs]
```

### Submit Changes to Gerrit Projects with "Depends-On"

This script can be used for submitting changes to multiple projects.

`./detect_submit.sh`

The output of this script is the change-IDs of all the changes submitted

### Reverify Gerrit Changes

This script can be used for submitting a comment to multiple pending changes in gerrit

`./recheck.sh`

This is useful in case you would like to re-trigger the CI for multiple projects with one command invocation.
