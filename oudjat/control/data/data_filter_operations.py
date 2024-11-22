import re

from typing import Union, List, Any

def ope_equals(a: Any, b: Any) -> bool:
  """ Checks if a equals b """
  return a == b

def ope_contains(a: Union[str, List], b: Any) -> bool:
  """ Checks if a contains b """
  return a.contains(b)
    
def ope_in(a: Any, b: Union[List, str]) -> bool:
  """ Checks if a is in b """
  return a in b

def ope_greater_than(a: Union[int, float], b: Union[int, float]) -> bool:
  """ Checks if a is greater than b """
  return a > b

def ope_greater_equal_than(a: Union[int, float], b: Union[int, float]) -> bool:
  """ Checks if a is greater than b """
  return a >= b

def ope_lower_than(a: Union[int, float], b: Union[int, float]) -> bool:
  """ Checks if a is greater than b """
  return a < b

def ope_lower_equal_than(a: Union[int, float], b: Union[int, float]) -> bool:
  """ Checks if a is greater than b """
  return a <= b

def ope_reg_match(value: str, pattern: str) -> bool:
  """ Checks if the value matches the provided pattern """
  return re.match(pattern, value)

def ope_reg_search(value: str, patter: str) -> bool:
  """ Searches for the provided pattern in value """
  return re.search(pattern, value)

DataFilterOperations = {
  "=": ope_equals,
  "contains": ope_contains,
  "in": ope_in,
  ">": ope_greater_than,
  ">=": ope_greater_equal_than,
  "<": ope_lower_than,
  "<=": ope_lower_equal_than,
  "match": ope_reg_match,
  "search": ope_reg_search
}