import itertools, string, operator
from state import State
import networkx as nx

def extract_inequality(prev, next, input):
  state = State(prev)
  currents = list(reversed(map(lambda i: input[i], state.unstables())))

  if next == state.transition(State.left).state:
    return ( (-1, currents[0]), (1, currents[1]), (1, prev) )
  elif next == state.transition(State.right).state:
    return ( (1, currents[0]), (-1, currents[1]), (-1, prev) )

def opposite(pair):
  return ( (-1*pair[0][0], pair[0][1]), (-1*pair[1][0], pair[1][1]) )

def make_pairs(ineq):
  for m1, m2, s in [ (0,1,2), (1,2,0), (2,0,1) ]:
    yield ( (ineq[m1], ineq[m2]), ineq[s] )

class InequalityDecider:
  def __init__(self):
    self.pairs = {}

  def add(self, prev, next, input):
    ineq = extract_inequality(prev, next, input)
    for p, s in make_pairs(ineq):
      if p not in self.pairs:
        self.pairs[p] = set()
      self.pairs[p].add(s)

  def add_cycle(self, problem, result, cycle):
    for input in problem[result]:
      for state, to in zip(cycle, cycle[1:] + cycle[:1]):
        self.add(state, to, input)

  def add_cycle_mapping(self, problem, mapping):
    for result, cycle in mapping:
      self.add_cycle(problem, result, cycle)

  def _construct_graph(self):
    graph = nx.DiGraph()
    for markers, variables in self.pairs.iteritems():
      other = opposite(markers)
      if other in self.pairs:
        for s1, s2 in itertools.product( variables, self.pairs[other] ):
          low, high = map(operator.itemgetter(1), sorted([s1, s2], key=operator.itemgetter(0)))
          graph.add_edge(high, low)
    return graph

  def freeze(self):
    return FrozenDecider(self._construct_graph(), self.pairs)

  def satisfiable(self):
    graph = self._construct_graph()
    return nx.is_directed_acyclic_graph(graph)

class FrozenDecider:
  def __init__(self, graph, pairs):
    self.graph       = graph
    self.pairs       = pairs
    self.satisfiable = nx.is_directed_acyclic_graph(graph)

  def satisfiable_with(self, prev, next, input):
    # if base solution is not satisfiable, adding a constraint cannot make it satisfiable
    if not self.satisfiable:
      return False

    ineq = extract_inequality(prev, next, input)

    # first check if this causes a trivial inconsistency
    opposite_marker   = opposite( (ineq[0], ineq[1]) )
    opposite_variable = (-1*ineq[2][0], ineq[2][1])
    if opposite_marker in self.pairs and opposite_variable in self.pairs[opposite_marker]:
      return False

    # now check if adding this would cause a loop in the implied inequalities
    for p, s in make_pairs(ineq):
      other = opposite(p)
      if other in self.pairs:
        for s2 in self.pairs[other]:
          low, high = map(operator.itemgetter(1), sorted([s, s2], key=operator.itemgetter(0)))
          if low in self.graph and len(self.graph[low]) > 0 and nx.has_path(self.graph, low, high):
            return False
    return True
