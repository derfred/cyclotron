import itertools, string
import networkx as nx

left  = -1
right = 1

class State:
  left  = left
  right = right

  @staticmethod
  def generate_states():
    return map(State, set(map(lambda s: string.join(s, ""), itertools.permutations(["a","a","b","b","c"]))))

  @staticmethod
  def cycles():
    return nx.simple_cycles(State.graph)

  @staticmethod
  def grouped_cycles():
    result = {}

    for cycle in State.cycles():
      _cycle = cycle[0:-1]
      if len(_cycle) not in result:
        result[len(_cycle)] = []
      result[len(_cycle)].append(_cycle)

    return result

  def __init__(self, state):
    self.state = string.join(list(state), "")

  def __eq__(self, other):
    return self.state == other.state

  def __str__(self):
    return self.state

  def __hash__(self):
    return hash(self.state)

  def cluster_indices(self, cluster):
    result = []
    pos = self.state.find(cluster)
    while pos != -1:
      result.append(pos)
      pos = self.state.find(cluster, pos+1)
    return result

  def unstables(self):
    return self.cluster_indices("a")

  def transition(self, direction):
    unstables = self.cluster_indices("a")
    stables   = self.cluster_indices("b")
    singleton = self.cluster_indices("c")[0]

    result = range(len(self.state))
    result[singleton] = "b"
    for i in unstables:
      result[i] = "b"

    for i in stables:
      result[i] = "a"

    if direction == left:
      result[min(unstables)] = "c"
    elif direction == right:
      result[max(unstables)] = "c"

    return State(string.join(result, ""))

State.all_states = State.generate_states()

State.graph = nx.DiGraph()
for state in State.all_states:
  State.graph.add_node(state.state)

for state in State.all_states:
  left_out  = state.transition(left)
  right_out = state.transition(right)

  State.graph.add_edge(state.state, left_out.state)
  State.graph.add_edge(state.state, right_out.state)
