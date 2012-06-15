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
  return tuple(map(operator.itemgetter(1), sorted(term, key=operator.itemgetter(1))))

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

class InequalityStore:
  # override this in subclasses
  def add(self, ineq):
    raise Exception("not implemented")

  def add_transition(self, prev, next, input):
    self.add(extract_inequality(prev, next, input))

  def add_cycle(self, problem, result, cycle):
    for input in problem[result]:
      for state, to in zip(cycle, cycle[1:] + cycle[:1]):
        self.add(state, to, input)

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
    self.inequalities = nx.Graph()

  def add(self, ineq):
    for other in self.inequalities.nodes():
      if trivially_inconsistent(other, ineq):
        # this is a trivial inconsistency, no need to proceed
        self.inequalities.add_edge(ineq, other, relation="conflicting")
      else:
        # no trivial inconsistency detected
        constraint = constrained_variable(ineq, other)
        if constraint:
          # these two inequalities share two variables in such a way 
          # that they imply an inequality between two other variables
          self.inequalities.add_edge(ineq, other, relation="constraining", constraint=constraint)
        else:
          # now check if this relation could imply a constraint if a constraint of the
          # previous kind were added
          potential_constraints = potentially_constrained_variables(ineq, other)
          if potential_constraints:
            print potential_constraints
            self.inequalities.add_edge(ineq, other, relation="potentially_constraining", potential_constraints=potential_constraints)

    # finally in case these this inequality does not interact at all
    self.inequalities.add_node(ineq)

  def _edges_by_relation(self, relation):
    return filter(lambda e: self.inequalities.edge[e[0]][e[1]]['relation'] == relation, self.inequalities.edges_iter())

  def _construct_graph(self):
    def add_inequalities(graph, ineq, potentials):
      if ineq in potentials:
        pass

    result = nx.DiGraph()

    # first extract first level implied inequalities
    for n1, n2 in self._edges_by_relation("constraining"):
      high, low = self.inequalities.edge[n1][n2]['constraint']
      result.add_edge(high, low)

    # cache potential constraints for later
    second_level = collections.defaultdict(set)
    for potential in self._edges_by_relation("potentially_constraining"):
      for k, v in potential['potential_constraints'].iteritems():
        second_level[k].add(v)

    # now recursively add inequalities from those implied by the first level
    for ineq in inequalities_from_graph(result):
      add_inequalities(result, ineq, second_level)

    return result

  def satisfiable(self):
    if len(self._edges_by_relation('conflicting')) > 0:
      return False

    param_dependencies = self._construct_graph()
    return True

decider = NewInequalityDecider()

decider.add("baabc", "acbab", ("I", "B2", "B3", "I", "I"))
decider.add("baabc", "abcab", ("I", "B2", "A3", "I", "I"))

decider.add("ababc", "cabab", ("A1", "I", "A3", "I", "I"))
decider.add("ababc", "bacab", ("B1", "I", "B3", "I", "I"))



print decider.satisfiable()

# h = nx.to_agraph(decider._construct_graph())
h = nx.to_agraph(decider.inequalities)
h.draw("q.png", prog="dot")
