#
# Fourth step of the decoding finding pipeline. This one is serial. usage:
#  python collate_potentially_connected.py <basedir>
#

import pickle, os, time, operator, sys, fnmatch, collections

basedir = sys.argv[1]

def index(comb):
  return comb[1]+comb[0]*len(cycles)

all_files = collections.defaultdict(set)
for path, dirs, files in os.walk(os.path.abspath("%s/collated_potentially_connected_cliques"%basedir)):
  for filename in fnmatch.filter(files, "*.pickle"):
    all_files[int(filename.replace(".pickle", ""))].add(os.path.join(path, filename))

result = collections.defaultdict(set)
for length, fnames in all_files.iteritems():
  for fname in fnames:
    with open(fname) as f:
      cliques = pickle.load(f)
    for clique in cliques:
      result[length].add(clique)

print len(result)

for k, v in result.iteritems():
  with open("%s/unique_potentially_connected_cliques/%d.pickle"%(basedir, k), "w") as f:
    pickle.dump(list(v), f)
