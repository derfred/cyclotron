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
  return comb[0]+comb[1]*len(cycles)

# Are all potential results represented in the decoding?
def valid_decoding(decoding):
  # if there are less assignments than there are results in the problem definition, it cannot be valid
  if len(decoding) < len(problem_def):
    return False
  return set(map(operator.itemgetter(0), decoding)) == set(problem_def.keys())

def subgraph_cliques(graph, center_vertex, testfn):
  if len(graph) > 0:
    sage_graph = Graph(graph)
    for clique in filter(testfn, sage.graphs.cliquer.all_max_clique(sage_graph)):
      yield frozenset(clique)

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
      cycle_mapping = map(lambda c: (c[0], cycles[c[1]]), clique)
      solution      = Solution(problem_def, cycle_mapping)
      solution.solve()
      if solution.satisfiable():
        print "  is consistent"
        result.add(clique)

with open("%s/cliques/%d.pickle"%(basedir, my_slice), "w") as f:
  pickle.dump(list(result), f)
