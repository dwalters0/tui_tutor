#!/bin/sh
set -e
#copy the default config into the mounted directory
if [ ! -f /opt/app/config/configuration.yaml ]; then
  cp /opt/app/Defaults/configuration.yaml /opt/app/config/configuration.yaml
fi

#copy the default InputUnit into the mounted directory
if [ ! -f /opt/app/InputUnits/AIFundamentals.yaml ]; then
  cp /opt/app/Defaults/AIFundamentals.yaml /opt/app/InputUnits/
fi

#start the ssh server
exec /usr/sbin/sshd -D -e