#!/usr/bin/env python

"""
Run the lite-raft service

Requires that the host be setup for password-less, known-key SSH.
"""

import urllib2
import candidate
import sys
from time import sleep
import json
import requests
import os.path
import os

class LiteraftCandidate(candidate.FlotsamCandidate):
  def __init__(self):
    super(LiteraftCandidate,self).__init__()
    self.name = "lite-raft"
    self.docker_image = "lite-raft"
    self.parties = range(5)
    self.num_containers = len(self.parties)
    self.leader = 0 # Note, this is not thread-safe.
    # Currently we have no concurrent actions, though.
    self.LOCAL_CONFIG_DIR = os.path.abspath('./lite-raft-configs/')
    try:
      os.mkdir(self.LOCAL_CONFIG_DIR)
    except OSError:
      sys.stderr.write("note: dir %s already exists\n" % self.LOCAL_CONFIG_DIR)

  def create_containers(self):
    self.process_name = "lite-raft"

    if self.docker_image is None:
      raise Exception("Docker image not set for %s" % (self.name or "candidate"))

    hostnames = []
    for number in self.parties:
      hostname = self.hostname_for_num(number)
      hostnames.append(hostname)
      c = self.docker_cli.create_container(image=self.docker_image,
                                           name=hostname,
                                           hostname=hostname,
                                           # entrypoint=["bash"],
                                           detach=True,
                                           stdin_open=True,
                                           # ports=[22],
                                           volumes=['/lite-raft-configs/'])
      self.containers.append(c)

    with open(os.path.join(self.LOCAL_CONFIG_DIR, "cluster_nodes"), 'w') as fout:
      fout.write(" ".join(hostnames))

  def hostname_for_num(self, num):
    return "lite-raft%d" % num

  def launch_containers(self):
    host_ip = self.get_host_ip()
    self.reset_dns()
    # Start the container in privileged mode to allow iptables manipulations
    for c, number in zip(self.containers, self.parties):
      port_map = {}
      # port_map[22] = 22
      while not self.is_running(c):
        sys.stderr.write("Trying to start %d\n" % number)
        self.docker_cli.start(c["Id"], privileged=True, port_bindings=port_map, dns=[host_ip], binds={self.LOCAL_CONFIG_DIR: {'bind': '/lite-raft-configs/', 'ro': True}})
        sleep(2)
      ip = self.get_container_ip(c)
      hostname = self.hostname_for_num(number)
      self.register_dns(hostname, ip)
    self.refresh_dns()

  def start_containers(self):
    for c, number in zip(self.containers, self.parties):
      hostname = self.hostname_for_num(number)
      self.docker_cli.execute(c["Id"], ["cp", "/lite-raft-configs/cluster_nodes", "/lite-raft/conf/cluster_nodes"])
      cmd = ["run-lr.sh", "./lite-raft", "first-boot"]
      sys.stderr.write("Starting %s\n" % str(cmd))
      # HACK: Without a sleep() here, lite-raft won't complete setup correctly
      sleep(5)
      self.docker_cli.execute(c["Id"], cmd, detach=True, stdout=False, stderr=False)

  def read(self, key):
    # Returns 400 with message "raft.Server: Not current leader" if applicable
    # URLError is raised if the server is unavailable.
    results = []
    tries = 0
    while (True):
      try:
        # Docker exec to run ./lite-raft-client get {key}
        res = self.docker_cli.execute(self.containers[self.leader], ["run-lr.sh", "./lite-raft-client", "get", key])
        results.append(res)
        if ("leader is not available" in res) or ("leader is stale" in res):
          tries += 1
          if tries < 50:
            continue # Try again here
          else:
            tries = 0
            raise Exception("try elsewhere")
        elif "no server running" in res:
          raise Exception("not running here")
        else:
          # Success is just the value or a "not found" msg; either's fine.
          # Remove line break on the end of the returned value.
          results[-1] = results[-1][:-1]
          break
      except:
        sys.stderr.write("Switching presumed leader from %d\n" % self.leader)
        self.leader = (self.leader + 1) % len(self.parties)
    return results

  def write(self, key, val):
    # Returns 400 with message "raft.Server: Not current leader" if applicable
    # URLError is raised if the server is unavailable.
    results = []
    while (True):
      try:
        # Docker exec to run ./lite-raft-client get {key}
        # bad: "timeout waiting for commit", "append-entry failed", "not leader"
        # good: "client succeded" [sic]
        cmd = ["run-lr.sh", "./lite-raft-client", "set", key, val]
        res = self.docker_cli.execute(self.containers[self.leader], cmd)
        results.append(res)

        if ("timeout waiting for commit" in res) or ("append-entry failed" in res):
          tries += 1
          if tries < 50:
            continue # Try again here
          else:
            tries = 0
            raise Exception("try elsewhere")
        elif "not leader" in res:
          raise Exception("try elsewhere")
        elif "no server running" in res:
          raise Exception("not running here")
        elif len(res.strip()) == 0: # returns nothing (used to say 'client succeeded' [sic])
          results.append("Success")
          return results # Success!
      except:
        sys.stderr.write("Switching presumed leader from %d\n" % self.leader)
        self.leader = (self.leader + 1) % len(self.parties)
    return results
