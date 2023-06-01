""" Several functions that aim to parse a certfr page """
import re
from datetime import datetime
from enum import Enum

import requests
from bs4 import BeautifulSoup

from oudjat.utils.color_print import ColorPrint
from oudjat.watchers.cve import CVE, CVE_REGEX

URL_REGEX = r'http[s]?:\/\/(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
CERTFR_REF_REGEX = r'CERTFR-\d{4}-(?:ALE|AVI|CTI|IOC|DUR)-\d{3,4}'
CERTFR_LINK_BASE = "https://www.cert.ssi.gouv.fr"
CERTFR_LINK_REGEX = r'https:\/\/www\.cert\.ssi\.gouv\.fr\/(?:alerte|avis|cti|ioc|dur)\/CERTFR-\d{4}-(?:ALE|AVI|CTI|IOC|DUR)-\d{3,4}\/?'


class RiskValues(Enum):
  """ Enumeration describing possible risk values """
  N_A = "Non spécifié par l'éditeur"
  EOP = "Élévation de privilèges"
  RCE = "Exécution de code"
  DOS = "Déni de service"
  SFB = "Contournement"
  IDT = "Usurpation"
  ID = "Atteinte à la confidentialité"
  TMP = "Atteinte à l'intégrité"
  XSS = "Injection de code"


class CERTFRPageTypes(Enum):
  """ Enumeration describing possible CERTFR page types """
  ALE = "alerte"
  AVI = "avis"
  CTI = "cti"
  IOC = "ioc"
  DUR = "dur"


