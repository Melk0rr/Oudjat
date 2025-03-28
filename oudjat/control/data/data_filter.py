from typing import Any, Callable, Dict, List, Tuple, Union

from oudjat.utils import ColorPrint

from .data_filter_operations import DataFilterOperation


class DataFilter:
    """DataFilter class : handling data filtering"""

    # ****************************************************************
    # Attributes & Constructors

    def __init__(self, fieldname: str, value: Any, operator: str = "in", negate: bool = False):
        """Constructor"""
        if operator not in DataFilterOperation.keys():
            raise ValueError(f"Invalid operator provided: {operator}")

        self.fieldname = fieldname
        self.operator = operator
        self.value = value
        self.negate = negate

    # ****************************************************************
    # Methods

    def get_fieldname(self) -> str:
        """Getter for filter fieldname"""
        return self.fieldname

    def get_operator(self) -> str:
        """Getter for filter operator"""
        return self.operator

    def get_operation(self, value: Any) -> Callable:
        """Returns a DataFilterOperation based on current parameters"""
        base_operation = DataFilterOperation[self.operator](value, self.value)
        return not base_operation if self.negate else base_operation

    def get_value(self) -> Any:
        """Getter for filter value"""
        return self.value

    def set_negate(self, new_negate: bool) -> None:
        """Setter for filter negate"""
        self.negate = new_negate

    def filter_dict(self, element: Dict) -> bool:
        """Returns wheither or not the dictionary element matches the filter"""

        return self.get_operation(value=element[self.fieldname])

    def filter_value(self, value: Any) -> bool:
        """Returns wheither or not the given value matches the filter"""

        return self.get_operation(value)

    def __str__(self) -> str:
        """Converts the current instance into a string"""
        return f"{self.fieldname} {self.operator} {self.value}"

    # ****************************************************************
    # Static methods

    @staticmethod
    def datafilter_from_dict(filter_dict: Dict) -> "DataFilter":
        """Creates a datafilter instance from a dictionary"""

        return DataFilter(
            fieldname=filter_dict["fieldname"],
            operator=filter_dict.get("operator", "in"),
            value=filter_dict["value"],
        )

    @staticmethod
    def datafilter_from_tuple(filter_tuple: Tuple[str, str, Any]) -> "DataFilter":
        """Creates a datafilter instance from a tuple"""

        if len(filter_tuple) < 3:
            raise ValueError(
                "DataFilter.datafilter_from_tuple::3 parameters needed to create a DataFilter instance"
            )

        return DataFilter(
            fieldname=filter_tuple[0],
            operator=filter_tuple[1],
            value=filter_tuple[2],
        )

    @staticmethod
    def get_valid_filters_list(
        filters_list: Union[List[Dict], List["DataFilter"]],
    ) -> List["DataFilter"]:
        """Check filters type and format them into DataFilter instances if needed"""
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
        """Generates DataFitler instances based on dictionnaries"""

        return list(map(lambda f: DataFilter.datafilter_from_dict(f), filters))

    @staticmethod
    def gen_from_tuple(filters: List[Tuple]) -> List["DataFilter"]:
        """Generates DataFitler instances based on tuples"""

        return list(map(lambda f: DataFilter.datafilter_from_tuple(f), filters))

    @staticmethod
    def get_conditions(element: Any, filters: Union[List["DataFilter"], List[Dict]]) -> bool:
        """Checks given filters on provided element"""
        checks = []

        for f in filters:
            check = None
            if isinstance(f, DataFilter):
                check = f.filter_dict(element)

            else:
                operation = DataFilterOperation[f["operator"]]
                check = operation(element[f["fieldname"]], f["value"])

            checks.append(check)

        return all(checks)

    @staticmethod
    def filter_data(
        data_to_filter: List[Dict], filters: Union["DataFilter", List["DataFilter"]] = None
    ) -> List[Dict]:
        """Filters data based on given filters"""

        if filters is None:
            return data_to_filter

        if not isinstance(filters, list):
            filters = [filters]

        return list(filter(lambda el: all(f.filter_dict(el) for f in filters), data_to_filter))
