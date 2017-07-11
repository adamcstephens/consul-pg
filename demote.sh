#!/usr/bin/env bash

[ -z $1 ] && echo "Must pass datacenter."

echo "Demoting $1"
docker-compose exec $1 sh -c "rm /etc/facter/facts.d/pg.yaml"
