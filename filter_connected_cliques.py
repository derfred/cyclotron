#
# Sixth (and last) step of the decoding finding pipeline. usage:
#  python filter_connected_cliques.py <problem_def> <basedir> <max_len> <clique_size> <worker_index>
#

import pickle, sys, os, itertools, operator
from inequality_decider import InequalityDecider, potentially_connected
from problem import *
from state import State
import networkx as nx

problem_def = read_problem_definition(sys.argv[1])
basedir     = sys.argv[2]
max_len     = int(sys.argv[3])
clique_size = int(sys.argv[4])

with open("cycles.pickle") as f:
  cycles = filter(lambda c: len(c) <= max_len, pickle.load(f))

with open("%s/unique_potentially_connected_cliques/%d.pickle"%(basedir, clique_size)) as f:
  cliques = pickle.load(f)

def index(comb):
  return comb[1]+comb[0]*len(cycles)

def find_choice_points(graphs):
  result = set()
  for d, g in graphs.iteritems():
    for n in g.nodes_iter():
      if len(g.successors(n)) == 2:
        for succ in g.successors(n):
          result.add( (n, succ, d[1]) )
  return result

def choose_transitions(clique, chosen):
  graphs = potentially_connected(clique, chosen)
  if not graphs:
    return

  choice_points = find_choice_points(graphs)
  if len(choice_points) == 0:
    # the system is fully determined and its still connected
    # this should be a winner!
    return [chosen]

  result = []
  for choice in choice_points:
    out = extend_transitions(clique, chosen+[choice])
    if out:
      result += out
  return result


total_slices = 399
my_slice     = int(sys.argv[5])

result       = list()

for i in xrange(len(cliques)):
  if i % total_slices == my_slice:
    clique        = cliques[i]
    print "starting %d %s"%(i, str(clique))
    for choices in choose_transitions(clique, []):
      print "have one"
      result.append( (clique, choices) )

with open("%s/connected_cliques/%d/%d.pickle"%(basedir, clique_size, my_slice), "w") as f:
  pickle.dump(result, f)
