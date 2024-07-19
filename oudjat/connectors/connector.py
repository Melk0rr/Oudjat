from typing import List, Any

from oudjat.utils.credentials import get_credentials

class Connector:
  """ Base connector """
  def __init__(self, target: Any, service_name: str = None):
    """ Constructor """
    self.target = target
    self.service_name = service_name

    # Retreive credentials for the service
    self.credentials = None
    if service_name is not None:
      self.credentials = get_credentials(self.service_name)

  def set_service_name(self, new_service_name: str) -> None:
    """ Setter for service name """
    self.service_name = new_service_name
    self.credentials = get_credentials(self.service_name)

  def connect(self) -> None:
    """ Connects to the target """
    raise NotImplementedError(
      "data() method must be implemented by the overloading class")

  def search(self) -> List[Any]:
    """ Connects to the target """
    raise NotImplementedError(
      "data() method must be implemented by the overloading class")