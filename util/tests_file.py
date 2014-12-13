#!/usr/bin/env python

"""
Reads the test specification format.
"""

import json
import sys
import flotsam_test
sys.path.append('./testgen/')
import key_val_uniform
sys.path.append('./run/')
import raftd
import raftd_forgetful
import kayvee
import literaft
sys.path.append('./compare/')
import basic_compare


def read_tests(filename):
  tests = []
  generators = {'key_val_uniform': key_val_uniform.KeyValUniTestGen}
  candidates = {'raftd': raftd.RaftdCandidate,
                'raftd_forgetful': raftd_forgetful.RaftdForgetfulCandidate,
                'kayvee': kayvee.KayveeCandidate,
                'lite-raft': literaft.LiteraftCandidate}
  comparators = {'basic': basic_compare.BasicComparator}
  with open(filename, 'r') as infile:
    spec = json.load(infile)
    name = spec["name"]
    runners = spec["candidates"]
    for t in spec["tests"]:
      gen = generators[t["gen"]](5)
      impls = [candidates[r]() for r in runners]
      comp = comparators[t["comp"]]()
      tests.append(flotsam_test.FlotsamTest(gen, impls, comp))
  return tests
