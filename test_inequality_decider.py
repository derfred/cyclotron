import unittest, inequality_decider

class TestInequalitySupport(unittest.TestCase):
  def test_build_inequality(self):
    # left switch
    self.assertEquals(inequality_decider.extract_inequality("aabbc", "cbaab", ("K1", "K2", "K3", "K4", "K5")), ( (-1, "K2"), (1, "K1"), (1, "aabbc") ))
    # right switch
    self.assertEquals(inequality_decider.extract_inequality("aabbc", "bcaab", ("K1", "K2", "K3", "K4", "K5")), ( (1, "K2"), (-1, "K1"), (-1, "aabbc") ))

class TestPotentialConstraints(unittest.TestCase):
  def test_independent(self):
    ineq1 = ( (-1, "K2"), (1, "K1"), (1, "aabbc") )
    ineq2 = ( (-1, "A2"), (1, "A1"), (1, "bbcaa") )

    self.assertEquals(inequality_decider.potentially_constrained_variables(ineq1, ineq2), None)

  def test_potentially_constrained(self):
    ineq1 = ( (-1, "K2"), (1, "K1"), (1, "aabbc") )     # K2-K1 < aabbc
    ineq2 = ( (1, "A2"), (-1, "A1"), (-1, "aabbc") )    # A2-A1 > aabbc

    potential_constraints = inequality_decider.potentially_constrained_variables(ineq1, ineq2)

    self.assertEquals(len(potential_constraints), 2)
    self.assertEquals(potential_constraints[("K2", "A2")], ("K1", "A1")) # K1 > A1 if K2 > A2
    self.assertEquals(potential_constraints[("A1", "K1")], ("A2", "K2")) # A2 > K2 if A1 > K1

class TestIdentifyRelations(unittest.TestCase):
  def test_potentially_constrained(self):
    ineq1 = ( (-1, "K2"), (1, "K1"), (1, "aabbc") )     # K2-K1 < aabbc
    ineq2 = ( (1, "A2"), (-1, "A1"), (-1, "aabbc") )    # A2-A1 > aabbc

    trivials, constraints, potential_constraints = inequality_decider.identify_relations([ineq1], ineq2)

    self.assertEquals(len(trivials), 0)
    self.assertEquals(len(constraints), 0)
    self.assertEquals(len(potential_constraints), 2)
    self.assertEquals(potential_constraints[("K2", "A2")], set([("K1", "A1")])) # K1 > A1 if K2 > A2
    self.assertEquals(potential_constraints[("A1", "K1")], set([("A2", "K2")])) # A2 > K2 if A1 > K1

class TestInequalityDecider(unittest.TestCase):
  def setUp(self):
    self.decider = inequality_decider.InequalityDecider()

  def test_empty(self):
    assert self.decider.satisfiable()

  def test_single_inequality(self):
    self.decider.add_transition("aabbc", "cbaab", ("K", "K", "K", "K", "K"))
    assert self.decider.satisfiable()

  def test_two_independent_inequalities(self):
    self.decider.add_transition("aabbc", "cbaab", ("K", "K", "K", "K", "K"))
    self.decider.add_transition("cbbaa", "baabc", ("J", "J", "J", "J", "J"))
    assert self.decider.satisfiable()

  def test_second_level_inconsistency(self):
    self.decider.add_transition("bcaba", "abbac", ("K", "K", "B3", "K", "I5"))
    self.decider.add_transition("bcaba", "abcab", ("K", "K", "A3", "K", "I5"))

    self.decider.add_transition("ababc", "bacab", ("B1", "K", "B3", "K", "K"))
    self.decider.add_transition("ababc", "cabab", ("A1", "K", "A3", "K", "K"))

    self.decider.add_transition("aabbc", "cbaab", ("B1", "B2", "K", "K", "K"))
    self.decider.add_transition("aabbc", "bcaab", ("A1", "B2", "K", "K", "K"))

    assert not self.decider.satisfiable()
