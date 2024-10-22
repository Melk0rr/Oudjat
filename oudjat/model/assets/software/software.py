from enum import Enum
from datetime import datetime
from typing import List, Dict, Union

from oudjat.utils import date_format_from_flag, DATE_FLAGS, days_diff
from oudjat.model.assets import Asset, AssetType
from oudjat.model.vulnerability import CVE_REGEX

def soft_date_str(date: datetime) -> str:
  """ Converts a software date into a string """
  soft_date = None
  if date is not None:
    date.strftime(date_format_from_flag(DATE_FLAGS))
    
  return soft_date

class SoftwareType(Enum):
  """ An enumeration to list software types """
  OS = 0
  APPLICATION = 1

class SoftwareRelease:
  """ A class to describe software releases """
  
  # ****************************************************************
  # Attributes & Constructors
  
  def __init__(
    self,
    software: "Software",
    version: Union[int, str],
    release_date: Union[str, datetime],
    release_label: str = None,
    support: Union[str, datetime] = None,
    end_of_life: Union[str, datetime] = None,
    edition: Union[str, List[str]] = None,
    long_term_support = False
  ):
    """ Constructor """

    self.software = software
    self.version = version
    self.label = release_label

    if not isinstance(edition, list):
      edition = [ edition ]

    self.edition = edition

    if support is not None and end_of_life is None:
      end_of_life = support

    try:
      if not isinstance(release_date, datetime):
        release_date = datetime.strptime(release_date, date_format_from_flag(DATE_FLAGS))
        
      if end_of_life is not None and not isinstance(end_of_life, datetime):
        end_of_life = datetime.strptime(end_of_life, date_format_from_flag(DATE_FLAGS))

      if support is not None and not isinstance(support, datetime):
        support = datetime.strptime(support, date_format_from_flag(DATE_FLAGS))

    except ValueError as e:
      raise ValueError(f"Please provide dates with %Y-%m-%d format\n{e}")

    self.active_support = support
    self.release_date = release_date
    self.end_of_life = end_of_life
    
    self.lts = long_term_support

    self.vulnerabilities = set()

  # ****************************************************************
  # Methods

  def get_software(self) -> "Software":
    """ Getter for release software """
    return self.software
  
  def get_label(self) -> str:
    """ Getter for release label """
    return self.label
  
  def get_version(self) -> Union[int, str]:
    """ Getter for release version """
    return self.version

  def get_edition(self) -> Union[str, List[str]]:
    """ Getter for release edition """
    return self.edition
  
  def get_edition_str(self, join_char: str = ',') -> str:
    """ Returns joined editions """
    return join_char.join(self.edition or [])

  def has_long_term_support(self) -> bool:
    """ Returns wheither the release has long term support or not """
    return self.lts
  
  def is_supported(self) -> bool:
    """ Checks if current release is supported """
    if self.end_of_life is None:
      return True
    
    return days_diff(self.end_of_life, reverse=True) > 0

  def compare_edition(self, edition: str = None) -> bool:
    """ Checks if the given edition(s) match release edition """
    return edition is None or edition in self.edition
  
  def support_str(self) -> str:
    """ Returns a string based on current support status """
    return "Ongoing" if self.is_supported() else "Retired"
  
  def support_state(self) -> str:
    """ Returns a string based on the supported status """
    support_days = days_diff(self.end_of_life, reverse=True)
    state = f"{abs(support_days)} days"
    
    if support_days > 0:
      state = f"Ends in {state}"
      
    else:
      state = f"Ended {state} ago"
      
    return state
  
  def add_vuln(self, vuln: str) -> None:
    """ Adds a vulnerability to the current release """
    self.vulnerabilities.add(vuln)

  def compare_values(self, version: Union[int, str], edition: Union[str, List[str]], lts: bool) -> bool:
    """ Compares current release to given values """
    return (
      self.version == version and
      self.compare_edition(edition) and
      self.lts == lts
    )

  def __eq__(self, other: SoftwareRelease) -> bool:
    """ Release comparison """
    return self.compare_values(
      version=other.get_version(),
      edition=other.get_edition(),
      lts=other.has_long_term_support()
    )

  def to_string(self, show_version: bool = False) -> str:
    """ Converts current release to a string """
    name = f"{self.software.get_name()} {self.label or ''}"
    name = f"{name.strip()} ({self.get_edition_str()})"

    if show_version:
      name = f"{name.strip()}({self.version})"

    return name.strip()

  def to_dict(self) -> Dict:
    """ Converts current release into a dict """
    return {
      "software": self.software.get_name(),
      "label": self.label,
      "full_name": self.to_string(),
      "version": self.version,
      "edition": self.edition,
      "release": soft_date(self.release_date),
      "support": soft_date(self.active_support),
      "eol": soft_date(self.end_of_life),
      "is_supported": self.is_supported(),
      "support_state": self.support_state()
    }

