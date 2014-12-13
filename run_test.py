#!/usr/bin/env python

import sys
sys.path.append('./util/')
import tests_file

def main(args):
  try:
    tests_filename = sys.argv[1]
  except Exception,e:
    sys.stderr.write("Error: %s\n" % str(e))
    try:
      sys.stderr.write("Usage: %s test_file.json\n" % args[0])
    except:
      sys.stderr.write("Usage: run_test.py test_file.json\n")

  tests = tests_file.read_tests(tests_filename)
  for t in tests:
    t.run()

if __name__=="__main__":
  main(sys.argv)
