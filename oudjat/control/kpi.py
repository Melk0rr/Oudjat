""" KPI module handling operations related to indicators """
from datetime import datetime
from typing import List, Dict, Tuple, Union
from enum import Enum

from oudjat.utils.color_print import ColorPrint
from oudjat.control.data import DataFilter, DataScope

class ConformityLevel(Enum):
  """ Defines the levels of conformity for a KPI or any other related element """
  CONFORM = { "min": 95, "max": 100.01, "color": ColorPrint.green }
  PARTIALLYCONFORM = { "min": 70, "max": 95, "color": ColorPrint.yellow }
  NOTCONFORM = { "min": 0, "max": 70, "color": ColorPrint.red }
      

class KPI(DataScope):
  """ KPI class """

  def __init__(
    self,
    name: str,
    perimeter: str,
    scope: List[Dict] | DataScope = None,
    filters: List[Dict] | List[DataFilter] = [],
    description: str = None,
    date: datetime = None
  ):
    """ Constructor """
    super().__init__(name=name, perimeter=perimeter, scope=scope, filters=filters, description=description)

    if date is None:
      date = datetime.today()

    self.date: datetime = date

  def get_date(self) -> datetime:
    """ Getter for kpi date """
    return self.date

  def get_conformity_level(self, value: float = None) -> "ConformityLevel":
    """ Establish the conformity level """
    if value is None:
      value = self.get_kpi_value()
    return next(filter(lambda lvl: lvl.value["min"] <= value <= lvl.value["max"], list(ConformityLevel)))

  def get_kpi_value(self) -> float:
    """ Returns the percentage of conform data based on kpi control """
    return round(len(self.get_data()) / len(self.get_input_data()) * 100, 2)

  def get_print_function(self) -> object:
    """ Defines print function """
    return self.get_conformity_level().value["color"]

  def print_value(
    self,
    prefix: str = None,
    suffix: str = "%\n",
    print_details: bool = True
  ) -> None:
    """ Print value with color based on kpi level """
    scope_str = self.to_string()

    print(prefix, end="")
    if print_details:
      print(f"{scope_str[0]}", end=" = ")

    self.get_print_function()(f"{scope_str[1]}", end=f"{suffix}")

  def get_date_str(self) -> str:
    """ Returns formated date string """
    return self.date.strftime('%Y-%m-%d')

  def to_dictionary(self) -> Dict:
    """ Converts the current instance into a dictionary """
    k_value = self.get_kpi_value()
    conformity = self.get_conformity_level(k_value)

    return {
      "name": self.name,
      "perimeter": self.perimeter,
      "scope": self.get_initial_scope_name(),
      "scope_size": len(self.get_input_data()),
      "conform_elements": len(self.get_data()),
      "value": k_value,
      "conformity": conformity.name,
      "date": self.get_date_str()
    }

  def to_string(self) -> Tuple[str, str]:
    """ Converts the current instance into a string """
    k_value = self.get_kpi_value()
    return (f"{len(self.get_data())} / {len(self.get_input_data())}", f"{k_value}")


class KPIComparator:
  """ KPIComparator class to compare two KPIs """

  tendencies = {
    "+": {
      "icon": "",
      "print": ColorPrint.green
    },
    "-": {
      "icon": "",
      "print": ColorPrint.red
    },
    "=": {
      "icon": "",
      "print": ColorPrint.yellow
    }
  }

  def __init__(self, kpi_a: KPI, kpi_b: KPI):
    """ Constructor """
    if kpi_a.get_perimeter() != kpi_b.get_perimeter():
      raise ValueError(f"{__class__} error : provided KPI do not share the same perimeter !")

    self.kpis = (kpi_a, kpi_b)

    self.values = ()
    self.tendency = None

  def get_kpis(self) -> Tuple[float,float]:
    """ Getter for kpis """
    return self.kpis

  def get_tendency(self) -> Dict:
    """ Getter for comparator tendency """
    return self.tendency

  def fetch_values(self) -> None:
    """ Get kpis different values and set changes """
    self.values = (self.kpis[0].get_kpi_value(), self.kpis[1].get_kpi_value())

  def get_tendency_key(self, v_a: Union[int, float], v_b: Union[int, float]) -> str:
    """ Substract given values and define tendency """
    return "+" if v_b > v_a else "-" if v_b < v_a else "="

  def compare(self) -> None:
    """ Compare values and set tendency """
    if len(self.values) == 0:
      self.fetch_values()

    t_key = self.get_tendency_key(self.values[0], self.values[1])
    self.tendency = self.tendencies[t_key]

  def print_tendency(self, print_first_value: bool = True, sfx: str = "\n") -> None:
    """ Print tendency """
    if print_first_value:
      self.kpis[0].get_print_function()(f"  {self.values[0]}%", end="")

    print(" -- ", end="")
    t_icon = self.tendency["icon"]
    self.kpis[1].get_print_function()(f"{self.values[1]}%", end="")
    self.tendency["print"](t_icon, end=sfx)


class KPIHistory:
  """ KPIEvolution class to handle """

  def __init__(self, name: str, kpis: List["KPI"] = []):
    """ Constructor """
    self.name = name
    self.kpis = []

    self.comparators = []

  def get_kpis(self):
    """ Getter for kpi list """
    return self.kpis

  def set_kpis(self, kpis: List["KPI"] = []) -> None:
    """ Setter for kpi list """
    for k in kpis:
      self.add_kpi(k)

  def add_kpi(self, kpi: "KPI") -> None:
    """ Add a kpi to the kpi list """
    if self.name != kpi.get_name():
      raise ValueError(f"{__class__} error while adding new kpi. KPI name and KPIHistory name must match !")

    self.kpis.append(kpi)

  def build_history(self) -> None:
    """ Builds the KPI history """
    comp_list = []
    sorted_kpis = sorted(self.kpis, key=lambda k: k.get_date())

    for i in range(len(self.kpis) - 1):
      comparator = KPIComparator(sorted_kpis[i], sorted_kpis[i + 1])
      comparator.compare()

      comp_list.append(comparator)
    
    self.comparators = comp_list

  def print_history(self) -> None:
    """ Print the KPI history """
    if len(self.comparators) == 0:
      self.build_history()

    ColorPrint.blue(f"\n {self.name} History")
    for i in range(len(self.comparators)):
      c = self.comparators[i]

      print_first = False
      print_end = ""

      if i == 0:
        print_first = True

      if i == len(self.comparators) - 1:
        print_end = "\n"

      c.print_tendency(print_first_value=print_first, sfx=print_end)