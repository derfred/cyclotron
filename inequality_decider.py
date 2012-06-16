import itertools, string, operator, collections
from state import State
import networkx as nx

def extract_inequality(prev, next, input):
  state = State(prev)
  currents = list(reversed(map(lambda i: input[i], state.unstables())))

  if next == state.transition(State.left).state:
    return ( (-1, currents[0]), (1, currents[1]), (1, prev) )
  elif next == state.transition(State.right).state:
    return ( (1, currents[0]), (-1, currents[1]), (-1, prev) )

def sortedtuple(term):
  return tuple(map(operator.itemgetter(1), sorted(term, key=operator.itemgetter(0), reverse=True)))

def trivially_inconsistent(ineq1, ineq2):
  return all(l[0] == -1*r[0] and l[1] == r[1] for l, r in zip(ineq1, ineq2))

def constrained_variable(ineq1, ineq2):
  # for these two inequalitites to imply a constraint there have to be exactly two terms of opposite sign
  opposites      = (not (l[0] == -1*r[0] and l[1] == r[1]) for l, r in zip(ineq1, ineq2))
  free_variables = list(itertools.compress(zip(ineq1, ineq2), opposites))
  if len(free_variables) != 1:
    return
  # return format is (A > B)
  return sortedtuple(free_variables[0])

def potentially_constrained_variables(ineq1, ineq2):
  def invert(ineq):
    return sortedtuple(map(lambda t: (-1*t[0], t[1]), ineq))

  opposites      = (not (l[0] == -1*r[0] and l[1] == r[1]) for l, r in zip(ineq1, ineq2))
  free_variables = list(itertools.compress(zip(ineq1, ineq2), opposites))

  # for potential constraints, we need exactly one shared variable of opposite sign
  # and therefore exactly two free variables
  if len(free_variables) != 2:
    return

  left, right = free_variables
  return { invert(left): sortedtuple(right), invert(right): sortedtuple(left) }

def identify_relations(existing, ineq):
  trivials              = set()
  constraints           = set()
  potential_constraints = collections.defaultdict(set)
  for other in existing:
    if trivially_inconsistent(other, ineq):
      # this is a trivial inconsistency, no need to proceed
      trivials.add( (other, ineq) )
    else:
      # no trivial inconsistency detected
      constraint = constrained_variable(ineq, other)
      if constraint:
        # these two inequalities share two variables in such a way 
        # that they imply an inequality between two other variables
        constraints.add( constraint )
      else:
        # now check if this relation could imply a constraint if a constraint of the
        # previous kind were added
        potentials = potentially_constrained_variables(ineq, other)
        if potentials:
          for k, v in potentials.iteritems():
            potential_constraints[k].add(v)
  return (trivials, constraints, potential_constraints)

class InequalityStore:
  # override this in subclasses
  def add(self, ineq):
    raise Exception("not implemented")

  def add_transition(self, prev, next, input):
    self.add(extract_inequality(prev, next, input))

  def add_cycle(self, problem, result, cycle):
    for input in problem[result]:
      for state, to in zip(cycle, cycle[1:] + cycle[:1]):
        self.add_transition(state, to, input)

  def add_cycle_mapping(self, problem, mapping):
    for result, cycle in mapping:
      self.add_cycle(problem, result, cycle)

class InequalityPrinter(InequalityStore):
  def __init__(self):
    self.ineqs = set()

  def add(self, ineq):
    self.ineqs.add(ineq)

  def print_mathematica(self):
    def escape(param):
      # Mathematica doesnt like I
      return param.replace("I", "J")
    params = set()
    result = set()
    for ineq in self.ineqs:
      params.add(escape(ineq[0][1]))
      params.add(escape(ineq[1][1]))
      params.add(escape(ineq[2][1]))

      result.add("(%d)*%s + (%d)*%s + (%d)*%s > 0"%(ineq[0][0], escape(ineq[0][1]), ineq[1][0], escape(ineq[1][1]), ineq[2][0], escape(ineq[2][1])))

    print "FindInstance[%s, {%s}, Reals]"%(string.join(result, "&&"), string.join(params, ","))

