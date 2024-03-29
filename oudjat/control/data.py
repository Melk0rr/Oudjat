""" Data module handling various data manipulation aspects """
from typing import List, Dict


def ope_contains(v, t):
  """ Checks whether or not the value (v) to check is 'in' the target value """
  return v.contains(t)
    
def ope_in(v, t):
  """ Checks whether or not the value (v) to check is 'in' the target value """
  return v in t

class DataFilter:
  """ DataFilter class : handling data filtering """

  operations = {
    "contains": ope_contains,
    "in": ope_in
  }

  def __init__(self, fieldname: str, value: List[str | int | float], operator: str = "in"):
    """ Constructor """
    self.fieldname = fieldname
    self.operator = operator
    self.value = value

  def check_filter(self, element: Dict) -> bool:
    """ Returns whether or not the element match the filter """
    return self.operations[self.operator](element[self.fieldname], self.value)

  @staticmethod
  def get_valid_filters_list(filters_list: List[Dict] | List["DataFilter"]):
    """ Check filters type and format them into DataFilter instances if needed """
    filters_valid = all(isinstance(x, DataFilter) for x in filters_list)
    if not filters_valid:
      filters_dict = all(isinstance(x, dict) for x in filters_list)

      if not filters_dict:
        raise ValueError(f"{__class__}: Invalid filters. Please provide either a list of dictionaries or a list of DataFilter instances")

      filters = DataFilter.gen_from_dict(filters_list)

    return filters_list

  @staticmethod
  def gen_from_dict(filters: List[Dict]):
    """ Generates DataFitler instances based on dictionnaries """
    filter_instances = []
    for f in filters:
      i = DataFilter(fieldname=f["field"], operator=f.get("operator", "in"), value=f["value"])
      filter_instances.append(i)

    return filter_instances

  @staticmethod
  def filter_data(data_to_filter: List[Dict], filters: List):
    """ Filters data based on given filters """
    filtered_data = []
    for el in data_to_filter:
      conditions = all(f.check_filter(el) for f in filters)
      if conditions:
        filtered_data.append(el)

    return filtered_data

class DataScope:
  """ DataScope class : handling data unfiltered and filtered state """

  def __init__(
    self,
    name: str,
    perimeter: str,
    data: List[Dict] | "DataScope" = None,
    filters: List[Dict] | List[DataFilter] = [],
    description: str = ""
  ):
    """ Constructor """
    self.name = name
    self.description = description
    self.perimeter = perimeter

    self.initial_scope = ""
    if isinstance(data, DataScope):
      self.initial_scope = data.get_name()

    self.data_in = data.get_data() if isinstance(data, DataScope) else data
    self.filters = DataFilter.get_valid_filters_list(filters)
    self.data = None

  def get_name(self):
    """ Getter for perimeter name """
    return self.name

  def get_input_data(self):
    """ Getter for input data """
    return self.data_in

  def get_perimeter(self):
    """ Getter for perimeter """
    return self.perimeter

  def set_input_data(self, data: List[Dict] | "DataScope"):
    """ Setter for input data """
    self.data_in = data.get_data() if isinstance(data, DataScope) else data
    self.initial_scope = data.get_name()
    self.data = None

  def set_filters(self, filters: List[Dict] | List[DataFilter] = []):
    """ Setter for filters """
    self.filters = DataFilter.get_valid_filters_list(filters)

  def filter_data(self):
    """ Apply filters to kpi data to get perimeter specific data """

    self.data = self.data_in

    if len(self.filters) > 0:
      self.data = DataFilter.filter_data(self.data_in, self.filters)

  def get_data(self):
    """ Getter for perimeter data """
    if self.data_in is None:
      raise ValueError(f"{__class__}: no input data defined for current scope {self.name}")

    if self.data is None:
      self.filter_data()

    return self.data

  @staticmethod
  def merge_scopes(name: str, scopes: List["DataScope"]):
    """ Merges given scopes into one """
    # Check if all scopes are on the same perimeter
    perimeters = set([ s.get_perimeter() for s in scopes ])
    if len(perimeters) > 1:
      raise ValueError(f"{__class__}: Error merging scopes. Please provide scopes with the same perimeter")

    merge_data = []
    for s in scopes:
      merge_data.extend(s.get_data())

    merge = DataScope(name=name, perimeter=list(perimeters)[0], data=merge_data, filters=[])
    merge.filter_data()

    return merge