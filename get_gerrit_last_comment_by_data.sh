#!/usr/bin/env bash

if ! type jq >/dev/null 2>&1; then
    echo >&2 "I require jq but it's not installed. Aborting."
    exit 1
fi

usage() { 
    echo "Usage: $0 [-u|--ssh_user USERNAME] [-p|--port NUM] [-s|--ssh_key_path PATH] [-H|--gerrit_host HOST] [-U|--gerrit_username USERNAME] [-C|--change_number NUM] [-g|--get-failure-jobs]"
    exit 2
}

declare gerrit_host port change_number ssh_key_path gerrit_username review_data get_failure_jobs

while [ $# -gt 0 ]; do
    case $1 in
        -H|--gerrit_host)
            gerrit_host=$2
            shift
            ;;
        -U|--gerrit_username)
            gerrit_username=$2
            shift
            ;;
        -C|--change_number) 
            change_number=$2
            shift
            ;;
        -p|--port) 
            port=$2
            shift
            ;;
        -u|--ssh_user)
            ssh_user=$2
            shift
            ;;
        -s|--ssh_key_path)
            ssh_key_path=$2
            shift
            ;;
        -g|--get_failure_jobs)
            get_failure_jobs=true
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

if [ -z "$ssh_user" ]; then
    echo 'Missing -u parameter: --ssh_user'
    exit 2
fi

if [[ -z $port ]]; then
    port=22
fi

if [ -z "$gerrit_host" ]; then
    echo 'Missing -H parameter: --gerrit_host'
    exit 2
fi

if [ -z "$gerrit_username" ]; then
    echo 'Missing -U parameter: --gerrit_username'
    exit 2
fi

if [ -z "$change_number" ]; then
    echo 'Missing -C parameter: --change_number'
    exit 2
fi

ssh_command=("ssh" "-p" "$port" "$ssh_user@$gerrit_host")
gerrit_command=( "gerrit" "query" "--comments" "change:$change_number" "--format=json" "commentby:$gerrit_username" "--format=JSON")

if [ ! -z "$ssh_key_path" ]; then
    if [ ! -f "$ssh_key_path" ]; then
        echo "SSH key '$ssh_key_path' not found"
        exit 2
    fi
    ssh_command+=('-i' $ssh_key_path)
fi

review_data=$("${ssh_command[@]}" "${gerrit_command[@]}")

if jq -e 'select(.type=="error")' <<< "${review_data[@]}"
then
    echo "An error has been returned by Gerrit"
    exit 1
fi

if jq -e 'select(.rowCount==0)' <<< "${review_data[@]}"
then
    echo "There is no data found in the review"
    exit 1
fi

comment_rows=$(head -n1 <<< "${review_data[@]}")

last_comment_review_info=$(jq -r --raw-output --exit-status "
                                                            [.project,
                                                            [[.comments | .[] | select(.reviewer.username==\"$gerrit_username\")] | last | .message]
                                                            ]" <<< "$comment_rows")

project_name=$(jq -r first <<< "$last_comment_review_info")

last_comment=$(jq -r 'last | .[]' <<< "$last_comment_review_info" \
                      | awk '/^-/{print $2,$3,$5}')

jq_extract_jobs_data_command=("jq" "-c" ".[]")
if [ ! -z "$get_failure_jobs" ]; then
    jq_extract_jobs_data_command=("jq" "-r" "'[.data | .[] | select(.status==\"FAILURE\")]'")
fi

data=$(echo "$last_comment" | column --table --table-columns TEST_NAME,URL,STATUS --json --table-name data | eval "${jq_extract_jobs_data_command[@]}") 

jq -n --arg project_name "$project_name"  \
      --arg change_id "$change_number"    \
      --argjson data "$data"              \
      '{project_name: $project_name, change_id: $change_id, data: $data}'