class SoftwareReleaseList(list):
  """ A class to manage lists of software releases """

  # ****************************************************************
  # Attributes & Constructors


  # ****************************************************************
  # Methods
  def contains(
    self,
    version: Union[int, str],
    edition: str = None,
    lts: bool = False,
  ) -> bool:
    """ Check if list contains element matching provided attributes """
    check = False
    
    for r in self:
      if r.compare_values(version, edition, lts):
        check = True

    return check

  def get(
    self,
    version: Union[int, str],
    edition: str = None,
    lts: bool = False,
  ) -> List[SoftwareRelease]:
    """ Returns releases matching arguments """
    res = []
    
    for r in self:
      if r.compare_values(version, edition, lts):
        res.append(r)
        
    return res

  def append(self, release: SoftwareRelease) -> None:
    if isinstance(release, SoftwareRelease):
      super().append(release)


class Software(Asset):
  """ A class to describe softwares """
  
  # ****************************************************************
  # Attributes & Constructors
  
  def __init__(
    self,
    id: Union[int, str],
    name: str,
    label: str,
    software_type: SoftwareType = SoftwareType.APPLICATION,
    editor: Union[str, List[str]] = None,
    description: str = None,
  ):
    """ Constructor """
    super().__init__(id=id, name=name, label=label, type=AssetType.SOFTWARE, desctiption=description)
    
    self.editor = editor
    self.type = software_type
    self.releases = SoftwareReleaseList()

  # ****************************************************************
  # Methods
  
  def get_editor(self) -> str:
    """ Getter for software editor """
    return self.editor
  
  def get_releases(self) -> SoftwareReleaseList:
    """ Getter for software releases """
    return self.releases

  def set_editor(self, editor: Union[str, List[str]]) -> None:
    """ Setter for software editor """
    self.editor = editor
    
  def add_release(self, new_release: SoftwareRelease) -> None:
    """ Adds a release to the list of software releases """
    self.releases.append(new_release)

  def retired_releases(self) -> List[SoftwareRelease]:
    """ Gets a list of retired releases """
    return [ r.to_string() for r in self.releases if not r.is_supported() ]

  def supported_releases(self) -> List[SoftwareRelease]:
    """ Gets a list of retired releases """
    return [ r.to_string() for r in self.releases if r.is_supported() ]
  
  def map_rel_by_version(self) -> Dict:
    """ Maps software releases using version numbers """
    rel_map = {}
    
    for r in self.releases:
      if r.get_version() not in rel_map.keys():
        rel_map[r.get_version()] = SoftwareReleaseList()

      rel_map[r.get_version()].append(r)
      
    return rel_map
  
  def to_dict(self) -> Dict:
    """ Converts the current instance into a dict """
    base_dict = super().to_dict()
    return {
      **base_dict,
      "editor": self.editor,
      "releases": ','.join([ r.to_string() for r in self.releases ]),
      "supported_releases": ','.join(self.supported_releases()),
      "retired_releases": ','.join(self.retired_releases())
    }
