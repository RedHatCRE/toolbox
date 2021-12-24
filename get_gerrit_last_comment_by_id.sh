#!/usr/bin/env bash

if ! command -v jq >/dev/null 2>&1; then
    echo >&2 "I require jq but it's not installed. Aborting."
    exit 1
fi

usage() { 
    echo "Usage: $0 [-u|--gerrit_server HOST] [-p|--port NUM] [-i|--id NUM] [-s|--ssh_key_path PATH]"
    exit 2
}

declare gerrit_server port id ssh_key_path

while [ $# -gt 0 ]; do
    case $1 in
        -g|--gerrit_server)
            gerrit_server=$2
            shift
            ;;
        -p|--port) 
            port=${2:-22}
            shift
            ;;
        -i|--id) 
            id=$2
            shift
            ;;
        -s|--ssh_key_path)
            ssh_key_path=$2
            shift
            ;;
        --)
            shift
            break
            ;;
        *)
            usage
    esac
    shift
done

if [[ -z $port ]]; then
    port=22
fi

if [ -z "$gerrit_server" ]; then
    echo 'Missing -g parameter: --gerrit_server'
    exit 2
fi

if [ -z "$id" ]; then
    echo 'Missing -i parameter: --id'
    exit 2
fi

if [ -z "$ssh_key_path" ]; then
    echo 'Missing -s parameter: --ssh_key_path'
    exit 2
fi


review_data=$(ssh -p "$port" "$gerrit_server" gerrit query --comments --current-patch-set "$id" --format=json)
# We should slurp the output with `jq`. The query comments always return 2 json without division if the review exist. If it doesn't then it returns one json always.
jq --raw-output --exit-status --slurp '
                                      .[0].comments 
                                      | last 
                                      | .message // "This review does not have comments"' <<< "$review_data"
