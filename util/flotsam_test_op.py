#!/usr/bin/env python

"""
This class defines how to read and write test specifications.
"""

import json

class FlotsamTestOp(object):
  def __init__(self):
    pass

  def from_str(self, in_str):
    test = json.loads(in_str)

  def to_str(self):
    op = self.op
    test = dict(op=op)
    if op == "get" or op == "set":
      test["key"] = self.key
      test["retry"] = self.retry
    if op == "set":
      test["val"] = self.val
    if op == "fail" or op == "partition":
      test["nodes"] = self.nodes
    return json.dumps(test)
