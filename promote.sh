#!/usr/bin/env bash

[ -z $1 ] && echo "Must pass docker-compose service name."

echo "Promoting $1"
docker-compose exec $1 sh -c "echo \"pg_role: 'master'\" > /etc/facter/facts.d/pg.yaml"
