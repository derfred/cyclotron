#
# Sixth (and last) step of the decoding finding pipeline. usage:
#  python filter_connected_cliques.py <problem_def> <basedir> <max_len> <clique_size> <worker_index>
#

import pickle, sys, os, itertools, operator, collections, time
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
  for input, graph in graphs.iteritems():
    for choice in find_choice_points_for_graph(graph):
      result.add( (choice[0], choice[1], input) )
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

def build_decider(prefix):
  basedecider = InequalityDecider()
  basedecider.add_cycle_mapping(problem_def, cycle_mapping)
  for transition in prefix:
    basedecider.add_transition(*transition)
  return basedecider.freeze()

def build_parent_graphs(problem_def, cycle_mapping, decider):
  graphs = {}
  for result, inputs in problem_def.iteritems():
    my_cycles    = map(operator.itemgetter(1), filter(lambda a: a[0]==result, cycle_mapping))
    other_cycles = map(operator.itemgetter(1), filter(lambda a: a[0]!=result, cycle_mapping))

    all_states   = set(map(lambda s: string.join(s, ""), itertools.permutations(["a","a","b","b","c"])))
    other_states = all_states-set(itertools.chain(*my_cycles))
    for input in inputs:
      graph      = decider.build_transition_graph(my_cycles, other_states, input)
      # now mark the edges for my cycles as they dont need to be tested
      for cycle in my_cycles:
        for n, p in zip(cycle, cycle[1:]+cycle[:1]):
          graph[n][p]["cycle"] = True
      graphs[input] = graph
  return graphs

def potentially_connected_graphs(problem_def, cycle_mapping, parentgraphs, decider, extra_transition):
  graphs = {}
  for result, inputs in problem_def.iteritems():
    my_cycles    = map(operator.itemgetter(1), filter(lambda a: a[0]==result, cycle_mapping))
    other_cycles = map(operator.itemgetter(1), filter(lambda a: a[0]!=result, cycle_mapping))
    for input in inputs:
      graph = parentgraphs[input].copy()
      for n, p in graph.edges():
        if "cycle" not in graph[n][p] and not decider.satisfiable_with_transitions(set([extra_transition, (n, p, input)])):
          graph.remove_edge(n, p)

      for state in set(itertools.chain(*other_cycles)) - set(itertools.chain(*my_cycles)):
        if all( nx.has_path(graph, state, cycle[0]) == False for cycle in my_cycles ):
          return False
      graphs[input] = graph
  return graphs

found = 0
times = {}

def choose(cycle_mapping, effectives):
  global found, times
  queue        = collections.deque(map(lambda e: [e], effectives))
  level_size   = { 1: len(effectives) }
  impossibles  = collections.defaultdict(set)
  start        = time.time()

  decider      = build_decider([])
  prefix       = []
  parentgraphs = build_parent_graphs(problem_def, cycle_mapping, decider)
  while len(queue) > 0:
    chosen = queue.popleft()

    if len(chosen) > 1 and chosen[:-1] != prefix:
      decider     = build_decider(chosen[:-1])
      prefix      = chosen[:-1]
      parentgraphs = build_parent_graphs(problem_def, cycle_mapping, decider)

    # this code is for monitoring performance
    if len(chosen) not in level_size and len(chosen) > 1:
      print "checked  @", len(chosen)-1, level_size[len(chosen)-1]
      print "excluded @", len(chosen)-1, len(impossibles[len(chosen)-1])
      print "time     @", len(chosen)-1, (time.time()-start)/60
      times[len(chosen)-1] = (time.time()-start)/60
      start = time.time()
      level_size[len(chosen)] = 0
      with open("%s/status/%d/%d.pickle"%(basedir, clique_size, my_slice), "w") as f:
        pickle.dump((found, len(chosen), times), f)

    level_size[len(chosen)] += 1

    print tuple(map(lambda c: effectives.index(c), chosen))
    graphs = potentially_connected_graphs(problem_def, cycle_mapping, parentgraphs, decider, chosen[-1])
    if not graphs:
      impossibles[len(chosen)].add( frozenset(map(lambda c: effectives.index(c), chosen)) )
      continue

    choice_points = find_choice_points(graphs)

    if valid_solution(graphs, choice_points):
      yield chosen
      found += 1
      with open("%s/status/%d/%d.pickle"%(basedir, clique_size, my_slice), "w") as f:
        pickle.dump((found, len(chosen), times), f)
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
disconnected = list()

for i in xrange(len(cliques)):
  if i % total_slices == my_slice:
    clique        = cliques[i]
    print "starting %d %s"%(i, str(clique))
    cycle_mapping = map(lambda c: (c[0], tuple(cycles[c[1]])), clique)
    graphs        = potentially_connected(problem_def, cycle_mapping)
    connected     = False
    for chosen in choose(cycle_mapping, effective_choice_points(graphs)):
      print "have one"
      connected   = True
      result.append( (clique, chosen) )
      with open("%s/connected_cliques/%d/%d.pickle"%(basedir, clique_size, my_slice), "w") as f:
        pickle.dump(result, f)
    if not connected:
      disconnected.append(clique)
      with open("%s/disconnected_cliques/%d/%d.pickle"%(basedir, clique_size, my_slice), "w") as f:
        pickle.dump(disconnected, f)


with open("%s/connected_cliques/%d/%d.pickle"%(basedir, clique_size, my_slice), "w") as f:
  pickle.dump(result, f)

with open("%s/disconnected_cliques/%d/%d.pickle"%(basedir, clique_size, my_slice), "w") as f:
  pickle.dump(disconnected, f)
