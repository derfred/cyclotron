#
# Sixth (and last) step of the decoding finding pipeline. usage:
#  python filter_connected_cliques.py <problem_def> <basedir> <max_len> <clique_size> <worker_index>
#

import pickle, sys, os, itertools, operator
from inequality_decider import InequalityDecider
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

def find_possible_transitions(decider, my_cycles, input):
  all_states = set(map(lambda s: string.join(s, ""), itertools.permutations(["a","a","b","b","c"])))
  for state in all_states-set(itertools.chain(*my_cycles)):
    for out_state in State.graph[state]:
      if decider.satisfiable_with_transition(state, out_state, input):
        yield (state, out_state)

def build_transition_graph(decider, my_cycles, input):
  graph = nx.DiGraph()
  for cycle in my_cycles:
    for prev, next in zip(cycle, cycle[1:]+cycle[:1]):
      graph.add_edge(prev, next)

  for prev, next in find_possible_transitions(decider, my_cycles, input):
    graph.add_edge(prev, next)

  return graph

def potentially_connected(clique):
  graphs = {}
  cycle_mapping = map(lambda c: (c[0], tuple(cycles[c[1]])), clique)

  base_decider = InequalityDecider()
  base_decider.add_cycle_mapping(problem_def, cycle_mapping)
  decider      =  base_decider.freeze()

  for result, inputs in problem_def.iteritems():
    my_cycles    = tuple(map(operator.itemgetter(1), filter(lambda a: a[0]==result, cycle_mapping)))
    other_cycles = map(operator.itemgetter(1), filter(lambda a: a[0]!=result, cycle_mapping))
    for input in inputs:
      graph = build_transition_graph(decider, my_cycles, input)
      if graph.number_of_edges() == 0:
        return False

      graphs[(result, input, my_cycles)] = graph
      for state in set(itertools.chain(*other_cycles)) - set(itertools.chain(*my_cycles)):
        if all( nx.has_path(graph, state, cycle[0]) == False for cycle in my_cycles ):
          return False
  return graphs


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
      graphs = potentially_connected(subclique)
      if graphs:
        print " is potentially connected %s"%str(subclique)
        potentially.add(tuple(sorted(subclique, key=index)))

with open("%s/potentially_connected_cliques/%d/%d.pickle"%(basedir, clique_size, my_slice), "w") as f:
  pickle.dump(potentially, f)
