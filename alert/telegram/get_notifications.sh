#!/bin/bash

DIRNAME=$(dirname $0)

TOKEN_FILE=$DIRNAME/token.txt
TOKEN=$(cat $TOKEN_FILE)


# get chat id
curl -s https://api.telegram.org/bot$TOKEN/getUpdates | jq '.result[].message.chat.id'