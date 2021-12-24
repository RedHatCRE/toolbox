#!/usr/bin/env bash

if ! command -v jq >/dev/null 2>&1; then
    echo >&2 "I require jq but it's not installed. Aborting."
    exit 1
fi

usage() { 
    echo "Usage: $0 [-h|--gerrit_host HOST] [-p|--port NUM] [-c|--change_number NUM] [-s|--ssh_key_path PATH] [-u|--gerrit_username USERNAME]"
    exit 2
}

declare gerrit_host port change_number ssh_key_path gerrit_username

while [ $# -gt 0 ]; do
    case $1 in
        -h|--gerrit_host)
            gerrit_host=$2
            shift
            ;;
        -p|--port) 
            port=$2
            shift
            ;;
        -c|--change_number) 
            change_number=$2
            shift
            ;;
        -s|--ssh_key_path)
            ssh_key_path=$2
            shift
            ;;
        -u|--gerrit_username)
            gerrit_username=$2
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

if [ -z "$gerrit_host" ]; then
    echo 'Missing -h parameter: --gerrit_host'
    exit 2
fi

if [ -z "$change_number" ]; then
    echo 'Missing -c parameter: --change_number'
    exit 2
fi

if [ -z "$ssh_key_path" ]; then
    echo 'Missing -s parameter: --ssh_key_path'
    exit 2
fi

if [ -z "$ssh_key_path" ]; then
    echo 'Missing -u parameter: --gerrit_username'
    exit 2
fi

review_data=$(ssh -p "$port" "$gerrit_host" gerrit query --comments --current-patch-set change:"$change_number" --format=json commentby:"$gerrit_username" --format=JSON)

# Gerrit returns error
if jq -e 'select(.type=="error")' <<< "$review_data"
then
    exit 1
fi

# There is no data
if jq -e 'select(.rowCount==0)' <<< "$review_data"
then
    exit 1
fi

jq -r --raw-output --exit-status "
                                 [.comments 
                                 | .[] 
                                 | select(.reviewer.username==\"$gerrit_username\")] 
                                 | last.message" <<< "$review_data"
