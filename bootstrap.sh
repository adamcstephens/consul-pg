#!/usr/bin/env bash

CONSUL_HOST="127.0.0.1"

echo "Adding query to dc1"
curl --request POST --data @prepared-query.json --silent http://$CONSUL_HOST:8500/v1/query
echo
echo "Adding query to dc2"
curl --request POST --data @prepared-query.json --silent http://$CONSUL_HOST:18500/v1/query
echo

curl --request GET --silent http://$CONSUL_HOST:8500/v1/query | jq
curl --request GET --silent http://$CONSUL_HOST:18500/v1/query | jq


./promote.sh dc1agent1
