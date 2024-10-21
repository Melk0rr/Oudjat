import json
import requests
from typing import List, Dict, Union

from oudjat.connectors import Connector

EOL_API_URL = "https://endoflife.date/api/"

class EndOfLifeConnector(Connector):
  """ A class to connect to endoflife.date """
  
  # ****************************************************************
  # Attributes & Constructors

  def __init__(self):
    """ Construcotr """

    super().__init__(target=EOL_API_URL)
    self.products = []

  # ****************************************************************
  # Methods

  def get_products(self) -> List[str]:
    """ Getter for list of products """
    return self.products

  def connect(self) -> None:
    """ Connects to target """
    self.connection = None

    try:
      headers = { 'Accept': 'application/json' }
      req = requests.get(f"{self.target}all.json", headers=headers)
      
      if req.status_code == 200:
        self.connection = True
        self.products = json.loads(req.content.decode("utf-8"))
      
    except ConnectionError as e:
      raise ConnectionError(f"Could not connect to {self.target}\n{e}")
    
  def search(
    self,
    search_filter: str,
    attributes: Union[str, List[str]] = None
  ) -> List[Dict]:
    """ Searches the API for product infos """
    res = []

    if self.connection is None or len(self.products) == 0:
      raise ConnectionError("Please run connect to initialize endoflife connection")
    
    if search_filter not in self.products:
      raise ValueError(f"{search_filter} is not a valid product:\n{self.products}")

    if attributes is not None and not isinstance(attributes, list):
      attributes = [ attributes ]
    
    try:
      headers = { 'Accept': 'application/json' }
      req = requests.get(f"{self.target}{search_filter}.json")

      if req.status_code == 200:
        res = json.loads(req.content.decode("utf-8"))

        if attributes is not None:
          res = [ { k: v for k,v in vuln.items() if k in attributes } for e in res ]
        
    except ConnectionError as e:
      raise ConnectionError(f"Could not retreive {search_filter} infos:\n{e}")
    
    return res
