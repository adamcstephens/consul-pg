#!/usr/bin/env python
#
# read rempgr and consul service and update tags accordingly

from socket import gethostname
from sys import exit
from traceback import print_exc
import argparse
import json
import yaml
import requests


class ConsulPostgreSQL:

    DEFAULT_CONFIGFILE = '/etc/default/consul_check_postgres.json'
    DEFAULT_FACTERFILE = '/etc/facter/facts.d/pg.yaml'

    def __init__(self, service, role_source, configfile=DEFAULT_CONFIGFILE):
        self.service = service
        self.role_source = role_source

        self.api_endpoint = 'http://127.0.0.1:8500/v1'
        self.api_session = requests.Session()

        self.hostname = gethostname()
        self.short_hostname = self.hostname.split('.')[0]

        self.update_service = False
        self.valid_states = ['master', 'slave', 'fail']

        self.configfile = configfile
        self.leader_uri = self.api_endpoint + '/kv/session/' + self.service + '/leader'

    def configure(self):
        # load config values
        try:
            with open(self.configfile) as configfile_contents:
                self.config = json.load(configfile_contents)
        except:
            self.config = {}

        try:
            self.agent_services = self.api_session.get(self.api_endpoint + '/agent/services?stale').json()
        except:
            print_exc()
            exit(135)
        self.managed_service = self.agent_services[self.service]

        if self.managed_service['Tags'] == None:
            self.managed_service['Tags'] = []

        if self.role_source == "facter":
            self.get_facter_state(self.DEFAULT_FACTERFILE)
        else:
            print("!! unsupported PG role source !!")
            exit(140)

    def __del__(self):
        self.api_session.close()

    def get_facter_state(self, fact_file):
        try:
            # use the same file that the ansible-playbooks use
            with open(fact_file, 'r') as ff:
                facts = yaml.load(ff.read())

            self.pg_role = facts['pg_role']
        except:
            # this exception is entered for multiple reasons (file missing, key missing, etc).
            # recreate the default fact setting of slave
            self.pg_role = 'slave'

        print("facter returns state: %s" % self.pg_role)

    def lock_session_leader(self):
        # if we're the master, let's acquire a session and lock the leader key
        if self.pg_role == 'master':
            try:
                node_sessions = self.api_session.get(self.api_endpoint + '/session/node/' + self.short_hostname).json()
                if len(node_sessions) == 0:
                    self.session_id = self.create_session()
                else:
                    # already have a session, let's renew it for this specific service
                    self.session_id = [ses for ses in node_sessions if ses['Name'] == self.service][0]['ID']
                    self.renew_session()

                leader_session_id = self.current_leader_session_id()
                if leader_session_id and leader_session_id != self.session_id:
                    leader_node = self.current_leader_session_info(leader_session_id)

                    if 'pagerduty_service_key' in self.config:
                        self.trigger_pagerduty_multimaster(leader_node)

                    raise Exception('!! leader is already locked by node: ' + leader_node)

                if not self.acquire_lock():
                    raise Exception('!! failed to acquire leader lock')
                else:
                    print('locked leader key: /kv/session/' + self.service + '/leader')
            except:
                print_exc()
                self.purge_tags_and_fail()

    def create_session(self):
        create_session = self.api_session.put(
            self.api_endpoint + '/session/create',
            data=json.dumps({
                "Name": self.service,
                "TTL": "30s"
            })
        )

        if create_session.status_code != 200:
            raise Exception('!! failed to create session')

        return create_session.json()['ID']

    def renew_session(self):
        renew_session = self.api_session.put(self.api_endpoint + '/session/renew/' + self.session_id)
        if renew_session.status_code != 200:
            raise Exception('!! failed to renew session')

    def current_leader_session_info(self, current_leader_session_id):
        current_leader_info = self.api_session.get(self.api_endpoint + '/session/info/' + current_leader_session_id)
        return current_leader_info.json()[0]['Node']

    def current_leader_session_id(self):
        check_current_leader = self.api_session.get(self.leader_uri)
        if check_current_leader.status_code == 200:
            return check_current_leader.json()[0].get('Session')

    def acquire_lock(self):
        # consul returns 200 AND a true json payload if able to acquire lock
        # consul returns 200 AND a false json payload if unable to acquire lock
        lock_leader = self.api_session.put(self.leader_uri + '?acquire=' + self.session_id)
        return lock_leader.status_code == 200 and lock_leader.json() is True

    def add_tag(self, newtag):
        if newtag not in self.managed_service['Tags']:
            self.managed_service['Tags'] += [newtag]
            print("adding tag: %s" % newtag)
            self.update_service = True

    def del_tag(self, oldtag):
        if oldtag in self.managed_service['Tags']:
            self.managed_service['Tags'].remove(oldtag)
            print("removing tag: %s" % oldtag)
            self.update_service = True

    def purge_tags_and_fail(self):
        for tag in self.valid_states:
            self.del_tag(tag)
        self.push_tags()
        exit(150)

    def push_tags(self):
        if self.update_service:
            self.managed_service['Name'] = self.managed_service['Service']
            try:
                self.api_session.put(self.api_endpoint + '/agent/service/register', data=json.dumps(self.managed_service))
            except:
                print_exc()
                exit(131)
            print("updated service through api.")

    def update_tags(self):
        for tag in self.valid_states:
            if tag != self.pg_role:
                self.del_tag(tag)
            elif tag == self.pg_role:
                self.add_tag(tag)

        self.push_tags()

    def trigger_pagerduty_multimaster(self, current_leader):
        # upstream docs: https://v2.developer.pagerduty.com/v2/docs/trigger-events
        # yes this is a weird URL
        pagerduty_event_api = 'https://events.pagerduty.com/generic/2010-04-15/create_event.json'

        payload = {
            'client': 'consul_check_postgres',
            'contexts': [
                {
                    'type': 'link',
                    'href': self.config['notes_url'],
                }
            ],
            'description': "%s attempted to acquire the master consul lock for %s but it was already locked by %s. Two or more nodes are marked as master." % (
                self.short_hostname,
                self.service,
                current_leader
            ),
            'event_type': 'trigger',
            'incident_key': "%s %s master already present" % (self.service, self.short_hostname),
            'service_key': self.config['pagerduty_service_key']
        }

        if len(self.config['pagerduty_service_key']) == 32:
            try:
                pd_response = requests.post(pagerduty_event_api, data=json.dumps(payload))
            except:
                print_exc()

            print('Sending incident to PagerDuty')
            print(pd_response.json())
        else:
            print('PagerDuty Service key is the wrong length (should be 32 characters)')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("service",
                        help="consul service to be managed")
    parser.add_argument("--role-source",
                        default="facter",
                        help="Source of truth for PG role.")
    args = parser.parse_args()

    t = ConsulPostgreSQL(args.service, args.role_source)
    t.configure()
    t.lock_session_leader()
    t.update_tags()
