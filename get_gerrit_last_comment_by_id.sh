#!/usr/bin/env bash

command -v jq >/dev/null 2>&1 || { echo >&2 "I require jq but it's not installed. Aborting."; exit 1; }

usage() { 
    echo "Usage: $0 [-u|--gerrit_server] [-p|--port] [-i|--id] [-s|--ssh_key_path]"; 
    exit 2;
}

declare gerrit_server port id ssh_key_path

while [ $# -gt 0 ]; do
    case $1 in
        -g|--gerrit_server)
            gerrit_server=$2;
            shift
            ;;
        -p|--port) 
            [[ -z $2 ]] && port=22 || port=$2;
            shift
            ;;
        -i|--id) 
            id=$2;
            shift
            ;;
        -s|--ssh_key_path)
            ssh_key_path=$2;
            shift
            ;;
        --)
            shift;
            break;;
        *)
            usage
    esac
    shift
done

if [[ -z $port ]]; then
    port=22
fi

if [ -z "$gerrit_server" ]; then
    { echo 'Missing -g parameter: --gerrit_server'; exit 2; }
fi

if [ -z "$id" ]; then
    { echo 'Missing -i parameter: --id'; exit 2; }
fi

if [ -z "$ssh_key_path" ]; then
    { echo 'Missing -s parameter: --ssh_key_path' ; exit 2; }
fi

# We should slurp the output with `jq`. The query comments always return 2 json without division
ssh -p "$port" "$gerrit_server" gerrit query --comments --current-patch-set "$id" --format=JSON \ | 
    jq --raw-output --exit-status --slurp '
    .[0].comments 
    | last 
    | .message'

if [ $? -ne 0 ]; then
     { echo "Error retrieving data from gerrit."; exit $?; }
fi