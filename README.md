## Nurikabe Solver
So I got angry with a [Nurikabe](https://en.wikipedia.org/wiki/Nurikabe_(puzzle)) I couldn't solve, and decided to make a sat encoding for it to find the solution.  
And here it is.

Pass in the name of the file in the parameter, and the program will output the solution to stdout.

Input format:
```
4.4...2.
........
.......4
........
........
.....2..
.9......
....2...
..2..8..
...6....
2.......
```

Output format:
```
4x4..x2.
.x.xxxxx
.xxx...4
.x.xxxxx
xx..x.x.
...xx2x.
.9.x.xx.
xxxx2x..
x.2xx8..
xxx6xxxx
2.x.....
```
where "x" denotes walls.

If the solver says an instance is unsolvable, make sure you didn't put an extra space in any line.  
Or the solver may also be faulty, but hey, it worked for the 2 instances I fed to it!
