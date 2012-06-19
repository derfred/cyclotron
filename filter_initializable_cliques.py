#
# Sixth (and last) step of the decoding finding pipeline. usage:
#  python filter_initializable_cliques.py <problem_def> <basedir> <max_len> <clique_size> <worker_index>
#

import pickle, sys, os, itertools, operator
from inequality_decider import InequalityDecider
from problem import *
from state import State

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

total_slices = 399
my_slice     = int(sys.argv[5])

def build_potential_graphs(cycle_mapping):
  graphs = {}
  decider = InequalityDecider()
  decider.add_cycle_mapping(problem_def, cycle_mapping)
  for result, inputs in problem_def.iteritems():
    my_cycles    = tuple(map(operator.itemgetter(1), filter(lambda a: a[0]==result, cycle_mapping)))
    other_cycles = map(operator.itemgetter(1), filter(lambda a: a[0]!=result, cycle_mapping))

    all_states   = set(map(lambda s: string.join(s, ""), itertools.permutations(["a","a","b","b","c"])))
    other_states = all_states-set(itertools.chain(*my_cycles))
    for input in inputs:
      graphs[input] = (decider.build_transition_graph(my_cycles, other_states, input), my_cycles[0][0])
  return graphs

result = list()

for i in xrange(len(cliques)):
  if i % total_slices == my_slice:
    clique        = cliques[i]
    print "starting %d %s"%(i, str(clique))
    if decider.satisfiable():
      graphs      = build_potential_graphs(decider, cycle_mapping)

      good_states = list()
      for state in set(map(lambda s: string.join(s, ""), itertools.permutations(["a","a","b","b","c"]))):
        for input, graph_plus in graphs.iteritems():
          path = nx.shortest_path(graph_plus[0], state, graph_plus[1])
          for f, t in zip(path[:-1], path[1:]):
            decider.add_transition(f, t, input)

        if decider.satisfiable():
          good_states.append(state)

      if len(good_states) > 0:
        result.append( (clique, good_states) )

with open("%s/initializable_cliques/%d/%d.pickle"%(basedir, clique_size, my_slice), "w") as f:
  pickle.dump(result, f)
