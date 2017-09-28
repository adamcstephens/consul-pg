#!/usr/bin/env bash

set -x

curl -s http://localhost:8500/v1/catalog/service/pgcluster | jq '.[] | {Node, ServiceName, ServiceTags}'
curl -s http://localhost:18500/v1/catalog/service/pgcluster | jq '.[] | {Node, ServiceName, ServiceTags}'
