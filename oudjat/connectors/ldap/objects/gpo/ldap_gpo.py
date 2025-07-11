"""A module to allow Group policy object retrieving and manipulations throug LDAPConnector."""

import re
from enum import Enum, IntEnum
from typing import TYPE_CHECKING, Dict, List, Union

from ..definitions import UUID_REG
from ..ldap_object import LDAPObject
from .ms_gppref import MS_GPPREF

if TYPE_CHECKING:
    from ...ldap_connector import LDAPConnector
    from ..ldap_entry import LDAPEntry


class LDAPGPOScope(Enum):
    """GPO scope enumeration."""

    USER = "gPCUserExtensionNames"
    MACHINE = "gPCMachineExtensionNames"


class LDAPGPOState(IntEnum):
    """GPO state enumeration."""

    ENABLED = 0
    DISABLED = 1
    ENFORCED = 2


class LDAPGroupPolicyObject(LDAPObject):
    """A class to manipulate Group Policy Objects."""

    # ****************************************************************
    # Attributes & Constructors
    def __init__(self, ldap_entry: "LDAPEntry"):
        """
        Initialize an instance of LDAPGPO.

        This constructor takes an LDAP entry as input and initializes the object with necessary attributes derived from the entry.

        Args:
            ldap_entry (LDAPEntry): An LDAP entry representing a group policy object.
        """

        super().__init__(ldap_entry=ldap_entry)

        self.display_name = self.entry.get("displayName")

        self.scope = None
        self.state = None

        wql = self.entry.get("gPCWQLFilter", None)

        if wql is not None:
            self.state = LDAPGPOState(int(wql.split(";")[-1][0]))

        try:
            self.scope = (
                LDAPGPOScope.USER
                if self.entry.get(LDAPGPOScope.USER.value) is not None
                else LDAPGPOScope.MACHINE
            )

        except Exception as e:
            raise (f"{__class__.__name__}::Error while trying to get group policy scope\n{e}")

        guids = re.findall(UUID_REG, self.entry.get(self.scope.value))
        self.infos = {guid: MS_GPPREF[guid] for guid in guids}

    # ****************************************************************
    # Methods

    def get_display_name(self) -> str:
        """
        Getter for GPO display name.

        Returns:
            str: The display name of the group policy object.
        """

        return self.display_name

    def get_infos(self) -> List[str]:
        """
        Getter for policy GUIDs.

        Returns:
            List[str]: A list of GUIDs associated with the group policy preferences.
        """

        return self.infos

    def get_linked_objects(
        self,
        ldap_connector: "LDAPConnector",
        attributes: Union[str, List[str]] = None,
        ou: str = "*",
    ) -> List["LDAPObject"]:
        """
        Get the GPO linked objects.

        This method searches for LDAP entries that are linked to the current group policy object (GPO).

        Args:
            ldap_connector (LDAPConnector)              : An instance of an LDAP connector used to perform the search operation.
            attributes (Union[str, List[str], optional) : The attributes to retrieve from the linked LDAP entries.
            ou (str, optional)                          : The organizational unit (OU) in which to search for linked objects.

        Returns:
            List["LDAPObject"]: A list of LDAPOrganizationalUnit instances that are linked to the current GPO.
        """

        return ldap_connector.get_ou(
            search_filter=f"(gPLink={f'*{self.name}*'})(name={ou})", attributes=attributes
        )

    def to_dict(self) -> Dict:
        """
        Convert the current instance into a dict.

        This method converts the group policy object (GPO) and its related information into a dictionary format for easier serialization or transmission.

        Returns:
            Dict: A dictionary containing the GPO's display name, scope, state, and linked GUIDs.
        """

        base_dict = super().to_dict()

        return {
            **base_dict,
            "displayName": self.display_name,
            "scope": self.scope.name,
            "state": self.state.name,
            "infos": " - ".join(self.infos.values()),
        }

    # ****************************************************************
    # Static methods
