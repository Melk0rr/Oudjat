from typing import List

from oudjat.model.network import Subnet
from oudjat.connectors.ldap.objects import LDAPObject, LDAPEntry

class LDAPSubnet(LDAPObject, Subnet):
  """ A class to describe LDAP subnet objects """

  # ****************************************************************
  # Attributes & Constructors

  def __init__(self, ldap_entry: LDAPEntry):
    """ Constructor """
    super().__init__(ldap_entry=ldap_entry)
    Subnet.__init__(
      self,
      addr=ldap_entry.get("name"),
      name=ldap_entry.get("location"),
      description=ldap_entry.get("description")
    )

  # ****************************************************************
  # Methods