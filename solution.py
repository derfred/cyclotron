from state import State
import string, itertools
import matplotlib.pyplot as plt
import networkx as nx
from sage.all import *

from networkx.utils import *
from collections import defaultdict

def rotate(x, y=1):
   if len(x) == 0:
      return x
   y = y % len(x) # Normalize y, using modulo - even works for negative y
   
   return x[y:] + x[:y]

def simple_cycles(G):
    # Jon Olav Vik, 2010-08-09
    def _unblock(thisnode):
        """Recursively unblock and remove nodes from B[thisnode]."""
        if blocked[thisnode]:
            blocked[thisnode] = False
            while B[thisnode]:
                _unblock(B[thisnode].pop())
    
    def circuit(thisnode, startnode, component):
        closed = False # set to True if elementary path is closed
        path.append(thisnode)
        blocked[thisnode] = True
        for nextnode in component[thisnode]: # direct successors of thisnode
            if nextnode == startnode:
                result.append(path + [startnode])
                closed = True
            elif not blocked[nextnode]:
                if circuit(nextnode, startnode, component):
                    closed = True
        if closed:
            _unblock(thisnode)
        else:
            for nextnode in component[thisnode]:
                if thisnode not in B[nextnode]: # TODO: use set for speedup?
                    B[nextnode].append(thisnode)
        path.pop() # remove thisnode from path
        return closed
    
    path = [] # stack of nodes in current path
    blocked = defaultdict(bool) # vertex: blocked from search?
    B = defaultdict(list) # graph portions that yield no elementary circuit
    result = [] # list to accumulate the circuits found
    # Johnson's algorithm requires some ordering of the nodes.
    # They might not be sortable so we assign an arbitrary ordering.
    ordering=dict(zip(G,range(len(G))))
    for s in ordering:
        # Build the subgraph induced by s and following nodes in the ordering
        subgraph = G.subgraph(node for node in G 
                              if ordering[node] >= ordering[s])
        # Find the strongly connected component in the subgraph 
        # that contains the least node according to the ordering
        strongcomp = nx.strongly_connected_components(subgraph)
        mincomp=min(strongcomp, 
                    key=lambda nodes: min(ordering[n] for n in nodes))
        component = G.subgraph(mincomp)
        if component:
            # smallest node in the component according to the ordering
            startnode = min(component,key=ordering.__getitem__) 
            for node in component:
                blocked[node] = False
                B[node][:] = []
            dummy=circuit(startnode, startnode, component)

    return result

class Theta:
  def __init__(self, state):
    self.state = State(state)
    self.left  = []
    self.right = []

  def add(self, to, input):
    currents = map(lambda i: input[i], self.state.unstables())
    currents.reverse()

    if to == self.state.transition(State.left).state:
      if currents not in self.left:
        self.left.append(currents)
    elif to == self.state.transition(State.right).state:
      if currents not in self.right:
        self.right.append(currents)
    else:
      raise "hell"

  def add_constraints_to(self, program):
    for left in self.left:
      program.add_constraint( program[left[0]]-program[left[1]]+1 <= program["T"+self.state.state] )

    for right in self.right:
      program.add_constraint( program[right[0]]-program[right[1]]-1 >= program["T"+self.state.state] )

  def switch(self, input, params):
    currents = map(lambda i: params[input[i]], self.state.unstables())
    delta    = currents[1] - currents[0]
    boundary = params.get("T"+self.state.state, 0)

    if delta < boundary:
      return [self.state.transition(State.left)]
    elif delta > boundary:
      return [self.state.transition(State.right)]
    else:
      return [self.state.transition(State.left), self.state.transition(State.right)]

def part_of(cycle, allowed_cycles):
  for allowed_cycle in allowed_cycles:
    if len(cycle) == len(allowed_cycle):
      if any(map(lambda t: rotate(allowed_cycle, t) == cycle, xrange(len(cycle)))):
        return True
  return False

class Solution:
  def __init__(self, problem, decoding=[]):
    self.program = None

    self.problem  = problem
    self.decoding = decoding

    self.thetas = {}

    for result, cycle in decoding:
      for input in problem[result]:
        for state, to in zip(cycle, rotate(cycle)):
          self.add(state, to, input)

  def add(self, state, to, input):
    if state not in self.thetas:
      self.thetas[state] = Theta(state)

    self.thetas[state].add(to, input)

  def solve(self):
    self.program = MixedIntegerLinearProgram()
    for theta in self.thetas.values():
      theta.add_constraints_to(self.program)

    try:
      self.program.solve()
      self.consistent = True
    except Exception, e:
      self.consistent = False

  def solution(self):
    if self.program == None:
      raise Exception("need to call solve first")

    result = {}
    for theta in self.thetas.itervalues():
      result["T"+theta.state.state] = self.program.get_values(self.program["T"+theta.state.state])

      for l, r in theta.left+theta.right:
        result[l] = self.program.get_values(self.program[l])
        result[r] = self.program.get_values(self.program[r])

    return result

  def satisfiable(self):
    if self.program == None:
      raise Exception("need to call solve first")

    return self.consistent

  def transition_graph(self, input):
    params = self.solution()
    result = nx.DiGraph()
    for theta in self.thetas.itervalues():
      for out in theta.switch(input, params):
        result.add_edge(theta.state.state, out.state)
    return result

  def verifies(self):
    if not self.satisfiable():
      raise Exception("this solution is not satisfiable")

    for result, inputs in self.problem.iteritems():
      allowed_cycles = map(operator.itemgetter(1), filter(lambda a: a[0] == result, self.decoding))
      for input in inputs:
        G = self.transition_graph(input)

        actual_cycles = map(lambda c: c[0:-1], simple_cycles(G))
        for cycle in actual_cycles:
          if not part_of(cycle, allowed_cycles):
            return False

    # for now...
    return True
