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

curl -X POST \
     -H 'Content-Type: application/json' \
     -d "{\"chat_id\": \"$CHAT_ID\", \"text\": \"My message: $MESSAGE\", \"disable_notification\": true}" \
     https://api.telegram.org/bot$TOKEN/sendMessage && echo