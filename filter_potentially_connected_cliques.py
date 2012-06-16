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

with open("%s/unique_cliques/%d.pickle"%(basedir, clique_size)) as f:
  cliques = pickle.load(f)

def index(comb):
  return comb[1]+comb[0]*len(cycles)

def subcombine(clique, center_vertex=None):
  # dont remove the center vertex
  redundant_assignments = filter(lambda l: len(l) > 1, map(lambda r: filter(lambda a: a[0] == r and a != center_vertex, clique), problem_def.keys()))
  children              = list(itertools.chain(*map(lambda c: subcombine(frozenset(clique)-frozenset([c]), center_vertex), itertools.chain(*redundant_assignments))))
  # use list/set to remove duplicates
  return sorted(list(set([clique] + children)), key=len, reverse=True)

total_slices = 399
my_slice     = int(sys.argv[5])

potentially = set()

for i in xrange(len(cliques)):
  if i % total_slices == my_slice:
    clique        = cliques[i]
    print "starting %d %s"%(i, str(clique))
    for subclique in subcombine(clique):
      cycle_mapping = map(lambda c: (c[0], tuple(cycles[c[1]])), subclique)
      graphs        = potentially_connected(problem_def, cycle_mapping)
      if graphs:
        print " is potentially connected %s"%str(subclique)
        potentially.add(tuple(sorted(subclique, key=index)))

with open("%s/potentially_connected_cliques/%d/%d.pickle"%(basedir, clique_size, my_slice), "w") as f:
  pickle.dump(potentially, f)
