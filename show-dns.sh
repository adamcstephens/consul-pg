#!/usr/bin/env bash

set -x

CONSUL_HOST="127.0.0.1"

dig +short pgcluster.service.dc1.consul @$CONSUL_HOST -p 8600

dig +short pgcluster.service.dc2.consul @$CONSUL_HOST -p 8600

echo
dig +short pg-pgcluster-master.query.dc1.consul @$CONSUL_HOST -p 8600

dig +short pg-pgcluster-master.query.dc2.consul @$CONSUL_HOST -p 8600

echo
dig +short pg-pgcluster-slave.query.dc1.consul @$CONSUL_HOST -p 8600

dig +short pg-pgcluster-slave.query.dc2.consul @$CONSUL_HOST -p 8600
