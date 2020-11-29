#!/bin/bash

DIRNAME=$(dirname $0)

notify_file=$DIRNAME/../../logs/newspapper_bot.service.notifed

if [ -z "$(systemctl status newspapper_bot.service  | grep "active (running)")" ]; then
    if [ ! -f $notify_file ]; then
        $DIRNAME/send_alarm.sh "NewspapperBot service is not running"
        touch $notify_file
    fi
else
	if [ -f $notify_file ]; then
        $DIRNAME/send_alarm.sh "NewspapperBot service is running"
        rm -f $notify_file
    fi
fi

