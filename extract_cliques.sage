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
  try:
    for clique in filter(testfn, nx.find_cliques(subgraph)):
      yield frozenset(clique)
  except MemoryError, e:
    # full processing not working for memory constraint reasons
    for node in graph.nodes_iter():
      if node != center_vertex:
        vertices = set(graph.neighbors(node)) & set(graph.neighbors(center_vertex))
        subgraph = graph.subgraph( vertices.union(set([node, center_vertex])) )
        for clique in filter(testfn, nx.find_cliques(subgraph)):
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
