import os
import csv
import json

from typing import List, Dict, Any

from oudjat.utils.color_print import ColorPrint
from oudjat.connectors.file.file_types import FileTypes

def check_path(path: str) -> None:
  """ Check if the provided path is valid """
  if not os.path.isfile(path):
    raise(f"Invalid file path provided: {path}")
    
  file_ext = path.split('.')[-1]
  if file_ext.upper() not in FileTypes.__members__:
    raise ValueError(f"Invalid filetype provided: {file_ext}")

class FileConnector:
  """ File connector to interact with different file types """
  
  def __init__(self, path: str, source: str):
    """ Constructor """
    check_path(path)
    
    self.path = path
    self.source = source
    self.filetype = FileTypes[file_ext.upper()]
    self.import_function = self.filetype.value.get("import_function")
    
  def set_path(self, new_path: str) -> None:
    """ Setter for connector path """
    check_path(new_path)
    self.path = new_path
    
  def data(self, callback: object) -> List[Any]:
    """ Returns the file data """
    raise NotImplementedError(
      "data() method must be implemented by the overloading class")
    
class CSVConnector(FileConnector):
  """ Specific file connector for CSV files """
  
  def __init__(self, path: str, source: str, delimiter: str = '|'):
    """ Constructor """
    if len(delimiter) > 0:
      raise(f"Invalid delimiter provided. Please provide a single character")
    
    self.delimiter = delimiter
    super().__init__(path, source)
    
  def data(self, callback: object) -> List[Any]:
    """ Implementation of parent function """
    return self.import_function(file_path=self.path, delimiter=self.delimiter, callback=callback)