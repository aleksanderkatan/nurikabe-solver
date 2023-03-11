from pysat.formula import IDPool
from pysat.formula import CNF
from pysat.solvers import Solver
from pysat.card import CardEnc


class Problem:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.fields = [[None for _ in range(y)] for _ in range(x)]
        self.solution = None

    def add_field(self, x, y, value):
        self.fields[x][y] = value

    def add_solution(self, solution: list[list[bool]]):
        self.solution = solution

    def __str__(self):
        lines = []
        for y in range(self.y):
            line = ""
            for x in range(self.x):
                elem = self.fields[x][y]
                if elem is not None:
                    line += str(elem)
                elif self.solution is not None:
                    if self.solution[x][y] and self.fields[x][y] is not None:
                        raise RuntimeError("Wall at a number!")
                    line += "x" if self.solution[x][y] else "."
                else:
                    line += "."
            lines.append(line)
        return "\n".join(lines)


def _implies(p, q):
    return [-p_i for p_i in p] + [q]


class Encoder:
    def __init__(self, problem_instance: Problem, wall_assumption: (int, int)):
        self.problem = problem_instance
        self.wall_assumption = wall_assumption
        self.pool = IDPool()
        self.v = {}
        self.field_indices = {}
        self.positions_of_indices = {}
        self.field_amount = 0
        self.max_field_size = 0
        self.wall_size = 0


    def _initialize_variables(self):
        xt = self.problem.x
        yt = self.problem.y

        self.wall_size = xt*yt

        for y in range(yt):
            for x in range(xt):
                # there is a wall at pos (x, y)
                self.v["w", x, y] = self.pool.id(("w", x, y))

                # field indices
                if self.problem.fields[x][y] is not None:
                    self.max_field_size = max(self.max_field_size, self.problem.fields[x][y])
                    self.wall_size -= self.problem.fields[x][y]
                    field_index = len(self.field_indices)
                    self.field_indices[(x, y)] = field_index
                    self.positions_of_indices[field_index] = (x, y)
                    self.field_amount += 1

        # field connectivity
        for y in range(yt):
            for x in range(xt):
                for field_index in range(self.field_amount):
                    for dist in range(self.max_field_size):
                        # pos (x, y) belongs to field_index, and is at distance k from field anchor
                        self.v["f", x, y, field_index, dist] = self.pool.id(("f", x, y, field_index, dist))

        # wall connectivity
        for y in range(yt):
            for x in range(xt):
                for dist in range(self.wall_size):
                    # pos (x, y) is at distance dist from wall_assumption
                    self.v["d", x, y, dist] = self.pool.id(("d", x, y, dist))


    def _index_neighbours(self, x, y):
        neighbours = []
        if x > 0:
            neighbours.append((x-1, y))
        if x < self.problem.x - 1:
            neighbours.append((x+1, y))
        if y > 0:
            neighbours.append((x, y-1))
        if y < self.problem.y - 1:
            neighbours.append((x, y+1))
        return neighbours


    def encode(self):
        self._initialize_variables()
        formula = CNF()
        xt = self.problem.x
        yt = self.problem.y

        # every position is in a field at distance or a wall
        for y in range(yt):
            for x in range(xt):
                literals = [self.v["w", x, y]]
                for field_index in range(self.field_amount):
                    for dist in range(self.max_field_size):
                        literals.append(self.v["f", x, y, field_index, dist])
                clauses = CardEnc.equals(literals, bound=1, vpool=self.pool)
                for clause in clauses:
                    formula.append(clause)


        # numbers belong to appropriate fields at distance 0
        for y in range(yt):
            for x in range(xt):
                if self.problem.fields[x][y] is not None:
                    field_index = self.field_indices[(x, y)]
                    formula.append([self.v["f", x, y, field_index, 0]])
                else:
                    for field_index in range(self.field_amount):
                        formula.append([-self.v["f", x, y, field_index, 0]])


        # a ^ b => c v d
        # !a v !b v c v d

        # ..x.4 <- this has to be prevented
        # if in field at distance d, then I have a neighbour at distance d-1
        for y in range(yt):
            for x in range(xt):
                for field_index in range(self.field_amount):
                    for dist in range(1, self.max_field_size):
                        clause = [-self.v["f", x, y, field_index, dist]]
                        for neigh_x, neigh_y in self._index_neighbours(x, y):
                            clause.append(self.v["f", neigh_x, neigh_y, field_index, dist-1])
                        formula.append(clause)

        # if I am in field at distance d, all my non-wall neighbours are in the same field at dist d-1 or d+1
        for y in range(yt):
            for x in range(xt):
                for field_index in range(self.field_amount):
                    for dist in range(0, self.max_field_size):
                        for neigh_x, neigh_y in self._index_neighbours(x, y):
                            clause = [-self.v["f", x, y, field_index, dist], self.v["w", neigh_x, neigh_y]]
                            if dist > 0:
                                clause.append(self.v["f", neigh_x, neigh_y, field_index, dist-1])
                            if dist < self.max_field_size-1:
                                clause.append(self.v["f", neigh_x, neigh_y, field_index, dist+1])
                            formula.append(clause)



        # every field has the appropriate size
        for field_index in range(self.field_amount):
            pos_x, pos_y = self.positions_of_indices[field_index]
            value = self.problem.fields[pos_x][pos_y]
            assert value is not None

            literals = []
            for y in range(yt):
                for x in range(xt):
                    for dist in range(self.max_field_size):
                        literals.append(self.v["f", x, y, field_index, dist])
            clauses = CardEnc.equals(literals, bound=value, vpool=self.pool)
            for clause in clauses:
                formula.append(clause)

        # no squares in walls
        for y in range(yt-1):
            for x in range(xt-1):
                a, b, c, d = self.v["w", x, y], self.v["w", x+1, y], self.v["w", x, y+1], self.v["w", x+1, y+1]
                formula.append([-a, -b, -c, -d])

        # ----- WALL CONNECTIVITY -----

        # this is the anchor
        wall_x, wall_y = self.wall_assumption
        for y in range(yt):
            for x in range(xt):
                if (x, y) == (wall_x, wall_y):
                    formula.append([self.v["d", x, y, 0]])
                else:
                    formula.append([-self.v["d", x, y, 0]])


        # not a wall or there is exactly one distance possible
        for y in range(yt):
            for x in range(xt):
                literals = [-self.v["w", x, y]]
                for dist in range(self.wall_size):
                    literals.append(self.v["d", x, y, dist])
                clauses = CardEnc.equals(literals, bound=1, vpool=self.pool)
                for clause in clauses:
                    formula.append(clause)


        # if wall distance d>0, then I have a neighbour at distance d-1
        for y in range(yt):
            for x in range(xt):
                for dist in range(1, self.wall_size):
                    clause = [-self.v["d", x, y, dist]]
                    for neigh_x, neigh_y in self._index_neighbours(x, y):
                        clause.append(self.v["d", neigh_x, neigh_y, dist-1])
                    formula.append(clause)


        # if wall distance d, then all wall-neighbours have wall distance d-1 or d+1
        for y in range(yt):
            for x in range(xt):
                for dist in range(1, self.wall_size):
                    for neigh_x, neigh_y in self._index_neighbours(x, y):
                        clause = [-self.v["d", x, y, dist], -self.v["w", neigh_x, neigh_y]]
                        if dist > 0:
                            clause.append(self.v["d", neigh_x, neigh_y, dist-1])
                        if dist < self.wall_size-1:
                            clause.append(self.v["d", neigh_x, neigh_y, dist+1])
                        formula.append(clause)


        # if wall, then connected
        for y in range(yt):
            for x in range(xt):
                clause = [-self.v["w", x, y]]
                for dist in range(self.wall_size):
                    clause.append(self.v["d", x, y, dist])
                formula.append(clause)

        return formula

    def decode(self, model: list[int]):
        xt = self.problem.x
        yt = self.problem.y

        walls = [[False for _ in range(yt)] for _ in range(xt)]
        for y in range(yt):
            for x in range(xt):
                walls[x][y] = model[self.v["w", x, y]-1] > 0

        return walls




if __name__ == '__main__':
    instance = Problem(8, 10)
    instance.add_field(3, 0, 5)
    instance.add_field(6, 1, 1)
    instance.add_field(0, 3, 4)
    instance.add_field(1, 4, 2)
    instance.add_field(3, 4, 2)
    instance.add_field(7, 4, 2)
    instance.add_field(0, 7, 4)
    instance.add_field(2, 7, 4)
    instance.add_field(4, 8, 9)
    instance.add_field(7, 9, 2)
    # instance = Problem(5, 2)
    # instance.add_field(0, 0, 4)
    # instance.add_field(3, 0, 4)
    print(instance)
    print()

    # encoder = Encoder(instance, (2, 4))
    encoder = Encoder(instance, (2, 0))
    formula = encoder.encode()
    formula_solution = None
    with Solver(bootstrap_with=formula, name="gluecard4") as solver:
        if solver.solve():
            formula_solution = solver.get_model()
        else:
            raise RuntimeError("No solution!")
    solution = encoder.decode(formula_solution)

    instance.add_solution(solution)
    print(instance)

