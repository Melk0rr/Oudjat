"""A module that describes group of assets."""
from typing import Dict, List, Union

from ..asset import Asset
from ..asset_type import AssetType
from ..generic_identifiable import GenericIdentifiable


class GroupMemberList(dict):
    """Dict override to handle member list."""


class Group(Asset):
    """A class to handle groups of assets."""

    # ****************************************************************
    # Attributes & Constructors

    def __init__(
        self,
        group_id: Union[int, str],
        name: str,
        label: str = None,
        description: str = None,
    ):
        """
        Create a new Group of assets.

        Args:
            group_id (Union[int, str]) : The identifier of the group.
            name (str)                 : The name of the group.
            label (str, optional)      : A short text label for the group. Defaults to None.
            description (str, optional): A detailed description of the group. Defaults to None.
        """

        super().__init__(
            asset_id=group_id, name=name, label=label, description=description, asset_type=AssetType.GROUP
        )

        self.members = GroupMemberList()

    # ****************************************************************
    # Methods

    def get_members(self) -> Dict[str, Asset]:
        """
        Return the members of the group.

        Returns:
            Dict[str, Asset]: A dictionary containing all members by their identifier.
        """

        return self.members.values()

    def get_member_names(self) -> List[str]:
        """
        Return the list of member names in the group.

        Returns:
            List[str]: A list of names of all members.
        """

        return [m.get_name() for m in self.members.values()]

    def add_member(self, member: GenericIdentifiable) -> None:
        """
        Add a new member to the group.

        Args:
            member (GenericIdentifiable): The asset to be added as a member.
        """

        if isinstance(member, GenericIdentifiable):
            self.members[member.get_id()] = member

    def clear_members(self) -> None:
        """
        Clear all members from the group.

        This method deletes all entries in the member list.
        """

        for member_id in list(
            self.members.keys()
        ):  # Using list to avoid RuntimeError during modification
            del self.members[member_id]

    def __str__(self) -> str:
        """
        Convert the current instance into a string representation.

        Returns:
            str: A string that represents the group's name.
        """

        return f"{self.name}"
