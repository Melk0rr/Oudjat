from typing import Any, List

from oudjat.utils import get_credentials


class Connector:
    """Base connector"""

    def __init__(self, target: Any, service_name: str = None, use_credentials: bool = False):
        """Constructor"""
        self.target = target
        self.service_name = service_name

        # Retreive credentials for the service
        self.credentials = None
        if use_credentials:
            self.credentials = get_credentials(self.service_name)

        self.connection = None

    def get_connection(self) -> Any:
        """Returns the current connection"""
        return self.connection

    def set_target(self, target: Any) -> None:
        """Setter for connector target"""
        self.target = target

    def set_service_name(self, new_service_name: str, use_credentials: bool) -> None:
        """Setter for service name"""
        self.service_name = new_service_name

        if use_credentials:
            self.credentials = get_credentials(self.service_name)

    def connect(self) -> None:
        """Connects to the target"""
        raise NotImplementedError("connect() method must be implemented by the overloading class")

    def search(self) -> List[Any]:
        """Connects to the target"""
        raise NotImplementedError("search() method must be implemented by the overloading class")

