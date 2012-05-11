#
# Fifth (and last) step of the decoding finding pipeline. usage:
#  sage -python filter_cliques.sage <problem_def> <basedir> <clique_size> <worker_index>
#
import sys, os

basedir = sys.argv[2]
clique_size  = int(sys.argv[3])

## when this job gets queued, nothing is known about the size of cliques
## therefore we might get started for a clique size that does not exist
## so just exit gracefully if that is the case
if not os.path.exists("%s/unique_cliques/%d.pickle"%(basedir, clique_size)):
  sys.exit(0)

## real program starts here
import pickle
from solution import Solution
from problem import *

problem_def = read_problem_definition(sys.argv[1])

with open("cycles.pickle") as f:
  cycles = pickle.load(f)

total_slices = 399
my_slice     = int(sys.argv[4])

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

if not os.path.exists("%s/filtered_cliques/%d/"%(basedir, clique_size)):
  os.mkdir("%s/filtered_cliques/%d/"%(basedir, clique_size))

with open("%s/filtered_cliques/%d/%d.pickle"%(basedir, clique_size, my_slice), "w") as f:
  pickle.dump(result, f)
