# Flotsam
Flotsam is an error checker for Raft implementations. Rather than specify test
cases and check that implementations match expected output, Flotsam pits the
Rafts against each other and checks for inconsistencies.

Flotsam is a course project for the autumn 2014 offering of Stanford
[CS244B](http://cs244b.scs.stanford.edu).

## Main Modules
Flotsam consists of three main modules, each of which is mostly independent of
the others.

### Test-case Generation (`testgen/`)
The test-case generation module is responsible for making up tests that we will
run against the candidate implementations.
It outputs the test cases in a way that can be run by the test harness.

### Actual Testing (`run/`)
This module actually does the testing; it is the "test harness" for Flotsam.
It needs to know how to do two main tasks:

1. Run the implementation and send it commands.
1. Interpret the test case and collect its output.

### Output Comparison (`compare/`)
The output comparison tool checks whether the implementations have produced
consistent results.

## Extensibility
Each of these modules could be replaced by another.
For instance, one might wish to write a more strict output comparison tool,
or write a test-case generator that used a different distribution over the
key space or didn't use key-value stores at all.
The overall testing framework allows them to be replaced.
In this version of Flotsam, however, there is just one implementation of each.

## Required Setup
Flotsam runs on Docker and incorporates a number of open-source projects as
candidates. It would be best to dedicate a VM to Flotsam. Flotsam is only tested
on Ubuntu 14.04 and requires up-to-date Docker, among other dependencies.

Run `setup/setup.sh` as root to interactively setup your environment; this will
install dependencies and build Docker images using the specifications in this
repository.

## Run
Flotsam, due to its use of Docker, must be run as root.

To run a test (like those provided in `tests/`), run
`./run_test.py tests/toy.json` as root.
