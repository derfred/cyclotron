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
  for data, graph in graphs.iteritems():
    for node in graph.nodes_iter():
      if len(graph.successors(node)) == 2:
        for succ in graph.successors(n):
          result.add( (node, succ, d[1]) )
  return result

def choose_transitions(cycle_mapping, chosen):
  graphs = potentially_connected(problem_def, cycle_mapping, chosen)
  if not graphs:
    return

  # since the target cycles are always present, if the total number of cycles in the
  # graph is equal to the number of target cycles, there are no other invalid cycles
  if all(len(data[2]) == len(nx.simple_cycles(graph)) for data, graph in graphs.iteritems()):
    # this setup only exhibits valid cycles, even though its not fully determined
    # thats also a valid result
    return [chosen]

  choice_points = find_choice_points(graphs)
  if len(choice_points) == 0:
    # the system is fully determined and its still connected
    # this should be a winner!
    return [chosen]

  result = []
  for choice in choice_points:
    out = choose_transitions(cycle_mapping, chosen+[choice])
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
    cycle_mapping = map(lambda c: (c[0], tuple(cycles[c[1]])), clique)
    for choices in choose_transitions(cycle_mapping, []):
      print "have one"
      result.append( (clique, choices) )

with open("%s/connected_cliques/%d/%d.pickle"%(basedir, clique_size, my_slice), "w") as f:
  pickle.dump(result, f)
