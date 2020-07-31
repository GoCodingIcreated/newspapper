#!/bin/bash
DIRNAME=$(dirname $0)

TOKEN=$(cat $DIRNAME/token.txt)

# curl -s https://api.telegram.org/bot$TOKEN/

# My chat id
CHAT_ID=128578085

MESSAGE=$1

if [ -z "$MESSAGE" ]; then
    echo "ERROR: Empty message."
    exit 1
fi
MESSAGE=$(echo "$MESSAGE" | sed 's/"/\\"/g' | sed 's/\./\\\\\./g' | sed 's/\-/\\\\\-/g' | sed 's/!/\\\\!/g' | sed 's/(/\\\\(/g' | sed 's/)/\\\\)/g' | sed 's/\\(\(http.*\)\\)/(\1)/g')

echo "DEBUG: SEND_ALARM: MESSAGE: $MESSAGE"
res=$(curl -s -X POST \
     -H 'Content-Type: application/json' \
     -d "{\"chat_id\": \"$CHAT_ID\", \"text\": \"$MESSAGE\", \"disable_notification\": true, \"parse_mode\": \"MarkdownV2\"}" \
     https://api.telegram.org/bot$TOKEN/sendMessage)
echo "$res"
echo
IS_OK=$(echo "$res" | jq ".ok" | grep "true")
if [ -z "$IS_OK" ]; then
    echo "ERROR: Message was not accepted by telegram."
    exit 1
else
    echo "INFO: Message was accepted by telegram."
    exit 0
fi
