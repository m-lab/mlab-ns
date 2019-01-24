#!/bin/bash
#
# cron.sh creates the cron jobs needed for the annotation service, using the
# Cloud Schedule API to create app engine cron jobs.

set -ex
PROJECT=${1:?Please provide project}
BASEDIR="$(dirname "$0")"

# Add gcloud to PATH.
source "${HOME}/google-cloud-sdk/path.bash.inc"
source $( dirname "${BASH_SOURCE[0]}" )/travis/gcloudlib.sh

# Authenticate all operations using the given service account.
activate_service_account SERVICE_ACCOUNT_${PROJECT/-/_}

gcloud version
echo $PATH
which gcloud
export PATH=$HOME/google-cloud-sdk/bin:$PATH

gcloud version
echo $PATH
which gcloud

# check for site status, run every minute.
"${BASEDIR}"/travis/schedule_appengine_job.sh "${PROJECT}" check_status \
    --description="Check sliver tools status" \
    --relative-url="/cron/check_status" \
    --schedule="every 1 minutes" \
    --http-method="GET" \
    --service="locate"

# check for new sites, and for new and/or updated IP addresses, roundrobin information.
# run every 24 hours, starting at 06:00
"${BASEDIR}"/travis/schedule_appengine_job.sh "${PROJECT}" check_site \
    --description="Check sites, update IP and roundrobin" \
    --relative-url="/cron/check_site" \
    --schedule="every day 06:00" \
    --http-method="GET" \
    --service="locate"

# Update blacklist of client signature list for abusive clients.
"${BASEDIR}"/travis/schedule_appengine_job.sh "${PROJECT}" update_requests \
    --description="Check client blacklists for abusive clients" \
    --relative-url="/cron/update_requests" \
    --schedule="every 5 minutes" \
    --http-method="GET" \
    --service="locate"

# Report all currently scheduled jobs.
gcloud --project "${PROJECT}" beta scheduler jobs list 2> /dev/null
