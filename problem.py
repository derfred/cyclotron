import string

def read_problem_definition(fname):
  with open(fname) as f:
    result = {}
    for line in f:
      symbol, inputs = string.strip(line).split(":")
      result[int(symbol)] = map(lambda s: s.split(","), inputs.split(";"))
    return result
