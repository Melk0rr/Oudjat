""" Target module handling targeting operations and data gathering """
from oudjat.utils.color_print import ColorPrint
from oudjat.utils.init_option_handle import str_file_option_handle
from oudjat.utils.file import export_2_csv

from .base import Base


class Target(Base):
  """ Main enumeration module """
  results = []

  def __init__(self, options):
    """ Initialization function """
    super().__init__(options)
    str_file_option_handle(self, "TARGET", "FILE")

  def handle_exception(self, e, message=""):
    """ Function handling exception for the current class """
    if self.options["--verbose"]:
      print(e)
    if message:
      ColorPrint.red(message)

  def res_2_csv(self):
    """ Write the results into a CSV file """
    print("\nExporting results to csv...")
    export_2_csv(self.results, self.options["--export-csv"], '|')

  def run(self):
    """ Main function called from the cli module """
    # Retreive IP of target and run initial configuration
    self.init()
