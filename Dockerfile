FROM consul:0.7.5

RUN apk add --no-cache --virtual .fetch-deps python py-pip

COPY requirements.txt /

RUN mkdir -p /etc/facter/facts.d

RUN pip install -r /requirements.txt