class InequalityDecider(InequalityStore):
  def __init__(self):
    self.ineqs                 = set()
    self.trivials              = set()
    self.constraints           = set()
    self.potential_constraints = collections.defaultdict(set)

  def identify_relations(self, ineq):
    return identify_relations(self.ineqs, ineq)

  def add(self, ineq):
    trivials, constraints, potential_constraints = self.identify_relations(ineq)

    self.trivials.update(trivials)
    self.constraints.update(constraints)
    for k, v in potential_constraints:
      self.potential_constraints[k].update(v)

    self.ineqs.add(ineq)

  def _construct_graph(self):
    result = nx.DiGraph()

    # go through each first level constraint, add an edge for it
    # then check whether those edges imply a second level constraint
    for constraint in self.constraints:
      result.add_edge(*constraint)
      if constraint in self.potential_constraints:
        for high, low in self.potential_constraints[constraint]:
          result.add_edge(high, low)

    # TODO: check whether the previous step needs to be done recursively
    # ie. check for potential constraints that become active because
    # of the activation of other potential constraints (are there levels higher than 2??)

    return result

  def satisfiable(self):
    if len(self.trivials) > 0:
      return False

    return nx.is_directed_acyclic_graph(self._construct_graph())

  def freeze(self):
    return FrozenDecider(self)

class FrozenDecider:
  def __init__(self, parent):
    self.parent = parent
    self.graph  = parent._construct_graph()

  def satisfiable_with_transition(self, prev, next, input):
    ineq = extract_inequality(prev, next, input)
    trivials, constraints, potential_constraints = self.parent.identify_relations(ineq)

    if len(trivials) > 0:
      return False

    graph = self.graph.copy()

    for constraint in constraints:
      graph.add_edge(*constraint)

    for k, constraints in potential_constraints.iteritems():
      if k[0] in graph and k[1] in graph and nx.has_path(graph, *k):
        for constraint in constraints:
          graph.add_edge(*constraint)

    return nx.is_directed_acyclic_graph(graph)

  def find_possible_transitions(self, in_states, input):
    for state in in_states:
      for out_state in State.graph[state]:
        if self.satisfiable_with_transition(state, out_state, input):
          yield (state, out_state)

  def build_transition_graph(self, my_cycles, in_states, input):
    graph = nx.DiGraph()
    for cycle in my_cycles:
      for prev, next in zip(cycle, cycle[1:]+cycle[:1]):
        graph.add_edge(prev, next)

    for prev, next in self.find_possible_transitions(in_states, input):
      graph.add_edge(prev, next)

    return graph

def potentially_connected(problem_def, cycle_mapping, additionals=[], shortcut=True):
  graphs = {}

  base_decider = InequalityDecider()
  base_decider.add_cycle_mapping(problem_def, cycle_mapping)
  for transition in additionals:
    base_decider.add_transition(*transition)
  decider      =  base_decider.freeze()

  for result, inputs in problem_def.iteritems():
    my_cycles    = tuple(map(operator.itemgetter(1), filter(lambda a: a[0]==result, cycle_mapping)))
    other_cycles = map(operator.itemgetter(1), filter(lambda a: a[0]!=result, cycle_mapping))

    all_states   = set(map(lambda s: string.join(s, ""), itertools.permutations(["a","a","b","b","c"])))
    other_states = all_states-set(itertools.chain(*my_cycles))
    for input in inputs:
      graph      = decider.build_transition_graph(my_cycles, other_states, input)
      if shortcut and graph.number_of_edges() == 0:
        return False

      graphs[(result, input, my_cycles)] = graph
      for state in set(itertools.chain(*other_cycles)) - set(itertools.chain(*my_cycles)):
        if shortcut and all( nx.has_path(graph, state, cycle[0]) == False for cycle in my_cycles ):
          return False
  return graphs
