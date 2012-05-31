#
# Fifth (and last) step of the decoding finding pipeline. usage:
#  sage -python filter_cliques.sage <problem_def> <basedir> <clique_size> <worker_index>
#
import pickle, sys, os
from solution import Solution
from problem import *

problem_def = read_problem_definition(sys.argv[1])
basedir     = sys.argv[2]
max_len     = int(sys.argv[3])
clique_size = int(sys.argv[4])

with open("cycles.pickle") as f:
  cycles = filter(lambda c: len(c) <= max_len, pickle.load(f))

total_slices = 399
my_slice     = int(sys.argv[5])

with open("%s/unique_cliques/%d.pickle"%(basedir, clique_size)) as f:
  cliques = pickle.load(f)

result = []
for i in xrange(len(cliques)):
  if i % total_slices == my_slice:
    print "starting %d"%i
    clique        = cliques[i]
    cycle_mapping = map(lambda c: (c[0], cycles[c[1]]), clique)
    solution      = Solution(problem_def, cycle_mapping)
    solution.solve()

    if solution.verifies():
      print " found one!"
      result.append(clique)

with open("%s/filtered_cliques/%d/%d.pickle"%(basedir, clique_size, my_slice), "w") as f:
  pickle.dump(result, f)
