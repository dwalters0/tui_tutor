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

#make the html directory if it doesn't exist
if [ ! -d /opt/app/html ]; then
  mkdir /opt/app/html
fi

#host the html folder in the background
#python3 -m http.server 8082 -d /opt/app/html &

#start the ssh server
exec /usr/sbin/sshd -D -e