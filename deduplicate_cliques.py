#
# Fourth step of the decoding finding pipeline. This one is serial. usage:
#  python deduplicate_cliques.py <basedir> <indir> <outdir>
#

import pickle, os, time, operator, sys

basedir = sys.argv[1]
indir   = sys.argv[2]
outdir  = sys.argv[3]

with open("cycles.pickle") as f:
  cycles = pickle.load(f)

def index(comb):
  return comb[1]+comb[0]*len(cycles)

result = {}
for fname in os.listdir("%s/%s/"%(basedir, indir)):
  with open("%s/%s/%s"%(basedir, indir, fname)) as f:
    cliques = pickle.load(f)
  for clique in cliques:
    if len(clique) not in result:
      result[len(clique)] = set()
    result[len(clique)].add(tuple(sorted(clique, key=index)))

print len(result)

for k, v in result.iteritems():
  with open("%s/%s/%d.pickle"%(basedir, outdir, k), "w") as f:
    pickle.dump(list(v), f)
