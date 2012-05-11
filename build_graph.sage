#
# First step of the decoding finding pipeline. usage:
#  sage -python build_graphs.sage <problem_def> <basedir> <worker_index>
#

from state import State
from problem import *
from solution import Solution
import itertools, time, operator, sys, os, string, pickle

problem_def = read_problem_definition(sys.argv[1])
max_len     = int(sys.argv[3])

with open("cycles.pickle") as f:
  cycles = filter(lambda c: len(c) <= max_len, pickle.load(f))

# given two cycle mappings (result, cycle_index)
# can they be part of a valid decoding?
def cycles_compatible(left, right):
  if left[1] == right[1]:
    # same cycle, different inputs, this cannot be part of a consistent mapping
    return False
  elif len(set(cycles[left[1]]).intersection(set(cycles[right[1]]))) == 0:
    # disjoint cycles are always locally compatible
    return True
  elif left[0] == right[0]:
    # this is an adjoint cycle, it can only be compatible if the intersection of states is empty
    # therefore it is not compatible
    return False
  else:
    # there is some overlap, we need to evaluate pairwise consistency explicitly
    cycle_mapping = map(lambda c: (c[0], cycles[c[1]]), [left, right])
    solution      = Solution(problem_def, cycle_mapping)
    solution.solve()
    return solution.satisfiable()

def index(comb):
  return comb[0]+comb[1]*len(cycles)

all_combinations = list(itertools.product(problem_def.keys(), xrange(len(cycles))))
total_slices     = 399
basedir          = sys.argv[2]
my_slice         = int(sys.argv[4])

data = { "total_edges": 0 }

print "start"
for vertex in all_combinations:
  result = set()
  # only work on my slice
  if index(vertex) % total_slices == my_slice:
    for other in all_combinations:
      # graph is undirected, so would only need to evaluate in one direction
      # however distribution step, ie adding the neighbour to the other
      # nodes neighbour list is DEADDD SLOOOOOWWWWWW>>>
      if cycles_compatible(vertex, other):
        result.add(other)

    data["total_edges"] += len(result)
    if len(result) not in data:
      data[len(result)] = 0
    data[len(result)] += 1

    with open("%s/neighbours/%d-%d.pickle"%(basedir, vertex[0], vertex[1]), "w") as f:
      pickle.dump(result, f)

print "finish"
