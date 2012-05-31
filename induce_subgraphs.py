#
# Second step of the decoding finding pipeline. usage:
#  python induce_subgraphs.py <problem_def> <basedir> <worker_index>
#

import pickle, os, sys, time, itertools, cache
from problem import *
import networkx as nx

problem_def = read_problem_definition(sys.argv[1])
max_len     = int(sys.argv[3])

with open("cycles.pickle") as f:
  cycles = filter(lambda c: len(c) <= max_len, pickle.load(f))

def index(comb):
  return comb[1]+comb[0]*len(cycles)

total_slices = 399
basedir      = sys.argv[2]
my_slice     = int(sys.argv[4])

@cache.lfu_cache(maxsize=2000)
def load_neighbours(vertex):
  with open("%s/neighbours/%d-%d.pickle"%(basedir, vertex[0], vertex[1])) as f:
    return pickle.load(f)

data = {}

for vertex in itertools.product(problem_def.keys(), xrange(len(cycles))):
  if index(vertex) % total_slices == my_slice:
    print "processing %s"%str(vertex)
    neighbours = load_neighbours(vertex)

    G = nx.Graph()
    G.add_node(vertex)

    for neighbour in neighbours:
      G.add_edge(vertex, neighbour)
      for nneighbour in load_neighbours(neighbour).intersection(neighbours):
        # only construct the subgraph induced by vertex and neighbours
        if nneighbour in neighbours:
          G.add_edge(neighbour, nneighbour)

    nx.write_gpickle(G, "%s/graphs/%d-%d.gpickle.bz2"%(basedir, vertex[0], vertex[1]))

    data[vertex] = { "nodes": G.number_of_nodes(), "edges": G.number_of_edges() }
    print " done[%s] %s"%(time.strftime('%X %x'), str(data[vertex]))
