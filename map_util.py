class Map(object):
  def __init__(self, width, height):
    self.width = width
    self.height = height

    # we'll store the map as a dict where 
    # data[(x, y)] is the map cell at coordinates
    # (x, y). not super efficient, but if we really 
    # need super efficiency, we can look into numpy's
    # multi-dimensional arrays (I'm not convinced
    # that lists of lists in python are any better and 
    # they're more annoying to initialize) 

    # also, since our maps are probably pretty wall-sparse,
    # this might be better anyway (not that it matters)
    self.data = dict([((x, y), 0) for x in xrange(self.width) 
                                  for y in xrange(self.height)])

  # set cell x, y to cell_val
  def set_cell(self, x, y, cell_val):
    self.data[(x,y)] = cell_val

# load map from file
def load_from_file(fname):
  with open('maps/%s' % fname) as f:
    line = f.readline()
    dims = [int(x) for x in line.split()]
    m = Map(dims[0], dims[1])

    for y in xrange(dims[1]):
      line = f.readline()
      vals = [int(x) for x in line.split()]
      for x in xrange(dims[0]):
        m.set_cell(x, y, vals[x])

  return m





