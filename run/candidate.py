#!/usr/bin/env python

"""
An 'abstract' class that lets us define implementations to test.

Requires docker-py: pip install docker-py
Requires netifaces: pip install netifaces
"""

import docker
import json
import os
import os.path
import shutil
import sys
import netifaces

DNSMASQ_DIR = "/opt/flotsam/dnsmasq.d/"

class FlotsamCandidate(object):
  def __init__(self):
    self.docker_cli = docker.Client(base_url='unix://var/run/docker.sock')
    self.containers = []
    self.num_containers = 5 # default

  """
  Prepare the containers.
  """
  def create_containers(self):
    raise NotImplementedError("Candidate does not implement create_containers")

  """
  Launch the containers.
  """
  def launch_containers(self):
    raise NotImplementedError("Candidate does not implement launch_containers")

  """
  Start processes in the containers, if necessary for the candidate.
  """
  def start_containers(self):
    raise NotImplementedError("Candidate does not implement start_containers")

  """
  Cleanup the containers; gracefully stop them and them remove them from Docker.
  """
  def cleanup_containers(self):
    for c in self.containers:
      try:
        self.docker_cli.stop(c["Id"], timeout=1)
      except docker.errors.APIError:
        pass # Already stopped
    for c in self.containers:
      self.docker_cli.remove_container(c["Id"])

  """
  Fail one or more nodes by stopping the candidate's container.
  """
  def fail_node(self, nodes):
    sys.stderr.write("Failing node %s by Docker stop() on its container\n" % str(nodes))
    if self.process_name is None:
      raise Exception("Process name not set for %s" % (self.name or "candidate"))
    for node_idx in nodes:
      self.docker_cli.stop(self.containers[node_idx]["Id"], timeout=1)
    return "Failed"

  """
  Returns the IP associated with a single container
  """
  def get_container_ip(self, container):
    inspector = self.docker_cli.inspect_container(container["Id"])
    return inspector["NetworkSettings"]["IPAddress"]

  """
  Returns the IPs associated with the containers we're using.
  """
  def get_container_ips(self):
    ips = []
    for c in self.containers:
      ip = self.get_container_ip(c)
      ips.append(ip)
    return ips

  """
  Checks the "Running" field to see if the container is running.
  """
  def is_running(self, container):
    inspector = self.docker_cli.inspect_container(container["Id"])
    status = inspector["State"]["Running"] # This is a boolean
    return status

  """
  Get the IP address of the Docker host, using the special 'docker0' iface.
  """
  def get_host_ip(self):
    return netifaces.ifaddresses('docker0')[netifaces.AF_INET][0]['addr']

  """
  Reset DNS by deleting the contents of the directory we use to configure
  dnsmasq
  """
  def reset_dns(self):
    shutil.rmtree(DNSMASQ_DIR, ignore_errors=True)
    os.makedirs(DNSMASQ_DIR)
    os.system("service dnsmasq restart")

  """
  Register hostname-to-IP matches for the given mapping.
  """
  def register_dns(self, host, ip):
    with open(os.path.join(DNSMASQ_DIR, "0host_"+host), 'w') as dns_file:
      dns_file.write("host-record=%s,%s" % (host, ip))

  """
  Restart DNS service to pick up changes
  """
  def refresh_dns(self):
    os.system("service dnsmasq restart")

  """
  Cause a network partition that isolates the specified nodes using iptables
  firewall rules.

  This is implemented by dropping all traffic to nodes *not* in the partition.
  """
  def partition_nodes(self, nodes):
    sys.stderr.write("Partitioning node %s using iptables\n" % str(nodes))
    ips = self.get_container_ips()
    ips_outside_partition = []
    for idx, ip in enumerate(ips):
      if idx not in nodes:
        ips_outside_partition.append(str(ip))
    ips_outside_partition.append(self.get_host_ip())
    cmds = ['iptables -A INPUT -s %s -j DROP' % ip for ip in ips_outside_partition]
    cmds.extend(['iptables -A OUTPUT -d %s -j DROP' % ip for ip in ips_outside_partition])
    for node_idx in nodes:
      for cmd in cmds:
        self.execute_on_node_id(node_idx, cmd)
    return "Partitioned"

  """
  Removes the partition condition by removing the iptables rules we set above
  (and all the others). Note that this does not support any notion of multiple
  simultaneous partitions.
  """
  def unpartition_nodes(self, nodes):
    cmds = ['iptables -F',
      'iptables -X',
      'iptables -t nat -F',
      'iptables -t nat -X',
      'iptables -t mangle -F',
      'iptables -t mangle -X',
      'iptables -t raw -F',
      'iptables -t raw -X',
      'iptables -t security -F',
      'iptables -t security -X',
      'iptables -P INPUT ACCEPT',
      'iptables -P FORWARD ACCEPT',
      'iptables -P OUTPUT ACCEPT']
    for node_idx in nodes:
      for cmd in cmds:
        self.execute_on_node_id(node_idx, cmd)
    return "Unpartitioned"

  """
  Convenience function to execute a function on the container with given
  internal index (assigned in order of creation).
  """
  def execute_on_node_id(self, id, cmd):
    self.docker_cli.execute(self.containers[int(id)]["Id"], cmd)

  """
  Run the entire test--boot up the virtualized environment, test, and clean up.
  """
  def run_test(self, ops_stream):
    sys.stderr.write("Creating containers...\n")
    self.create_containers()
    sys.stderr.write("Launching containers...\n")
    self.launch_containers()
    sys.stderr.write("Starting processes...\n")
    self.start_containers()
    sys.stderr.write("Beginning tests...\n")
    output = []
    for num, line in enumerate(ops_stream):
      test = json.loads(line.strip())
      result = {}
      result["candidate"] = self.name
      result["test_op"] = test
      op = test["op"]
      if op == "get":
        result["result"] = self.read(test["key"])
      elif op == "set":
        result["result"] = self.write(test["key"], test["val"])
      elif op == "fail":
        result["result"] = self.fail_node(test["nodes"])
      elif op == "partition":
        result["result"] = self.partition_nodes(test["nodes"])
      elif op == "unpartition":
        result["result"] = self.unpartition_nodes(test["nodes"])
      output.append(json.dumps(result))
      if num % 10 == 0:
        sys.stderr.write(".")
    sys.stderr.write("\nCleaning up containers...\n")
    self.cleanup_containers()
    return output
