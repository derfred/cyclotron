#
# Sixth (and last) step of the decoding finding pipeline. usage:
#  sage filter_connected_cliques.sage <problem_def> <basedir> <max_len> <clique_size> <worker_index>
#

import pickle, sys, os, itertools, operator
from solution import *
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

def find_cycle_target(state, cycle):
  _state = State(state)
  for dir in  [State.left, State.right]:
    out_state = _state.transition(dir).state
    if out_state in cycle:
      return out_state
  print "fail", state, cycle
  asd

def find_possible_transitions(cycle_mapping, my_cycles, input):
  all_states = set(map(lambda s: string.join(s, ""), itertools.permutations(["a","a","b","b","c"])))
  for state in all_states-set(itertools.chain(*my_cycles)):
    for out_state in State.graph[state]:
      solution = Solution(problem_def, cycle_mapping)
      solution.add(state, out_state, input)
      solution.solve()
      if solution.satisfiable():
        yield (state, out_state)

def build_transition_graph(cycle_mapping, my_cycles, input):
  graph = nx.DiGraph()
  for cycle in my_cycles:
    for prev, next in zip(cycle, cycle[1:]+cycle[:1]):
      graph.add_edge(prev, next)

  for prev, next in find_possible_transitions(cycle_mapping, my_cycles, input):
    graph.add_edge(prev, next)

  return graph

def potentially_connected(clique):
  graphs = {}
  cycle_mapping = map(lambda c: (c[0], tuple(cycles[c[1]])), clique)
  for result, inputs in problem_def.iteritems():
    my_cycles    = tuple(map(operator.itemgetter(1), filter(lambda a: a[0]==result, cycle_mapping)))
    other_cycles = map(operator.itemgetter(1), filter(lambda a: a[0]!=result, cycle_mapping))
    for input in inputs:
      graph = build_transition_graph(cycle_mapping, my_cycles, input)
      if graph.number_of_edges() == 0:
        return False

      graphs[(result, input, my_cycles)] = graph
      for state in set(itertools.chain(*other_cycles)) - set(itertools.chain(*my_cycles)):
        if all( nx.shortest_path(graph, state, cycle[0]) == False for cycle in my_cycles ):
          return False
  return graphs


def remove_cycles(graph, my_cycles):
  def potential_cycles_match(graph, expected_cycles):
    # ordering doesn't matter in this comparison, as it is implied by the structure of the state graph
    return set(map(lambda c: frozenset(c[:-1]), simple_cycles(graph))) == set(map(frozenset, expected_cycles))

  def next_transition_to_remove(graph, my_cycles):
    def non_essential(transition, cycles, graph):
      _graph = graph.copy()
      _graph.remove_edge(*transition)
      return any( nx.shortest_path(_graph, transition[0], cycle[0]) for cycle in cycles )

    # first build list of possible transitions to remove
    transitions = list(itertools.chain(*map(lambda n: map(lambda nn: (n, nn), graph[n]), filter(lambda n: len(graph[n]) == 2, graph))))

    # if there are no transitions....
    if len(transitions) == 0:
      return

    # now the magic happens
    spurious_cycles = set(filter(lambda c: c not in my_cycles, map(lambda c: tuple(c[:-1]), simple_cycles(graph))))
    transitions = filter(lambda t: non_essential(t, my_cycles, graph), transitions)
    return sorted(transitions, key=lambda t: len(filter(lambda c: t[0] in c, spurious_cycles)), reverse=True)[0]

  def opposite_of(transition):
    return (transition[0], list(set(State.graph[transition[0]].keys())-set([transition[1]]))[0])

  while not potential_cycles_match(graph, my_cycles):
    to_remove = next_transition_to_remove(graph, my_cycles)
    if to_remove == None:
      # if this clique is potentially connected, we should never get here
      raise "failed"
    yield opposite_of(to_remove)
    graph.remove_edge(*to_remove)

def connected(graphs):
  solution = Solution(problem_def)
  for setup, graph in graphs.iteritems():
    for cycle in setup[2]:
      for prev, next in zip(cycle, cycle[1:]+cycle[:1]):
        solution.add(prev, next, setup[1])

    for prev, next in remove_cycles(graph, setup[2]):
      solution.add(prev, next, setup[1])

  solution.solve()
  return solution.satisfiable()


def subcombine(clique, center_vertex=None):
  # dont remove the center vertex
  redundant_assignments = filter(lambda l: len(l) > 1, map(lambda r: filter(lambda a: a[0] == r and a != center_vertex, clique), problem_def.keys()))
  children              = list(itertools.chain(*map(lambda c: subcombine(clique-frozenset([c]), center_vertex), itertools.chain(*redundant_assignments))))
  # use list/set to remove duplicates
  return sorted(list(set([clique] + children)), key=len, reverse=True)

total_slices = 399
my_slice     = int(sys.argv[5])

output = set()

for i in xrange(len(cliques)):
  if i % total_slices == my_slice or True:
    clique        = cliques[i]
    print "starting %d %s"%(i, str(clique))
    for subclique in subcombine(clique):
      graphs = potentially_connected(subclique)
      if graphs:
        print " is potentially connected %s"%str(subclique)
        if connected(graphs):
          print "  got a winner %s"%str(subclique)
          output.add(subclique)

with open("%s/connected_cliques/%d/%d.pickle"%(basedir, clique_size, my_slice), "w") as f:
  pickle.dump(output, f)
