#!/usr/bin/env bash

CONSUL_HOST="$(docker-machine ip)"

echo ":: dc1 pg service"
dig +short pgcluster.service.dc1.consul @$CONSUL_HOST -p 8600

echo
echo ":: dc2 pg service"
dig +short pgcluster.service.dc2.consul @$CONSUL_HOST -p 8600

echo
echo ":: dc1 pg master query"
dig +short pg-pgcluster-master.query.dc1.consul @$CONSUL_HOST -p 8600

echo
echo ":: dc2 pg master query"
dig +short pg-pgcluster-master.query.dc2.consul @$CONSUL_HOST -p 8600

echo
echo ":: dc1 pg slave query"
dig +short pg-pgcluster-slave.query.dc1.consul @$CONSUL_HOST -p 8600

echo
echo ":: dc2 pg slave query"
dig +short pg-pgcluster-slave.query.dc2.consul @$CONSUL_HOST -p 8600
