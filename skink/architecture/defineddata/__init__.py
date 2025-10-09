from skink.sarif.defineddata.DefinedDataResult import DefinedDataResult


class DefinedData(object):

  def __init__(self, ddr: DefinedDataResult):
    self.ddr = ddr

  def address(self):
    return list(set(l.physicalLocation.address.absoluteAddress for l in self.ddr.locations))[0]