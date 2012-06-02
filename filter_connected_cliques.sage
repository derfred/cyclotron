#
# Sixth (and last) step of the decoding finding pipeline. usage:
#  sage filter_connected_cliques.sage <problem_def> <basedir> <clique_size> <worker_index>
#

import pickle, sys, os, itertools, operator
from solution import Solution
from problem import *
from state import State
import networkx as nx

problem_def = read_problem_definition(sys.argv[1])
basedir     = sys.argv[2]
clique_size = int(sys.argv[3])

with open("cycles.pickle") as f:
  cycles = pickle.load(f)

total_slices = 399
my_slice     = int(sys.argv[4])

#with open("%s/unique_cliques/%d.pickle"%(basedir, clique_size)) as f:
 # cliques = pickle.load(f)

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

def build_targets_graph(cycle_mapping, my_cycles, input):
  graph = nx.DiGraph()
  for i in range(len(my_cycles)):
    graph.add_node("target%i"%i, target=True)

  for prev, next in find_possible_transitions(cycle_mapping, my_cycles, input):
    if next not in itertools.chain(*my_cycles):
      graph.add_edge(prev, next)
    else:
      for i in range(len(my_cycles)):
        if next in my_cycles[i]:
          graph.add_edge(prev, "target%i"%i)

  return graph

def transitions_from_cycle(cycle):
  return zip(cycle, cycle[1:]+cycle[:1])

def transitions_from_path(path):
  return zip(path, path[1:]+path[:1])[:-1]

def find_target_paths(graph, state, cycles):
  result = []
  nx.write_graphml(graph, "test.graphml")
  for target in filter(lambda n: "target" in n[1], graph.nodes(data=True)):
    path = nx.shortest_path(graph, state, target[0])
    if path:
      cycle = cycles[int(target[0].replace("target", ""))]
      result.append( path[:-1]+[find_cycle_target(path[-2], cycle)] )
  return result

def required_transitions(clique):
  cycle_mapping = map(lambda c: (c[0], cycles[c[1]]), clique)

  requirements = {}
  for result, inputs in problem_def.iteritems():
    my_cycles    = map(operator.itemgetter(1), filter(lambda a: a[0]==result, cycle_mapping))
    other_cycles = map(operator.itemgetter(1), filter(lambda a: a[0]!=result, cycle_mapping))
    for input in inputs:
      requirements[input] = []

      # first require the cycles to exist
      requirements[input].append([list(itertools.chain(*map(transitions_from_cycle, my_cycles)))])

      # next require a path from every other cycle state to one of the target cycles
      # if such a path does not exist for one of the states, this clique is not connected
      graph   = build_targets_graph(cycle_mapping, my_cycles, input)
      if graph.number_of_edges() == 0:
        return False

      origins = set(itertools.chain(*other_cycles)) - set(itertools.chain(*my_cycles))
      for paths in map(lambda s: find_target_paths(graph, s, my_cycles), origins):
        if len(paths) == 0:
          # for this state there is no conceivable path to a valid cycle for the current input
          return False
        else:
          requirements[input].append(map(transitions_from_path, paths))
  return requirements

def satisfiable_transitions(transitions):
  possibles = []
  for input, paths in transitions.iteritems():
    possibles.append( map(lambda p: (input, list(itertools.chain(*p))), itertools.product(*paths)) )
  for setup in itertools.product(*possibles):
    solution = Solution(problem_def)
    for input, paths in setup:
      for prev, next in paths:
        solution.add(prev, next, input)
    solution.solve()
    if solution.satisfiable():
      return True
  return False

def subcombine(clique, center_vertex=None):
  # dont remove the center vertex
  redundant_assignments = filter(lambda l: len(l) > 1, map(lambda r: filter(lambda a: a[0] == r and a != center_vertex, clique), problem_def.keys()))
  children              = list(itertools.chain(*map(lambda c: subcombine(clique-frozenset([c]), center_vertex), itertools.chain(*redundant_assignments))))
  # use list/set to remove duplicates
  return reversed(sorted(list(set([clique] + children)), key=len))


with open("392.pickle") as f:
  cliques = pickle.load(f)

output = set()

for i in xrange(len(cliques)):
  if i % total_slices == my_slice:
    clique        = cliques[i]
    print "starting %d %s"%(i, str(clique))
    for subclique in subcombine(clique):
      transitions = required_transitions(subclique)
      if transitions != False:
        print " is potentially connected %s"%str(subclique)
        if satisfiable_transitions(transitions):
          print "  got a winner %s"%str(subclique)
          output.add(subclique)
   

with open("%s/connected_cliques/%d/%d.pickle"%(basedir, clique_size, my_slice), "w") as f:
  pickle.dump(output, f)
