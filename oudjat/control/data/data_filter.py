"""A module to handle data filters."""

from typing import Any, Callable, Dict, List, Tuple, Union

from oudjat.utils.color_print import ColorPrint
from oudjat.utils.operations import Operation


class DataFilter:
    """
    A class to handle data filtering operations.

    Once created, a filter can be run against one or multiple elements to check if they are as expected.

    Exemple 1:
        my_filter = DataFilter(fieldname="anything", operator="=", value=9)
        check = my_filter.filter_value(8)
        print(check) -> False

    Exemple 2:
        my_filter = DataFilter(fieldname="name", operator="in", value="Batty")
        replicant = { "name": "Roy Batty", "age": 4 }
        check = my_filter.filter_dict(replicant)
        print(check) -> True
    """

    # ****************************************************************
    # Attributes & Constructors

    def __init__(
        self, fieldname: str, value: Any, operator: str = "in", negate: bool = False
    ) -> None:
        """
        Return a new instance of data filter.

        Args:
            fieldname (str): name of the field to filter
            value (Any)    : the value of the filter and the value the filtered element must have
            operator (str) : the operator used to filter the element
            negate (bool)  : if you want to negate the filter result or not (True -> False; False -> True)
        """

        if operator not in Operation.keys():
            raise ValueError(f"{__class__.__name__}::Invalid operator provided: {operator}")

        self.fieldname = fieldname
        self.operator = operator
        self.value = value
        self.negate = negate

    # ****************************************************************
    # Methods

    def get_fieldname(self) -> str:
        """
        Return the filter fieldname.

        Returns:
            str: fieldname of the instance that will be used to filter a dictionary
        """

        return self.fieldname

    def get_operator(self) -> str:
        """
        Return the filter operator.

        Returns
            str: operator used to determine which function will be used to filter
        """

        return self.operator

    def get_operation(self) -> Callable:
        """
        Return a DataFilterOperation based on current parameters.

        Returns:
            Callable: DataFilterOperation function
        """

        return Operation[self.operator]

    def get_value(self) -> Any:
        """
        Return the filter value.

        Returns:
            Any: the value the filtered element must have
        """
        return self.value

    def set_negate(self, new_negate: bool) -> None:
        """
        Set the filter negation.


        """
        self.negate = new_negate

    def filter_dict(self, element: Dict) -> bool:
        """
        Run the current filter against a dictionary.

        Args:
            element (Dict): element to run the filter against

        Returns:
            bool: wheither or not the dictionary matches the filter
        """

        check = self.get_operation()(element[self.fieldname], self.value)
        return not check if self.negate else check

    def filter_value(self, value: Any) -> bool:
        """
        Run the current filter against the provided value.

        Args:
            value (Any): value to run the filter against

        Returns:
            bool: wheither or not the given value matches the filter
        """

        check = self.get_operation()(value, self.value)
        return not check if self.negate else check

    def __str__(self) -> str:
        """
        Convert the current instance into a string.

        Returns:
            str: current filter converted into a string

        Exemple:
            my_filter = DataFilter(fieldname="name", operator="=", value="Roy Batty")
            print(my_filter) -> name = Roy Batty
        """
        return f"{self.fieldname} {self.operator} {self.value}"

    # ****************************************************************
    # Static methods

    @staticmethod
    def from_dict(filter_dict: Dict) -> "DataFilter":
        """
        Create a datafilter instance from a dictionary.

        Args:
            filter_dict (Dict): dictionary used to create DataFilter instance

        Returns:
            DataFilter: new instance

        Exemple:
            my_filter = DataFilter.from_dict({ "fieldname": "name", "operator": "=", "value": "Rick Deckard"})
        """

        return DataFilter(
            fieldname=filter_dict["fieldname"],
            operator=filter_dict.get("operator", "in"),
            value=filter_dict.get("value", None),
        )

    @staticmethod
    def from_tuple(filter_tuple: Tuple[str, str, Any]) -> "DataFilter":
        """
        Create a datafilter instance from a tuple.

        Args:
            filter_tuple (Tuple): tuple used to create DataFilter instance

        Returns:
            DataFilter: new instance

        Exemple:
            my_filter = DataFilter.from_tuple(( "name", "=", "Rick Deckard" ))
        """

        if len(filter_tuple) < 3:
            raise ValueError(
                f"{__class__.__name__}.from_tuple::3 parameters needed to create a DataFilter instance"
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
        """
        Check filters type and format them into DataFilter instances if needed.

        Args:
            filters_list (List[Dict] | List[DataFilter]): filter list to check / format

        Returns:
            List[DataFilter]: formated list of data filter instances
        """
        filters = []

        for f in filters_list:
            # Checks if the current filter is either a dictionary or a DataFilter instance
            if not isinstance(f, DataFilter) and not isinstance(f, dict):
                ColorPrint.yellow(f"Invalid filter: {f}")
                continue

            filter_i = f
            if isinstance(f, dict):
                filter_i = DataFilter.from_dict(f)

            filters.append(filter_i)

        return filters

    @staticmethod
    def gen_from_dict(filters: List[Dict]) -> List["DataFilter"]:
        """
        Generate multiple DataFitler instances based on dictionnaries.

        Args:
            filters (List[Dict]): list of dictionaries used to generated instances

        Returns:
            List[DataFilter]: data filter instances
        """

        return list(map(DataFilter.from_dict, filters))

    @staticmethod
    def gen_from_tuple(filters: List[Tuple]) -> List["DataFilter"]:
        """
        Generate DataFitler instances based on tuples.

        Args:
            filters (List[Tuple]): list of tuples used to generated instances

        Returns:
            List[DataFilter]: data filter instances
        """

        return list(map(DataFilter.from_tuple, filters))

    @staticmethod
    def get_conditions(element: Any, filters: Union[List["DataFilter"], List[Dict]]) -> bool:
        """
        Run all given filters against a single provided element.

        Args:
            element (Any)                          : element to check
            filters (List[Dict] | List[DataFilter]): filters to run

        Returns:
            bool: filter results
        """
        checks = []

        for f in filters:
            check = None
            if isinstance(f, DataFilter):
                check = f.filter_dict(element)

            else:
                operation = Operation[f["operator"]]
                check = operation(element[f["fieldname"]], f["value"])

            checks.append(check)

        return all(checks)

    @staticmethod
    def filter_data(
        data_to_filter: List[Dict], filters: Union["DataFilter", List["DataFilter"]] = None
    ) -> List[Dict]:
        """
        Filter data based on given filters.

        Args:
            data_to_filter (List[Dict])            : well... the data to be filtered duh
            filters (DataFilter | List[DataFilter]): filters to run

        Returns:
            List[Dict]: filtered data
        """

        if filters is None:
            return data_to_filter

        if not isinstance(filters, list):
            filters = [filters]

        return list(filter(lambda el: all(f.filter_dict(el) for f in filters), data_to_filter))
