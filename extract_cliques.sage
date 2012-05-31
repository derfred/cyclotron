#
# Third step of the decoding finding pipeline. usage:
#  sage -python extract_cliques.sage <problem_def> <basedir> <worker_index>
#

import pickle, os, sys, time, operator, itertools
import networkx as nx
from solution import Solution
from state import State
from problem import *

problem_def = read_problem_definition(sys.argv[1])
max_len     = int(sys.argv[3])

with open("cycles.pickle") as f:
  cycles = filter(lambda c: len(c) <= max_len, pickle.load(f))

def index(comb):
  return comb[1]+comb[0]*len(cycles)

# Are all potential results represented in the decoding?
def valid_decoding(decoding):
  # if there are less assignments than there are results in the problem definition, it cannot be valid
  if len(decoding) < len(problem_def):
    return False
  return set(map(operator.itemgetter(0), decoding)) == set(problem_def.keys())

def subgraph_cliques(graph, center_vertex, testfn):
  for clique in filter(testfn, nx.find_cliques(graph)):
    yield frozenset(clique)

def consistent_subcliques(clique):
  cycle_mapping = map(lambda c: (c[0], cycles[c[1]]), clique)
  solution      = Solution(problem_def, cycle_mapping)
  solution.solve()

  if solution.satisfiable():
    yield clique
  else:
    redundant_assignments = filter(lambda l: len(l) > 1, map(lambda r: filter(lambda a: a[0] == r, clique), problem_def.keys()))
    for assignment in itertools.chain(*redundant_assignments):
      consistent_subcliques(clique-frozenset([assignment]))


result = set()

total_slices = 399
basedir      = sys.argv[2]
my_slice     = int(sys.argv[4])

for vertex in itertools.product(problem_def.keys(), xrange(len(cycles))):
  if index(vertex) % total_slices == my_slice:
    graph = nx.read_gpickle("%s/pruned_graphs/%d-%d.gpickle.bz2"%(basedir, vertex[0], vertex[1]))
    graph.name = str(vertex) # there is something odd going on in subgraph, which requires the graph to have a name
    print "processing %s (%d nodes)"%(str(vertex), len(graph))

    for clique in subgraph_cliques(graph, vertex, valid_decoding):
      print " is valid %s"%str(clique)
      for subclique in consistent_subcliques(clique):
        print "  is consistent"
        result.add(clique)

with open("%s/cliques/%d.pickle"%(basedir, my_slice), "w") as f:
  pickle.dump(list(result), f)
