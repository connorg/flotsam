from key_val import KeyValTestGen
import json
import random
import sys

"""
This module randomly creates test cases, assuming a key-value store and using
a uniform distribution across the keys. The mix of gets and sets is even and
each get currently happens right after the set.
"""

class KeyValUniTestGen(KeyValTestGen):
  """
  Initialize the test generator. Use a seed if you want reproducible tests.
  """
  def __init__(self, num_nodes, num_keys=200, seed=None):
    self.keys = [self.int_to_key(i) for i in xrange(num_keys)]
    random.seed(seed)
    self.current_failures = set()
    self.num_nodes = num_nodes

  def int_to_key(self, n):
    curr = n
    key = ''
    while (curr >= 0):
      key += chr((curr % 26) + ord('a'))
      curr -= 26
    return key

  """
  Can we fail another node at this point in the test?
  Ensures that the new number of failures, f, wouldn't cause 2f+1 to exceed the
  total number of nodes, since that would just cause the test to stall forever.
  """
  def can_fail(self):
    return 2*(len(self.current_failures) + 1) + 1 <= self.num_nodes

  def mark_failed(self, node_id):
    self.current_failures.add(node_id)

  def gen_tests(self, n=1000, prob_fail=0.01):
    result = []
    for i in xrange(n):
      key = random.choice(self.keys)
      val = str(random.randint(1,99999999))
      test = dict(op="set", key=key, val=val)
      result.append(json.dumps(test))
      test = dict(op="get", key=key)
      result.append(json.dumps(test))
      if random.random() < 0.01 and self.can_fail():
        newly_failed = random.choice(sorted(list(set(xrange(self.num_nodes)).difference(self.current_failures))))
        self.mark_failed(newly_failed)
        if random.random() < 0.5:
          sys.stderr.write("Inserting node failure %d\n" % newly_failed)
          test = dict(op="fail", nodes=[newly_failed])
        else:
          sys.stderr.write("Inserting node partition %d\n" % newly_failed)
          test = dict(op="partition", nodes=[newly_failed])
        result.append(json.dumps(test))
    sys.stderr.write("Finished generating tests.\n")
    return result

if __name__=="__main__":
  KeyValUniTestGen().gen_tests()
