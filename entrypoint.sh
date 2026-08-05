#!/bin/sh
set -e
#copy the default config into the mounted directory
if [ ! -f /Users/dan/development/Python/tui_tutor/Curricula/config/configuration.yaml ]; then
  cp /Users/dan/development/Python/tui_tutor/Curricula/Defaults/configuration.yaml /Users/dan/development/Python/tui_tutor/Curricula/config/configuration.yaml
fi

#copy the default InputUnit into the mounted directory
if [ ! -f /Users/dan/development/Python/tui_tutor/Curricula/InputUnits/AIFundamentals.yaml ]; then
  cp /Users/dan/development/Python/tui_tutor/Curricula/Defaults/AIFundamentals.yaml /Users/dan/development/Python/tui_tutor/Curricula/InputUnits/
fi

#start the ssh server
exec /usr/sbin/sshd -D -e