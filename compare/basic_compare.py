#!/usr/bin/env python

import compare
import json

"""
Compare the output of multiple candidate implementations.

This basic comparator reports a difference if the last result of a "get" is
different across candidates. (We take the last to handle retries.)
"""

class BasicComparator(compare.AbstractComparator):
  def comparator_check(self, results):
    curr_output = None
    for r in results:
      output = r["result"][-1] # take the last output to handle retries
      if curr_output is None:
        curr_output = output
      if curr_output != output:
        return False
    return True
