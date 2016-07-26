#!/bin/sh

# This script gathers Job queue depth (e.g. - Jobs scheduled but not yet running)

# Defaults
GO_SERVER=${GO_SERVER:-build.go.cd}
GO_USER=${GO_USER:-view}
GO_PASSWORD=${GO_PASSWORD:-password}
# JSON_REQUEST=''

# if [[ -f '/bin/busybox' ]]; then
#   # Likely running in Alpine.  Adjust flags and ensure curl is installed.
#   BASE64_OPTS=''
#   # apk --no-cache add curl
# else
#   # Default flags for OSX.  Hope it works on Linux too ;-)
#   BASE64_OPTS="--input='-' --output='-'"
# fi
#
#
# BASE64=`echo $GO_USER:$GO_PASSWORD|base64 ${BASE64_OPTS}`
# BASIC_AUTH_HEADER="Authorization: Basic ${BASE64}"

DEPTH=`curl -s "https://${GO_SERVER}/go/api/jobs/scheduled.xml" -u "${GO_USER}:${GO_PASSWORD}"|grep "job name"|wc -l|awk '{print $1}'`

# Format is category,tag1,tag2 field=value,field2=value
echo "jobs,host=${GO_SERVER} scheduled_jobs=${DEPTH}"
