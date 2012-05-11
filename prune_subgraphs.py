#
# Third step of the decoding finding pipeline. usage:
#  python prune_subgraphs.py <problem_def> <basedir> <worker_index>
#

import pickle, os, sys, time, itertools, cache, operator
from problem import *
import networkx as nx

problem_def = read_problem_definition(sys.argv[1])

with open("cycles.pickle") as f:
  cycles = pickle.load(f)

def index(comb):
  return comb[0]+comb[1]*len(cycles)

def valid_decoding(decoding):
  # if there are less assignments than there are results in the problem definition, it cannot be valid
  if len(decoding) < len(problem_def):
    return False
  return set(map(operator.itemgetter(0), decoding)) == set(problem_def.keys())

total_slices = 399
basedir      = sys.argv[2]
my_slice     = int(sys.argv[3])

data = {}

for vertex in itertools.product(problem_def.keys(), xrange(len(cycles))):
  if index(vertex) % total_slices == my_slice:
    print "processing %s"%str(vertex)
    graph = nx.read_gpickle("%s/graphs/%d-%d.gpickle.bz2"%(basedir, vertex[0], vertex[1]))

    total = 0
    for node in graph.nodes():
      neighbours = graph.neighbors(node)
      if not valid_decoding(neighbours+[node]):
        graph.remove_node(node)
        total += 1

    print " removed %d nodes, remaining %d"%(total, len(graph))

    nx.write_gpickle(graph, "%s/pruned_graphs/%d-%d.gpickle.bz2"%(basedir, vertex[0], vertex[1]))

