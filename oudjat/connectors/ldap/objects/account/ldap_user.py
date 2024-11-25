from typing import Dict

from oudjat.control.data import DataFilter
from oudjat.model.assets.user import User
from oudjat.connectors.ldap.objects import LDAPEntry

from . import LDAPUserType, LDAPAccount

class LDAPUser(LDAPAccount, User):
  """ A class to describe LDAP user objects """

  # ****************************************************************
    # Attributes & Constructors

  def __init__(self, ldap_entry: LDAPEntry):
    """ Constructor """

    super().__init__(ldap_entry=ldap_entry)

    self.employeeId = self.entry.get("employeeID", None)
    self.manager = self.entry.get("manager", None)

    email = self.entry.get("mail", None)
    if email is not None:
      email = email.lower()

    User.__init__(
      self,
      id=self.uuid,
      name=self.name,
      firstname=self.entry.get("givenName"),
      lastname=self.entry.get("sn"),
      email=email,
      login=self.san,
      description=self.description,
    )

  # ****************************************************************
  # Methods
  
  def get_employee_id(self) -> str:
    """ Getter for the employee id """
    return self.employeeId
  
  def get_manager(self) -> str:
    """ Getter for the user's manager """
    return self.manager

  def is_admin(self) -> bool:
    """ Checks if the current user is an admin """
    is_admin = False
    adm_count = self.entry.get("adminCount", None)
    
    if adm_count is not None:
      is_admin = adm_count == 1

    return is_admin

  def is_service_account(self) -> bool:
    """ Try to determine if the current user is a service account """
    check = False
    
    svc_filters = DataFilter.gen_from_dict(LDAPUserType.SERVICE.value["filters"])
    if all(f.filter_value(value=self.entry.get(f.get_fieldname(), None)) for f in svc_filters):
      check = True
      
    return check
  
  def to_dict(self) -> Dict:
    """ Converts the current instance into a dictionary """
    base_dict = super().to_dict()
    base_dict.pop("san")

    user_dict = User.to_dict(self)

    return {
      **base_dict,
      "employeeID": self.employeeId,
      "manager": self.manager,
      "is_admin": self.is_admin(),
      **user_dict
    }