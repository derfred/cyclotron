#
# Fourth step of the decoding finding pipeline. This one is serial. usage:
#  python deduplicate_cliques.py <basedir>
#

import pickle, os, time, operator, sys

basedir = sys.argv[1]

result = {}
for fname in os.listdir("%s/cliques/"%basedir):
  with open("%s/cliques/%s"%(basedir, fname)) as f:
    cliques = pickle.load(f)
  for clique in cliques:
    if len(clique) not in result:
      result[len(clique)] = set()
    result[len(clique)].add(clique)

for k, v in result.iteritems():
  with open("%s/unique_cliques/%d.pickle"%(basedir, k), "w") as f:
    pickle.dump(list(v), f)
