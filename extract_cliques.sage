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

result = []

total_slices = 399
basedir      = sys.argv[2]
my_slice     = int(sys.argv[4])

for vertex in itertools.product(problem_def.keys(), xrange(len(cycles))):
  if index(vertex) % total_slices == my_slice:
    graph = nx.read_gpickle("%s/pruned_graphs/%d-%d.gpickle.bz2"%(basedir, vertex[0], vertex[1]))
    print "processing %s (%d nodes)"%(str(vertex), len(graph))

    try:
      for clique in filter(valid_decoding, nx.cliques_containing_node(graph, vertex)):
        print " is valid %s"%str(clique)
        cycle_mapping = map(lambda c: (c[0], cycles[c[1]]), clique)
        solution      = Solution(problem_def, cycle_mapping)
        solution.solve()
        if solution.satisfiable():
          print "  is consistent"
          result.append(clique)
    except MemoryError, e:
      sys.stderr.write("Failed because of insufficient memory on problem: %s\n"%sys.argv[1])
      sys.stderr.write(" found so far: %d\n"%len(result))
      sys.stderr.write(" max_len: %d\n"%max_len)
      sys.stderr.write(" my_slice: %d\n"%my_slice)
      sys.stderr.write(" basedir: %s\n"%basedir)
      sys.stderr.write(" vertex: %s"%str(vertex))
      sys.exit(127)

with open("%s/cliques/%d.pickle"%(basedir, my_slice), "w") as f:
  pickle.dump(result, f)
