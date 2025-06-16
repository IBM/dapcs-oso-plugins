#!/bin/bash
#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#
#

# entrypoint for nginx
touch /tmp/certs.pem
echo 'Starting envsubst'
# shellcheck disable=SC2016,SC2154
# HOSTNAME="https://dapcs.ibm.com" COMPONENT_DN="$joined" envsubst '\$PORT \$HOSTNAME' </app-root/nginx.conf.template >/app-root/nginx.conf
echo 'Starting nginx'
nginx -c /app-root/deploy/nginx.conf -g 'daemon off;' &
# Wait for the Nginx process to finish
NGINX_PID=$!
wait $NGINX_PID

# Exit with the same exit code as the Nginx process
exit $?