class CERTFR:
  """ CERTFR class addressing certfr page behavior """

  # ****************************************************************
  # Attributes & Constructors

  ref = ""
  title = ""
  date_initial = ""
  date_last = ""
  sources = []
  cve_list = set()
  risks = set()
  affected_products = []
  documentations = []
  link = ""
  page_type = ""
  CVE_RESOLVED = False

  def __init__(self, ref, title=""):
    """ Constructor """
    self.set_ref(ref)
    self.resolve_type_from_ref()
    self.resolve_link()
    self.title = title

  # ****************************************************************
  # Getters & Setters

  def get_ref(self):
    """ Getter for the reference """
    return self.ref

  def get_risks(self, short=True):
    """ Get the list of risks """
    return [r.name if short else r.value for r in self.risks]

  def get_cve_refs(self):
    """ Returns the refs of all the related cves """
    return [cve.get_ref() for cve in self.cve_list]

  def get_max_cve(self, cve_data=None):
    """ Returns the highest cve """
    print(f"\nResolving most critical CVE for {self.ref}")
    if not self.CVE_RESOLVED:
      self.resolve_cve_data(cve_data)

    return max(self.cve_list, key=lambda cve: cve.get_cvss())

  def get_title(self):
    """ Getter for the title """
    return self.title

  def get_link(self):
    """ Getter for the link """
    return self.link

  def get_documentations(self, filter=None):
    """ Getter for the documentations """
    docs = self.documentations

    if filter is not None and filter != "":
      docs = [d for d in self.documentations if filter not in d]

    return docs

  def set_ref(self, ref):
    """ Setter for CERTFR ref """
    if CERTFR.is_valid_ref(ref):
      self.ref = ref

    else:
      raise (f"Invalid CERTFR ref provided : {ref}")

  def set_link(self, link):
    """ Setter for CERTFR link """
    if CERTFR.is_valid_link(link):
      self.link = link

    else:
      ColorPrint.red(f"Invalid CERTFR link provided: {link}")

  def append_source(self, source):
    """ Appends a source to the list of sources """
    self.sources.append(source)

  # ****************************************************************
  # Resolvers

  def resolve_type_from_ref(self):
    """ Resolves CERTFR page type from ref """
    split_type = self.ref.split("-")[-2]
    certfr_types = {e.name: e.value for e in CERTFRPageTypes}
    self.page_type = certfr_types[split_type]

  def resolve_link(self):
    """ Resolves CERTFR page link based on CERTFR page type and ref """
    if self.page_type == "":
      ColorPrint.red(
          "You need to resolve CERTFR page type before trying to resolve link")
      return

    self.link = f"{CERTFR_LINK_BASE}/{self.page_type}/{self.ref}/"

  def resolve_cve_data(self, cve_data=None):
    """ Resolves CVE data for all related CVE """
    print(f"\nResolving CVE data for {self.ref}...")
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
        cve.parse_nist()

    self.CVE_RESOLVED = True

  # ****************************************************************
  # Parsers

  def parse_cve(self, content):
    """ Extract all CVE refs in content and look for the highest CVSS """
    cve_refs = set(re.findall(CVE_REGEX, content.text))
    for ref in cve_refs:
      self.cve_list.add(CVE(ref))

  def parse_products(self, content):
    """ Generates a list of affected products based on the corresponding <ul> element """
    product_list = content.find_all("ul")[1]
    self.affected_products = [li.text for li in product_list.find_all("li")]

  def parse_documentations(self, content):
    """ Extracts data from the certfr documentation list """
    self.documentations = re.findall(URL_REGEX, content.text)

  def parse_risks(self, content):
    """ Generates a list out of a the <ul> element relative to the risks """

    for risk in list(RiskValues):
      if risk.value.lower() in content.text.lower():
        self.risks.add(risk)

  def parse_meta(self, meta_section):
    """ Parse meta section """
    meta_tab = meta_section.find_all("table")[0]
    tab_cells = []

    for row in meta_tab.find_all("tr"):
      cell_txt = row.find_all("td")[-1].text
      tab_cells.append(self.clean_str(cell_txt))

    if self.title == "":
      self.title = tab_cells[1]

    self.date_initial = tab_cells[2]
    self.date_last = tab_cells[3]
    self.sources = tab_cells[-2].split("\n")

  def parse_content(self, section):
    """ Parse content section """
    self.parse_cve(section)
    self.parse_risks(section)
    self.parse_products(section)
    self.parse_documentations(section)

  def parse(self):
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

  def to_string(self):
    """ Converts current instance into a string """
    return f"{self.ref}: {self.title}"

  def to_dictionary(self):
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
  def is_valid_ref(ref):
    """ Returns whether the ref is valid or not """
    return re.match(CERTFR_REF_REGEX, ref)

  @staticmethod
  def is_valid_link(link):
    """ Returns whether the link is valid or not """
    return re.match(CERTFR_LINK_REGEX, link)

  @staticmethod
  def clean_str(str):
    return str.replace("\r", "")

  @staticmethod
  def get_ref_from_link(link):
    """ Returns a CERTFR ref based on a link """
    if not re.match(CERTFR_LINK_REGEX, link):
      ColorPrint.red(f"Invalid CERTFR link provided: {link}")
      return

    return re.findall(CERTFR_REF_REGEX, link)[0]

  @staticmethod
  def parse_feed(feed_url, date_str_filter=None):
    """ Parse a CERTFR Feed page """
    try:
      feed_req = requests.get(feed_url)
      feed_soup = BeautifulSoup(feed_req.content, "xml")

    except Exception as e:
      print(
          e, f"A parsing error occured for {feed_url}: {e}\nCheck if the page has the expected format.")

    feed_items = feed_soup.find_all("item")
    filtered_feed = feed_items

    if date_str_filter:
      valid_date_format = "%Y-%m-%d"

      try:
        date_filter = datetime.strptime(date_str_filter, valid_date_format)
        filtered_feed = []

        for item in feed_items:
          date_str = item.pubDate.text.split(" +0000")[0]
          date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S")

          if date > date_filter:
            certfr_page = CERTFR(
                ref=CERTFR.get_ref_from_link(item.link.text))
            filtered_feed.append(certfr_page)

      except ValueError as e:
        ColorPrint.red(
            f"Invalid date filter format. Please provide a date filter following the pattern YYYY-MM-DD !")

    return filtered_feed
