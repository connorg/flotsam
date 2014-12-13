#!/usr/bin/env python

"""
Run the "forgetful" version of the raftd service from goraft/raftd.
Everything is the same as the actual raftd service, except for the Docker image
and the name.
"""

import raftd

class RaftdForgetfulCandidate(raftd.RaftdCandidate):
  def __init__(self):
    super(RaftdForgetfulCandidate,self).__init__()
    self.name = "connorg/raftd-forgetful"
    self.docker_image = "raftd-forgetful"
    self.ports = [5001, 5002, 5003, 5004, 5005]
    self.num_containers = len(self.ports)
