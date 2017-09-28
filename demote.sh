#!/usr/bin/env bash

[ -z $1 ] && echo "Must pass datacenter." && exit 3

consul_agent="$1"

echo "Demoting $consul_agent"

set -x

docker-compose exec $consul_agent sh -c "rm /etc/facter/facts.d/pg.yaml"

session_id="$(docker-compose exec $consul_agent curl http://localhost:8500/v1/session/list | jq -r ".[] | .ID")"

for sess in $session_id
do
  docker-compose exec $consul_agent curl -X PUT http://localhost:8500/v1/session/destroy/$sess
done
