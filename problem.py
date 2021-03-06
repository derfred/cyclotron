import string

def read_problem_definition(fname):
  with open(fname) as f:
    result = {}
    for line in f:
      if line[0]!= "#" and line != "":
        symbol, inputs = string.strip(line).split(":")
        result[int(symbol)] = map(lambda s: tuple(s.split(",")), inputs.split(";"))
    return result
