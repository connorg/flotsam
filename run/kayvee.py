#!/usr/bin/env python

"""
Run the kayvee service from allengeorge/libraft/libraft-samples/kayvee.

Requires requests: pip install requests
"""

import urllib2
import candidate
import sys
from time import sleep
import json
import requests
import os.path
import os

class KayveeCandidate(candidate.FlotsamCandidate):
  def __init__(self):
    super(KayveeCandidate,self).__init__()
    self.name = "libraft/kayvee"
    self.docker_image = "kayvee"
    self.web_ports = [4001, 4002, 4003, 4004, 4005]
    self.raft_ports = [5001, 5002, 5003, 5004, 5005]
    self.num_containers = len(self.web_ports)
    self.leader = 0 # Note, this is not thread-safe.
    # Currently we have no concurrent actions, though.
    self.LOCAL_CONFIG_DIR = os.path.abspath('./kayvee-configs/')
    try:
      os.mkdir(self.LOCAL_CONFIG_DIR)
    except OSError:
      sys.stderr.write("note: dir %s already exists\n" % self.LOCAL_CONFIG_DIR)

  def create_containers(self):
    self.process_name = "kayvee"

    if self.docker_image is None:
      raise Exception("Docker image not set for %s" % (self.name or "candidate"))

    # From libraft-samples/kayvee/README.md
    # We directly construct the YAML string to take advantage of the example.
    # Note there are some additions not specified in the docs, like 'database:'
    template = """
http:
  # port on which KayVee listens for client requests
  port: {web_port}
  # port on which KayVee listens for admin commands
  adminPort: {admin_port}

database:
  driverClass: org.sqlite.JDBC
  url: jdbc:sqlite:kayvee.db
  user: test
  password: test

# raft-agent Log and Store database
raftDatabase:
  driverClass: org.sqlite.JDBC
  url: jdbc:sqlite:kayvee_raft.db
  user: test
  # password may be empty or omitted
  password: test

# cluster configuration
cluster:
  # unique id of _this_ server
  self: {this_server}

  # lists _all_ the members in the cluster
  # members can be defined in any order
  members:
    # configuration block describing _this_ server
    # uses settings defined in the 'http' block above for kayVeeUrl
{common_portion}

logging:
  level: INFO

  console:
    enabled: true

  file:
    enabled: true
    currentLogFilename: kayvee.log
    archivedLogFilenamePattern: kayvee-%d.log.gz
    archivedFileCount: 3
    """
    config_each_member = """    - id: {hostname}
      # http (i.e. client API) url
      kayVeeUrl: http://{hostname}:{web_port}
      # raft consensus system endpoint
      raftEndpoint: {hostname}:{raft_port}"""

    config_members = []
    for web_port, raft_port in zip(self.web_ports, self.raft_ports):
      hostname = self.hostname_for_port(web_port)
      c = self.docker_cli.create_container(image=self.docker_image,
                                           name=hostname,
                                           hostname=hostname,
                                           entrypoint=["bash"],
                                           detach=True,
                                           stdin_open=True,
                                           ports=[web_port, raft_port],
                                           volumes=['/kayvee-configs/'])
      self.containers.append(c)
      config_members.append(config_each_member.format(hostname=hostname,
                                                      web_port=web_port,
                                                      raft_port=raft_port))

    for web_port, raft_port in zip(self.web_ports, self.raft_ports):
      hostname = self.hostname_for_port(web_port)
      # "If your configuration file doesn't end in .yml or .yaml, Dropwizard tries to parse it as a JSON file."
      # http://dropwizard.github.io/dropwizard/0.6.2/manual/core.html
      with open(os.path.join(self.LOCAL_CONFIG_DIR, hostname+".yml"), 'w') as fout:
        fout.write(template.format(web_port=web_port, admin_port=web_port,
                                   this_server=hostname,
                                   common_portion="\n".join(config_members)))

  def hostname_for_port(self, port):
    return "kayvee%d" % port

  def launch_containers(self):
    host_ip = self.get_host_ip()
    self.reset_dns()
    # Start the container in privileged mode to allow iptables manipulations
    for c, web_port, raft_port in zip(self.containers, self.web_ports, self.raft_ports):
      port_map = {}
      port_map[web_port] = web_port
      port_map[raft_port] = raft_port
      while not self.is_running(c):
        sys.stderr.write("Trying to start %d %d\n" % (web_port, raft_port))
        self.docker_cli.start(c["Id"], privileged=True, port_bindings=port_map, dns=[host_ip], binds={self.LOCAL_CONFIG_DIR: {'bind': '/kayvee-configs/', 'ro': True}})
        sleep(2)
      ip = self.get_container_ip(c)
      hostname = self.hostname_for_port(web_port)
      self.register_dns(hostname, ip)
    self.refresh_dns()

  def start_containers(self):
    for c, web_port, raft_port in zip(self.containers, self.web_ports, self.raft_ports):
      hostname = self.hostname_for_port(web_port)
      # kayvee gets mad if you don't have the file at ./kayvee.yml
      self.docker_cli.execute(c["Id"], ["cp", "/kayvee-configs/" + hostname + ".yml", "kayvee.yml"])
      cmd = ["/kayvee/kayvee", "server", "kayvee.yml"]
      sys.stderr.write("Starting %s\n" % cmd)
      self.docker_cli.execute(c["Id"], cmd, detach=True, stdout=False, stderr=False)

  def read(self, key):
    # Returns 301 if leader is different
    # Returns 503 if no leader
    # URLError is raised if the server is unavailable.
    results = []
    while (True):
      try:
        attempt = urllib2.urlopen("http://%s:%d/keys/%s" % (self.hostname_for_port(self.web_ports[self.leader]), self.web_ports[self.leader], key))
        result = attempt.read()
        try:
          results.append(json.loads(result)["value"])
        except:
          results.append(result)
        valid_codes = [200, 404]
        if int(attempt.getcode()) in valid_codes:
          break # Done if we got 200 (value) or 404 (not found)
      except urllib2.URLError:
        sys.stderr.write('Trying next Raft party due to URLError on %s.\n' % self.leader)
        self.leader = (self.leader + 1) % len(self.web_ports)
    return results

  def write(self, key, val):
    # Returns 301 if leader is different
    # Returns 503 if no leader
    # URLError is raised if the server is unavailable.
    results = []
    while (True):
      try:
        put_data = json.dumps({"newValue": str(val)}, indent=1) # json.dumps({'newValue': val})
        url = "http://%s:%d/keys/%s" % (self.hostname_for_port(self.web_ports[self.leader]), self.web_ports[self.leader], key)
        headers = {'Content-Type': 'application/json'}
        r = requests.put(url, data=put_data, headers=headers, allow_redirects=False)
        results.append(r.content)
        if int(r.status_code) == 200:
          results.append("Success")
          break # Done if we got a 200!
        if int(r.status_code) == 301:
          raise requests.exceptions.RequestException("not leader, try round-robin")
      except requests.exceptions.RequestException,e:
        sys.stderr.write('Trying next Raft party due to RequestException on %s.\n' % self.leader)
        self.leader = (self.leader + 1) % len(self.web_ports)
    return results
