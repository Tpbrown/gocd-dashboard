#!/bin/sh
# This script gathers Agent health metrics

# Defaults
GO_SERVER=${GO_SERVER:-build.go.cd}
GO_USER=${GO_USER:-view}
GO_PASSWORD=${GO_PASSWORD:-password}
JSON_REQUEST="-H 'Accept: application/vnd.go.cd.v2+json'"

# if [[ -f '/bin/busybox' ]]; then
#   # Likely running in Alpine.  Adjust flags and ensure curl is installed.
#   BASE64_OPTS=''
#   # apk --no-cache add curl
# else
#   # Default flags for OSX.  Hope it works on Linux too ;-)
#   BASE64_OPTS="--input='-' --output='-'"
# fi


# BASE64=`echo $GO_USER:$GO_PASSWORD|base64 ${BASE64_OPTS}`
# BASIC_AUTH_HEADER="Authorization: Basic ${BASE64}"

TMPFILE=`mktemp`
STATES=`mktemp`
curl -o $TMPFILE -s "https://${GO_SERVER}/go/api/agents" -u "${GO_USER}:${GO_PASSWORD}" "${JSON_REQUEST}"
grep agent_state $TMPFILE|awk '{print $2}'|tr -d \"\, >$STATES
TOTAL_AGENTS=`wc -l $STATES|awk '{print $1}'`
STATE_IDLE=`grep Idle $STATES|wc -l|awk '{print $1}'`
STATE_BUILDING=`grep Building $STATES|wc -l|awk '{print $1}'`
STATE_LOST_CONTACT=`grep LostContact $STATES|wc -l|awk '{print $1}'`
STATE_MISSING=`grep Missing $STATES|wc -l|awk '{print $1}'`
STATE_UNKNOWN=`grep Unknown $STATES|wc -l|awk '{print $1}'`

rm $TMPFILE
rm $STATES

# Format is category,tag1,tag2 field=value,field2=value
echo "agents,host=${GO_SERVER} total=${TOTAL_AGENTS},idle=${STATE_IDLE},building=${STATE_BUILDING},lost=${STATE_LOST_CONTACT},missing=${STATE_MISSING},unknown=${STATE_UNKNOWN}"
