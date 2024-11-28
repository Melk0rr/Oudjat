from typing import List, Dict, Union, Any

from oudjat.utils import ColorPrint

from . import DataFilterOperation

class DataFilter:
  """ DataFilter class : handling data filtering """

  # ****************************************************************
  # Attributes & Constructors

  def __init__(
    self,
    fieldname: str,
    value: Any,
    operator: str = "in",
    negate: bool = False
  ):
    """ Constructor """
    if operator not in DataFilterOperation.keys():
      raise ValueError(f"Invalid operator provided: {operator}")

    self.fieldname = fieldname
    self.operator = operator
    self.value = value
    self.negate = negate

  # ****************************************************************
  # Methods

  def get_fieldname(self) -> str:
    """ Getter for filter fieldname """
    return self.fieldname
  
  def get_operator(self) -> str:
    """ Getter for filter operator """
    return self.operator
  
  def get_value(self) -> Any:
    """ Getter for filter value """
    return self.value

  def filter_dict(self, element: Dict) -> bool:
    """ Returns wheither or not the dictionary element matches the filter """
    check = DataFilterOperation[self.operator](element[self.fieldname], self.value)
    if self.negate:
      return not check

    return check

  def filter_value(self, value: Any) -> bool:
    """ Returns wheither or not the given value matches the filter """
    check = DataFilterOperation[self.operator](value, self.value)
    
    if self.negate:
      return not check
    
    return check
    
  def __str__(self) -> str:
    """ Converts the current instance into a string """
    return f"{self.fieldname} {self.operator} {self.value}"

  # ****************************************************************
  # Static methods
  
  @staticmethod
  def datafilter_from_dict(dictionnary: Dict) -> "DataFilter":
    """ Converts a dictionary """
    return DataFilter(
      fieldname=dictionnary["fieldname"],
      operator=dictionnary.get("operator", "in"),
      value=dictionnary["value"]
    )

  @staticmethod
  def get_valid_filters_list(
    filters_list: Union[List[Dict], List["DataFilter"]]
  ) -> List["DataFilter"]:
    """ Check filters type and format them into DataFilter instances if needed """
    filters = []

    for f in filters_list:
      # Checks if the current filter is either a dictionary or a DataFilter instance
      if not isinstance(f, DataFilter) and not isinstance(f, dict):
        ColorPrint.yellow(f"Invalid filter: {f}")
        continue

      filter_i = f
      if isinstance(f, dict):
        filter_i = DataFilter.datafilter_from_dict(f)
      
      filters.append(filter_i)

    return filters

  @staticmethod
  def gen_from_dict(filters: List[Dict]) -> List["DataFilter"]:
    """ Generates DataFitler instances based on dictionnaries """
    filter_instances = []

    for f in filters:
      current_filter = DataFilter.datafilter_from_dict(f)
      filter_instances.append(current_filter)

    return filter_instances

  @staticmethod
  def get_conditions(element: Any, filters: Union[List["DataFilter"], List[Dict]]) -> bool:
    """ Checks given filters on provided element """
    checks = []

    for f in filters:
      if isinstance(f, DataFilter):
        checks.append(f.filter_dict(element))
      
      else:
        operation = DataFilterOperation[f["operator"]]
        checks.append(operation(element[f["fieldname"]], f["value"]))
      
    return all(checks)

  @staticmethod
  def filter_data(data_to_filter: List[Dict], filters: List["DataFilter"]) -> List[Dict]:
    """ Filters data based on given filters """
    filtered_data = []
    for el in data_to_filter:
      conditions = all(f.filter_dict(el) for f in filters)
      if conditions:
        filtered_data.append(el)

    return filtered_data
  

class DataFilterGroup:
  """ Group of data filters joined with """

  # ****************************************************************
  # Attributes & Constructors

  def __init__(self, join_operator: str = "and", filters: List[DataFilter] = None):
    """ Constructor """
    
    if join_operator != "and" and join_operator != "or":
      raise ValueError(f"Invalid join operator provided: {join_operator}. Please use either 'or' or 'and'")
    
    self.join_operator = join_operator
    self.filters = filters

  # ****************************************************************
  # Methods
  
  def get_join_operator(self) -> str:
    """ Getter for join operator """
    return self.join_operator
  
  def get_filters(self) -> List[DataFilter]:
    """ Getter for filters """
    return self.filters
  
  def get_result(self, element: Dict) -> bool:
    """ Get the group result based on parameters """
    res = None

    if self.join_operator == "or":
      res = any(f.filter_dict(element) for f in self.filters)
      
    else:
      res = all(f.filter_dict(element) for f in self.filters)
      
  
  # ****************************************************************
  # Static methods
  
  @staticmethod
  def gen_from_dict(filter_dict: Dict) -> "DataFilterGroup":
    """ Creates a new data filter group from dictionary """
    
    return DataFilterGroup(
      join_operator=filter_dict.get("join_operator", "and"),
      filters=DataFilter.gen_from_dict(filters=filter_dict.get("filters", []))
    )
