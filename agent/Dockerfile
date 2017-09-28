FROM consul:0.7.5

RUN apk add --no-cache --virtual .fetch-deps python py-pip

COPY requirements.txt /
RUN pip install -r /requirements.txt

RUN mkdir -p /etc/facter/facts.d
COPY service_pg.json /consul/config/
COPY consul_check_postgres.py /usr/local/bin/
