#!/usr/bin/python3

import time
import sys
import shutil
import random
import argparse
from functools import partial
from itertools import tee


# designate some printing helpers
print_ns = partial(print, sep='') # print with no spaces between items
print_ns_nn = partial(print, sep='', end='') # print no spaces and no newline


# designate some slices
ALL_BUT_LAST = slice(-1)
LAST = -1


# box drawing unicode characters
h = '\u2500' # horizontal
v = '\u2502' # vertical
tlc = '\u250c' # top left corner
trc = '\u2510' # top right corner
blc = '\u2514' # bottom left corner
brc = '\u2518' # bottom right corner
vr = '\u251c' # vertical and right
vl = '\u2524' # vertical and left
hd = '\u252c' # horizontal and down
hu = '\u2534' # horizontal and up
hv = '\u253c' # horizontal and vertical (cross)


# for easier iterating
def pairwise(iterable):
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


# for merging sets of cells
def merge(a, b):
    """Merge set b into set a. All cells in set b will have their
    set key updated to a. b will still exist afterward but will
    have zero elements."""

    a_cell = a.pop()
    a_set_key = a_cell.set_key
    a.add(a_cell)

    a.update(b)
    for c in b:
        c.set_key = a_set_key
    
    b.clear()



class Cell:
    def __init__(self, key=None):
        self.set_key = key
        self.walls = {'r', 'd'}



class Row:

    def __init__(self):
        self.sets = {}
        self.cells = []
            

    def __len__(self):
        return len(self.cells)
    

    @classmethod
    def from_num_cells(cls, num_cells):
        """Create a new row of num_cells length."""
        row = cls()
        for i in range(num_cells):
            cell = Cell(key=i)
            row.sets[i] = {cell}
            row.cells.append(cell)

        return row


    @classmethod
    def from_prev_row(cls, prev_row):
        """Create a new row from the previous row."""
        row = cls()

        for i in range(len(prev_row)):
            above_cell = prev_row.cells[i]
            cell = Cell()
            row.cells.append(cell)

            if 'd' not in above_cell.walls:
                # this cell should belong to same set as above_cell
                cell.set_key = above_cell.set_key

                if cell.set_key in row.sets:
                    row.sets[cell.set_key].add(cell)
                else:
                    row.sets[cell.set_key] = {cell}

            else:
                # this should be a new cell with a new set
                used_keys = prev_row.sets.keys() | row.sets.keys()
                low_unused_key = 0

                while low_unused_key in used_keys:
                    low_unused_key += 1

                assert low_unused_key not in used_keys

                cell.set_key = low_unused_key
                row.sets[cell.set_key] = {cell}

        return row


    def process_right_walls(self):
        """Randomly join adjacent cells that belong to different sets."""
        for cell, next_cell in pairwise(self.cells):
            cell_set = self.sets[cell.set_key]
            next_cell_set = self.sets[next_cell.set_key]

            if next_cell not in cell_set:
                if random.random() < 0.5:
                    cell.walls.remove('r')
                    
                    k = next_cell.set_key
                    merge(cell_set, next_cell_set)
                    del self.sets[k]


    def process_down_walls(self):
        """Create at least one down path per set."""
        for s in self.sets.values():
            tmp_set = set()
            down_walls_removed = 0

            while len(s) > 1:
                cell = s.pop()
                tmp_set.add(cell)
                if random.random() < 0.5:
                    cell.walls.remove('d')
                    down_walls_removed += 1

            cell = s.pop()
            tmp_set.add(cell)
            if down_walls_removed == 0 or random.random() < 0.5:
                cell.walls.remove('d')
            
            s.update(tmp_set)


    def process_last_row(self):
        """Connect adjacent but disjoint cells."""
        for cell, next_cell in pairwise(self.cells):
            cell_set = self.sets[cell.set_key]
            next_cell_set = self.sets[next_cell.set_key]

            if next_cell not in cell_set:
                cell.walls.remove('r')

                k = next_cell.set_key
                merge(cell_set, next_cell_set)
                del self.sets[k]


    # things for printing rows of cells
    def print_very_first_third(self):
        """Print the very first line of the maze."""
        print_ns_nn(tlc, h * 3)
        print_ns((hd + h * 3) * (num_cells - 1), trc)


    def print_very_last_third(self):
        """Print the very last line of the maze."""
        print_ns_nn(blc, h * 3)
        print_ns((hu + h * 3) * (num_cells - 1), brc)


    def print_middle_third(self, verbose=False):
        """Print the middle line of a row of cells."""
        if verbose:
            print_ns_nn(v)
            for c in self.cells:
                if 'r' in c.walls:
                    if c.set_key < 10:
                        print_ns_nn(' ', c.set_key, ' ', v)
                    elif 10 <= c.set_key < 100:
                        print_ns_nn(' ', c.set_key, v)
                    else:
                        print_ns_nn(c.set_key, v)
                else:
                    if c.set_key < 10:
                        print_ns_nn(' ', c.set_key, '  ')
                    elif 10 <= c.set_key < 100:
                        print_ns_nn(' ', c.set_key, ' ')
                    else:
                        print_ns_nn(c.set_key)
        else:
            print_ns_nn(v)
            for c in self.cells:
                if 'r' in c.walls:
                    print_ns_nn(' ' * 3, v)
                else:
                    print_ns_nn(' ' * 4)

        print_ns_nn('\n')


    def print_last_third(self):
        """Print the shared line of two rows of cells.
        This is row's first third and prev_row's last third."""
        row = self.cells
        print_ns_nn(vr)
        for c in row[ALL_BUT_LAST]:
            if 'd' in c.walls:
                print_ns_nn(h * 3, hv)
            else:
                print_ns_nn(' ' * 3, hv)

        c = row[LAST]
        if 'd' in c.walls:
            print_ns_nn(h * 3, vl)
        else:
            print_ns_nn(' ' * 3, vl)
        print_ns_nn('\n')


def parse_cmd():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Display each cell\'s set number.')
    return parser.parse_args()


if __name__ == '__main__':

    args = parse_cmd()

    # calculate how many cells to fill the terminal
    columns, _ = shutil.get_terminal_size()
    num_cells = (columns - 1) // 4

    # make a row
    row = Row.from_num_cells(num_cells)

    row.print_very_first_third()

    while True:
        try:
            # combine some right adjacent cells
            row.process_right_walls()
            # open some down walls
            row.process_down_walls()

            row.print_middle_third(args.verbose)
            row.print_last_third()

            row = Row.from_prev_row(row)

            time.sleep(0.03)

        except KeyboardInterrupt:
            # must print '\r' (return) to overwrite the ^C
            print_ns_nn('\r')
            
            row.process_last_row()

            row.print_middle_third(args.verbose)
            row.print_very_last_third()

            sys.exit(0)
