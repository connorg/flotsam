#!/usr/bin/env python

from itertools import imap, starmap, izip
import json
import sys

"""
Basic 'abstract' class for output comparison.
"""

def output_parse(line):
  return json.loads(line.strip())

class AbstractComparator(object):
  def __init__(self):
    pass

  """
  Hands off all the results to check(), candidate-by-candidate.
  """
  def compare(self, outputs):
    all_ok = self.check(outputs.values())
    if all_ok:
      print
      print "No inconsistencies found!"
    return all_ok

  """
  Parse each item and then pass it off to be checked.
  """
  def check(self, streams):
    return all(map(self.comparator_check_wrap, izip(*streams)))

  """
  Unpacks the test result and sends to the comparator-specific checking
  function.
  """
  def comparator_check_wrap(self, lines):
    ok = self.comparator_check([output_parse(line) for line in lines])
    if not ok:
      sys.stderr.write("ERROR! Inconsistent output:\n%s\n" % "\n".join(lines))
    return ok

  # Subclass must implement self.comparator_check(lines)
  def comparator_check(self, lines):
    raise NotImplementedError("Comparator does not define comparator_check")
