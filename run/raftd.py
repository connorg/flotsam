#!/usr/bin/env python

"""
Run the raftd service from goraft/raftd.
"""

import urllib2
import candidate
import sys
from time import sleep

class RaftdCandidate(candidate.FlotsamCandidate):
  def __init__(self):
    super(RaftdCandidate,self).__init__()
    self.name = "goraft/raftd"
    self.docker_image = "raftd"
    self.ports = [4001, 4002, 4003, 4004, 4005]
    self.num_containers = len(self.ports)
    self.leader = 0 # Note, this is not thread-safe.
    # Currently we have no concurrent actions, though.

  def create_containers(self):
    self.process_name = "app"

    if self.docker_image is None:
      raise Exception("Docker image not set for %s" % (self.name or "candidate"))

    for port in self.ports:
      hostname = self.hostname_for_port(port)
      c = self.docker_cli.create_container(image=self.docker_image,
                                           name=hostname,
                                           hostname=hostname,
                                           entrypoint=["bash"],
                                           detach=True,
                                           stdin_open=True,
                                           ports=[port])
      self.containers.append(c)

  def hostname_for_port(self, port):
    return "raft%d" % port

  def launch_containers(self):
    host_ip = self.get_host_ip()
    self.reset_dns()
    for c, port in zip(self.containers, self.ports):
      port_map = {}
      port_map[port] = port
      while not self.is_running(c):
        sys.stderr.write("Trying to start %d\n" % port)
        # Start the container in privileged mode to allow iptables manipulations
        self.docker_cli.start(c["Id"], privileged=True, port_bindings=port_map, dns=[host_ip])
        sleep(5)
      ip = self.get_container_ip(c)
      hostname = self.hostname_for_port(port)
      self.register_dns(hostname, ip)
    self.refresh_dns()

  def start_containers(self):
    # Start the leader
    leader_port = self.ports[0]
    leader_hostname = self.hostname_for_port(leader_port)
    leader = "%s:%d" % (leader_hostname, leader_port)
    leader_cmd = ["app", "-trace", "-h", leader_hostname, "-p", str(leader_port), "~/raft/"]
    leader_container = self.containers[0]
    sys.stderr.write("Starting %s\n" % str(leader_cmd))
    self.docker_cli.execute(leader_container["Id"], leader_cmd, detach=True, stdout=False, stderr=False)

    # Join the non-leaders to the leader
    for c, port in zip(self.containers[1:], self.ports[1:]):
      hostname = self.hostname_for_port(port)
      follower_cmd = ["app", "-trace", "-h", hostname, "-p", str(port), "-join", leader, "~/raft/"]
      sys.stderr.write("Starting %s\n" % follower_cmd)
      self.docker_cli.execute(c["Id"], follower_cmd, detach=True, stdout=False, stderr=False)

  def read(self, key):
    # Returns 400 with message "raft.Server: Not current leader" if applicable
    # URLError is raised if the server is unavailable.
    results = []
    while (True):
      try:
        attempt = urllib2.urlopen("http://%s:%d/db/%s" % (self.get_container_ips()[self.leader], self.ports[self.leader], key))
        results.append(attempt.read())
        if int(attempt.getcode()) == 200:
          break # Done if we got a 200!
      except urllib2.URLError:
        sys.stderr.write('Trying next Raft party due to URLError on %s.\n' % self.leader)
        self.leader = (self.leader + 1) % len(self.ports)
    return results

  def write(self, key, val):
    # Returns 400 with message "raft.Server: Not current leader" if applicable
    # URLError is raised if the server is unavailable.
    results = []
    while (True):
      try:
        attempt = urllib2.urlopen("http://%s:%d/db/%s" % (self.get_container_ips()[self.leader], self.ports[self.leader], key), data=val)
        results.append(attempt.read())
        if int(attempt.getcode()) == 200:
          results.append("Success")
          break # Done if we got a 200!
      except urllib2.URLError:
        sys.stderr.write('Trying next Raft party due to URLError on %s.\n' % self.leader)
        self.leader = (self.leader + 1) % len(self.ports)
    return results
