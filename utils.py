import os


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
                        raise RuntimeError("Algorith error: wall at a number!")
                    line += "x" if self.solution[x][y] else "."
                else:
                    line += "."
            lines.append(line)
        return "\n".join(lines)


# def try_find_wall(problem_instance: Problem):
#     # neighbour numbers
#     tile_neighbours = {}
#     for



def read_problem_grid(path):
    with open(path, 'r') as f:
        data = []
        for line in f:
            data.append(line)

        xt = len(data[0])
        yt = len(data)

        instance = Problem(xt, yt)
        for y, line in enumerate(data):
            for x, char in enumerate(line):
                if '0' <= char <= '9':
                    instance.add_field(x, y, int(char))
        return instance

