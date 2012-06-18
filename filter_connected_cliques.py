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

def same_cycles(cycle1, cycle2):
  if len(cycle1) != len(cycle2):
    return False

  for i in xrange(len(cycle1)):
    if cycle1[i:] + cycle1[:i] == cycle2:
      return True
  return False

def filter_cycles(all_cycles, remove):
  result = []
  for cycle in all_cycles:
    if not any(same_cycles(my_cycle, tuple(cycle[:-1])) for my_cycle in remove):
      result.append(cycle)
  return result

def find_choice_points_for_graph(graph):
  result = set()
  for node in graph.nodes_iter():
    if len(graph.successors(node)) == 2:
      for succ in graph.successors(node):
        result.add( (node, succ) )
  return result

def find_choice_points(graphs):
  result = set()
  for data, graph in graphs.iteritems():
    for choice in find_choice_points_for_graph(graph):
      result.add( (choice[0], choice[1], data[1]) )
  return result

def find_effective_choice_points(graph, my_cycles):
  other_cycles  = filter_cycles(nx.simple_cycles(graph), my_cycles)
  result  = []
  for choice in find_choice_points_for_graph(graph):
    total = 0
    for cycle in other_cycles:
      if choice[0] in cycle and choice not in zip(cycle, cycle[1:]+cycle[:1]):
        total += 1
    result.append( (total, choice) )
  return result

def effective_choice_points(graphs):
  result = []
  for data, graph in graphs.iteritems():
    for uses, choice in find_effective_choice_points(graph, data[2]):
      result.append( (uses, (choice[0], choice[1], data[1])) )
  return map(operator.itemgetter(1), sorted(result, key=operator.itemgetter(0), reverse=True))


def excluded(impossibles, choice):
  for d in sorted(impossibles.keys()):
    if d < 5 and d < len(choice):
      for impossible in impossibles[d]:
        if frozenset(choice) < impossible:
          return True
  return False

def valid_solution(graphs, choice_points):
  # since the target cycles are always present, if the total number of cycles in the
  # graph is equal to the number of target cycles, there are no other invalid cycles
  if all(len(data[2]) == len(nx.simple_cycles(graph)) for data, graph in graphs.iteritems()):
    # this setup only exhibits valid cycles, even though its not fully determined
    # thats also a valid result
    return True

  if len(choice_points) == 0:
    # the system is fully determined and its still connected
    # this should be a winner!
    return True
  return False

def choose(effectives):
  queue       = collections.deque(map(lambda e: [e], effectives))
  level_size  = { 1: len(effectives) }
  impossibles = collections.defaultdict(set)
  start       = time.time()
  while len(queue) > 0:
    chosen = queue.popleft()

    # print tuple(map(lambda c: effectives.index(c), chosen))

    if len(chosen) not in level_size and len(chosen) > 1:
      print "checked  @", len(chosen)-1, level_size[len(chosen)-1]
      print "excluded @", len(chosen)-1, len(impossibles[len(chosen)-1])
      print "time     @", len(chosen)-1, (time.time()-start)/60
      start = time.time()
      level_size[len(chosen)] = 0

    level_size[len(chosen)] += 1

    graphs = potentially_connected(problem_def, cycle_mapping, chosen)
    if not graphs:
      impossibles[len(chosen)].add( frozenset(map(lambda c: effectives.index(c), chosen)) )
      continue

    choice_points = find_choice_points(graphs)

    if valid_solution(graphs, choice_points):
      yield chosen
      continue

    for choice in effectives:
      if choice not in choice_points and choice not in chosen and effectives.index(choice) < effectives.index(chosen[-1]):
        impossibles[len(chosen)+1].add( frozenset(map(lambda c: effectives.index(c), chosen)+[effectives.index(choice)]) )

    for choice in choice_points:
      if choice in effectives and effectives.index(choice) < effectives.index(chosen[-1]) and not excluded(impossibles, choice):
        queue.append( chosen+[choice] )


total_slices = 399
my_slice     = int(sys.argv[5])

result       = list()

for i in xrange(len(cliques)):
  if i % total_slices == my_slice:
    clique        = cliques[i]
    print "starting %d %s"%(i, str(clique))
    cycle_mapping = map(lambda c: (c[0], tuple(cycles[c[1]])), clique)
    graphs        = potentially_connected(problem_def, cycle_mapping)
    for chosen in choose(effective_choice_points(graphs)):
      print "have one"
      result.append( (clique, chosen) )
      with open("%s/connected_cliques/%d/%d.pickle"%(basedir, clique_size, my_slice), "w") as f:
        pickle.dump(result, f)

with open("%s/connected_cliques/%d/%d.pickle"%(basedir, clique_size, my_slice), "w") as f:
  pickle.dump(result, f)
