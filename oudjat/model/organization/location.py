from typing import Union, List

from oudjat.model.assets import AssetType, Asset
from oudjat.model.assets.network import Subnet

class Location:
  """ A class to describe generic location with subnets, assets, users """

  # ****************************************************************
  # Attributes & Constructors

  def __init__(
    self,
    id: Union[int, str],
    name: str,
    description: str,
    city: str = None,
    label: str = None,
    subnet: Union[Subnet, List[Subnet]] = None
  ):
    """ Constructor """
    self.id = id
    self.name = name
    self.label = label
    self.description = description
    
    self.assets = {}

  # ****************************************************************
  # Methods
  
  def get_id(self) -> Union[int, str]:
    """ Getter for the location id """
    return self.id
  
  def get_name(self) -> str:
    """ Getter for the location name """
    return self.name
  
  def get_description(self) -> str:
    """ Getter for the location description """
    return self.description
    
  def add_asset(asset: Asset, asset_type: AssetType) -> None:
    """ Adds a new asset to the current location """

    if asset_type not in self.assets.keys():
      self.assets[asset_type] = {}

    if asset.get_id() not in self.assets.keys():
      self.assets[asset_type][asset.get_id()] = asset
    