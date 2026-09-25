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

# Keep both SSH and the web application running, and restart either one if it
# exits unexpectedly.
exec /usr/bin/supervisord -c /opt/app/supervisord.conf
