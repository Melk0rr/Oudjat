""" Several functions that aim to parse a certfr page """
import re
import requests

from enum import Enum
from typing import List, Dict
from datetime import datetime
from bs4 import BeautifulSoup, element

from oudjat.utils.color_print import ColorPrint
from oudjat.model.cve import CVE, CVE_REGEX
from oudjat.connectors.cert.risk_types import RiskTypes
from oudjat.connectors.cert.certfr.certfr_page_types import CERTFRPageTypes

CERTFR_LINK_BASE = "https://www.cert.ssi.gouv.fr"

REF_TYPES = '|'.join([ pt.name for pt in CERTFRPageTypes ])
LINK_TYPES = '|'.join([ pt.value for pt in CERTFRPageTypes ])
URL_REGEX = r'http[s]?:\/\/(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
CERTFR_REF_REGEX = rf"CERTFR-\d{{4}}-(?:{REF_TYPES})-\d{{3,4}}"
CERTFR_LINK_REGEX = rf"https:\/\/www\.cert\.ssi\.gouv\.fr\/(?:{LINK_TYPES})\/{CERTFR_REF_REGEX}"


class CERTFRConnector:
  """ CERTFR class addressing certfr page behavior """

  # ****************************************************************
  # Attributes & Constructors

  def __init__(self, ref: str, title: str = None):
    """ Constructor """
    if not CERTFRConnector.is_valid_ref(ref) and not CERTFRConnector.is_valid_link(ref):
      raise ValueError(f"Invalid CERTFR ref provided : {ref}")
    
    self.ref = ref if CERTFRConnector.is_valid_ref(ref) else CERTFRConnector.get_ref_from_link(ref)
    self.title = title
    self.date_initial = None
    self.date_last = None
    self.sources = []
    self.cve_list = set()
    self.risks = set()
    self.affected_products = []
    self.documentations = []
    self.CVE_RESOLVED = False

    # Set page type
    ref_type = re.search(rf"(?:{REF_TYPES})", self.ref).group(0)
    self.page_type = CERTFRPageTypes[ref_type].value

    self.link = f"{CERTFR_LINK_BASE}/{self.page_type}/{self.ref}/"

  # ****************************************************************
  # Getters & Setters

  def get_ref(self) -> str:
    """ Getter for the reference """
    return self.ref

  def get_risks(self, short: bool = True) -> List[str]:
    """ Get the list of risks """
    return [ r.name if short else r.value for r in self.risks ]

  def get_cve_refs(self) -> List[str]:
    """ Returns the refs of all the related cves """
    return [ cve.get_ref() for cve in self.cve_list ]

  def get_max_cve(self, cve_data: List["CVE"] = None) -> "CVE":
    """ Returns the highest cve """
    if len(self.cve_list) <= 0:
      print("No comparison possible: no CVE related")
      return None
    
    print(f"\nResolving most critical CVE for {self.ref}")

    if not self.CVE_RESOLVED:
      self.resolve_cve_data(cve_data)

    max_cve = max(self.cve_list, key=lambda cve: cve.get_cvss())
    self.documentations.append(max_cve.get_link())
    print(f"\n{self.ref} max CVE is {max_cve.get_ref()}({max_cve.get_cvss()})")

    return max_cve

  def get_title(self) -> str:
    """ Getter for the title """
    return self.title

  def get_link(self) -> str:
    """ Getter for the link """
    return self.link

  def get_documentations(self, filter: str = None) -> List[str]:
    """ Getter for the documentations """
    docs = self.documentations

    if filter is not None and filter != "":
      docs = [ d for d in self.documentations if filter not in d ]

    return docs

  def set_link(self, link: str) -> None:
    """ Setter for CERTFR link """
    if CERTFRConnector.is_valid_link(link):
      self.link = link

    else:
      ColorPrint.red(f"Invalid CERTFR link provided: {link}")

  def append_source(self, source: str) -> None:
    """ Appends a source to the list of sources """
    self.sources.append(source)

  # ****************************************************************
  # Resolvers

  def resolve_cve_data(self, cve_data: List["CVE"]) -> None:
    """ Resolves CVE data for all related CVE """
    print(f"\nResolving {len(self.cve_list)} CVE data for {self.ref}...")

    for cve in self.cve_list:
      # Checks if the current CVE can be found in the provided cve list. If not : parse Nist page
      cve_imported = False
      if cve_data:
        cve_search = CVE.find_cve_by_ref(ref=cve.get_ref(), cve_list=cve_data)
        
        if cve_search:
          print(f"Found {cve.get_ref()} in CVE list ! Copying data...")
          cve.copy(cve_search)
          cve_imported = True

      if not cve_imported:
        cve.parse_nist(verbose=False)

    self.CVE_RESOLVED = True

  # ****************************************************************
  # Parsers

  def parse_cve(self, content: BeautifulSoup) -> None:
    """ Extract all CVE refs in content and look for the highest CVSS """
    cve_refs = set(re.findall(CVE_REGEX, content.text))
    for ref in cve_refs:
      self.cve_list.add(CVE(ref))

    print(f"{len(self.cve_list)} CVEs related to {self.ref}")

  def parse_products(self, content: BeautifulSoup) -> None:
    """ Generates a list of affected products based on the corresponding <ul> element """
    product_list = content.find_all("ul")[1]
    self.affected_products = [li.text for li in product_list.find_all("li")]

  def parse_documentations(self, content: BeautifulSoup) -> None:
    """ Extracts data from the certfr documentation list """
    self.documentations = re.findall(URL_REGEX, content.text)

  def parse_risks(self, content: BeautifulSoup) -> None:
    """ Generates a list out of a the <ul> element relative to the risks """

    for risk in list(RiskTypes):
      if risk.value.lower() in content.text.lower():
        self.risks.add(risk)

  def parse_meta(self, meta_section: element.Tag) -> None:
    """ Parse meta section """
    meta_tab = meta_section.find_all("table")[0]
    tab_cells = {}

    for row in meta_tab.find_all("tr"):
      cells = row.find_all("td")
      c_name = cells[0].text.strip()
      c_value = cells[-1].text.strip()

      tab_cells[self.clean_str(c_name)] = self.clean_str(c_value)

    if not self.title:
      self.title = tab_cells["Titre"]

    self.date_initial = tab_cells["Date de la première version"]
    self.date_last = tab_cells["Date de la dernière version"]
    clean_sources = tab_cells["Source(s)"].split("\n")
    clean_sources = [
      re.sub(r'\s+', ' ', line).strip()
      for line in clean_sources if re.sub(r'\s+', '', line).strip()
    ]
    self.sources = clean_sources

  def parse_content(self, section: element.Tag) -> None:
    """ Parse content section """
    self.parse_cve(section)
    self.parse_risks(section)
    self.parse_products(section)
    self.parse_documentations(section)

  def parse(self) -> None:
    """ Main function to parse a certfr page """
    print(f"\n* Parsing {self.ref} *")

    # Handle possible connection error
    try:
      req = requests.get(self.link)
      soup = BeautifulSoup(req.content, 'html.parser')

    except ConnectionError:
      ColorPrint.red(
          f"Error while requesting {self.ref}. Make sure it is a valid certfr reference")

    # Handle parsing error
    try:
      article_sections = soup.article.find_all("section")
      self.parse_meta(article_sections[0])
      self.parse_content(article_sections[1])

    except Exception as e:
      ColorPrint.red(
          f"A parsing error occured for {self.ref}: {e}\nCheck if the page has the expected format.")

  # ****************************************************************
  # Converters

  def to_string(self) -> str:
    """ Converts current instance into a string """
    return f"{self.ref}: {self.title}"

  def to_dictionary(self) -> Dict:
    """ Converts current instance into a dictionary """
    return {
        "ref": self.ref,
        "title": self.title,
        "date_initial": self.date_initial,
        "date_last": self.date_last,
        "sources": self.sources,
        "cve": self.get_cve_refs(),
        "risks": self.get_risks(),
        "products": self.affected_products,
        "docs": self.get_documentations(filter="cve.org"),
        "link": self.link
    }

  # ****************************************************************
  # Static methods

  @staticmethod
  def is_valid_ref(ref: str) -> bool:
    """ Returns whether the ref is valid or not """
    return re.match(CERTFR_REF_REGEX, ref)

  @staticmethod
  def is_valid_link(link: str) -> bool:
    """ Returns whether the link is valid or not """
    return re.match(CERTFR_LINK_REGEX, link)

  @staticmethod
  def clean_str(str: str) -> str:
    return str.replace("\r", "").strip()

  @staticmethod
  def get_ref_from_link(link: str) -> str:
    """ Returns a CERTFR ref based on a link """
    if not re.match(CERTFR_LINK_REGEX, link):
      raise ValueError(f"Invalid CERTFR link provided: {link}")

    return re.findall(CERTFR_REF_REGEX, link)[0]

  @staticmethod
  def parse_feed(feed_url: str, date_str_filter: str = None) -> List[str]:
    """ Parse a CERTFR Feed page """
    try:
      feed_req = requests.get(feed_url)
      feed_soup = BeautifulSoup(feed_req.content, "xml")

    except Exception as e:
      print(
          e, f"A parsing error occured for {feed_url}: {e}\nCheck if the page has the expected format.")

    feed_items = feed_soup.find_all("item")
    filtered_feed = []

    for item in feed_items:
      certfr_ref = CERTFRConnector.get_ref_from_link(item.link.text)

      if date_str_filter:
        try:
          valid_date_format = "%Y-%m-%d"
          date_filter = datetime.strptime(date_str_filter, valid_date_format)          

          date_str = item.pubDate.text.split(" +0000")[0]
          date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S")

          if date > date_filter:
            filtered_feed.append(certfr_ref)

        except ValueError as e:
          ColorPrint.red(
              f"Invalid date filter format. Please provide a date filter following the pattern YYYY-MM-DD !")
          
      else:
        filtered_feed.append(certfr_ref)

    return filtered_feed