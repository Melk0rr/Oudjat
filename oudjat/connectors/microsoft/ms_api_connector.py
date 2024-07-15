import re
import json
import requests

from datetime import datetime
from typing import List, Dict, Union, Any

from oudjat.utils.file import export_csv
from oudjat.utils.color_print import ColorPrint

################################################################################
# Useful content
CVE_REGEX = r'CVE-\d{4}-\d{4,7}'
CVRF_ID_REGEX = r'\d{4}-[a-zA-Z]{3}'
KB_NUM_REGEX = r'\d{7}'
MS_PRODUCT_REGEX = r'\d{4,5}(?:-\d{4,5})?'

API_REQ_HEADERS = { 'Accept': 'application/json' }
API_BASE_URL = "https://api.msrc.microsoft.com/"

def get_cvrf_id_from_cve(cve: str) -> str:
  """ Returns a CVRF ID based on a CVE ref """
  if not re.match(CVE_REGEX, cve):
    raise(f"Invalid CVE provided: {cve}")

  # API URL to retreive CVRF id from CVE
  id_url = f"{API_BASE_URL}Updates('{cve}')"

  cvrf_id = None

  # Retreive CVRF ID
  id_resp = requests.get(id_url, headers=API_REQ_HEADERS)
  if id_resp.status_code != 200:
    raise ConnectionError(f"Could not connect to {self.id_url}")

  data = json.loads(id_resp.content)
  cvrf_id = data["value"][0]["ID"]

  return cvrf_id

################################################################################
# MS API Connector class
class MSAPIConnector:
  """ Connector to interact with Microsoft API """

  def __init__(self):
    """ Constructor """

    self.date = datetime.now()
    self.api_version = str(self.date.year)

    self.documents = {}

  def get_cvrf_doc(self, cvrf_id: str = None) -> "CVRFDocument":
    """ Retreives an existing document instance or create new one """
    cvrf = self.documents.get(cvrf_id, None)
    if cvrf is None:
      cvrf = doc=CVRFDocument(cvrf_id)
      self.add_document(cvrf)

    return self.documents[cvrf_id]
  
  def add_document(self, doc: "CVRFDocument") -> None:
    """ Adds a CVRF document to the list """
    if doc.get_doc_id() not in self.documents.keys():
      self.documents[doc.get_doc_id()] = doc

  def get_cve_knowledge_base(self, cve: str) -> List[Dict]:
    """ Retreives CVE informations like KB, affected products, etc """
    cvrf_id = get_cvrf_id_from_cve(cve)
    cvrf = self.get_cvrf_doc(cvrf_id)
    cvrf.parse_vulnerabilities()

    cve = cvrf.vulns[cve]

    return cve.get_flat_dict()
  

################################################################################
# CVRF Document class
class CVRFDocument:
  """ Class to manipulate MS CVRF documents """

  def __init__(self, id: str):
    """ Constructor """
    if not re.match(CVRF_ID_REGEX, id):
      raise ValueError(f"CVRF ID must follow the 'YYYY-MMM' format !")

    self.id = id
    self.url = f"{API_BASE_URL}cvrf/{self.id}"

    url_resp = requests.get(self.url, headers=API_REQ_HEADERS)
    
    if url_resp.status_code != 200:
      raise ConnectionError(f"Could not connect to {self.url}")
    
    ColorPrint.green(f"{self.url}")
    self.content = json.loads(url_resp.content)
    
    self.products = {}
    self.vulns = {}
    self.kbs = {}

  def get_doc_id(self) -> str:
    """ Getter for document id """
    return self.id

  def get_products(self) -> Dict[str, "MSProduct"]:
    """ Returns MS products mentionned in the document """
    if not self.products:
      self.parse_products()
    
    return self.products

  def get_vulnerabilities(self) -> Dict[str, "MSVuln"]:
    """ Returns vulnerabilities mentionned in the document """
    if not self.vulns:
      self.parse_vulnerabilities()
      
    return self.vulns
    
  def get_kbs(self) -> Dict[str, "MSRemed"]:
    """ Returns MS KBs mentionned in the document """
    if not self.kbs:
      self.parse_vulnerabilities()
      
    return self.kbs

  def add_product(self, product: "MSProduct") -> None:
    """ Adds a product to the list of the document products """
    if product.get_id() not in self.products.keys():
      self.products[product.get_id()] = product

  def add_vuln(self, vuln: "MSVuln") -> None:
    """ Adds a vuln to the list of the document vulnerabilities """
    if vuln.get_cve() not in self.vulns.keys():
      self.vulns[vuln.get_cve()] = vuln

  def add_kb(self, kb: "MSRemed") -> None:
    """ Adds a kb to the list of the kb mentionned in the document """
    if kb.get_number() not in self.kbs.keys():
      self.kbs[kb.get_number()] = kb

  def parse_products(self) -> None:
    """ Retreives the products mentionned in the document """
    prod_tree = self.content["ProductTree"]["Branch"][0]["Items"]
    for b in prod_tree:
      product_type = b["Name"]

      for p in b["Items"]:
        pid = p["ProductID"]
        prod = MSProduct(pid=pid, name=p["Value"], product_type=b["Name"])
        self.add_product(prod)

  def parse_vulnerabilities(self) -> None:
    """ Retreives the vulnerabilities mentionned in the document """
    
    if not self.products:
      self.parse_products()

    for v in self.content["Vulnerability"]:
      vuln = MSVuln(cve=v["CVE"])

      for kb in v["Remediations"]:
        kb_num = kb["Description"]["Value"]
        
        mskb = MSRemed(num=kb_num)
        mskb.set_products([ self.products[id] for id in kb.get("ProductID", []) ])

        self.add_kb(mskb)
        vuln.add_kb(kb_num=kb_num, kb=mskb)
        
      self.add_vuln(vuln)
      
    
################################################################################
# MS API Vuln class
class MSVuln:
  """ Class to manipulate CVE data related to MS products """

  def __init__(self, cve: str):
    """ Constructor """

    if not re.match(CVE_REGEX, cve):
      raise(f"Invalid CVE provided: {cve}")

    self.cve = cve
    self.kbs = {}
    self.products = {}

  def get_cve(self) -> str:
    """ Getter for CVE """
    return self.cve
  
  def get_remediations(self) -> Dict[str, "MSRemed"]:
    """ Getter for KB list """
    return self.kbs
  
  def get_remediation_numbers(self) -> List[int]:
    """ Returns kb numbers """
    return [ kb_number for kb_number in self.kbs.keys() ]

  def get_impacted_products(self) -> Dict[str, "MSProduct"]:
    """ Getter for impacted product list """
    return self.products

  def add_kb(self, kb_num: int, kb: "MSRemed") -> None:
    """ Adds a KB to vuln KB list """
    if not (re.match(KB_NUM_REGEX, kb_num) or re.match(r'(\w+)$', kb_num)):
      ColorPrint.yellow(f"Invalid KB number provided for {self.cve}:\n{kb_num}")
      return

    ColorPrint.green(f"New kb added for {self.cve}: {kb_num}")
    self.kbs[kb_num] = kb

  def get_flat_dict(self) -> List[Dict]:
    """ Converts kbs into dictionaries """
    kb_flat_dicts = []
    for k in self.kbs.values():
      kb_flat_dicts.extend(k.get_flat_dict())

    return [
      { **kb_dict, "cve": self.cve }
      for kb_dict in kb_flat_dicts
    ]

  def to_dict(self) -> Dict[str, Any]:
    """ Converts current vuln into a dict """
    return {
      "cve": self.cve,
      "kbs": self.kbs.keys(),
      "products": [ p.to_string() for p in self.products.values() ]
    }


################################################################################
# MS Remed class
class MSRemed:
  """ Class to manipulate MS KBs """

  def __init__(self, num: int):
    """ Constructor """
    self.number = num

    self.type = "KB"
    if not re.match(KB_NUM_REGEX, self.number):
      self.type = "Patch"
      
    self.products = {}
    
  def set_products(self, products: List["MSProduct"]) -> None:
    """ Setter for kb products """
    self.products = { 
      p.get_id(): p
      for p in products if p.get_id() not in self.products.keys()
    }

  def get_number(self) -> int:
    """ Getter for kb number """
    return self.number

  def get_flat_dict(self) -> List[Dict]:
    """ Converts patched products into dictionaries """
    return [ { **p.to_dict(), "remed": self.number, "remed_type": self.type } for p in self.products.values() ]

  def to_dict(self) -> Dict[str, Any]:
    """ Converts the current kb into a dict """
    return {
      "number": self.number,
      "patched_products": [ p.to_string() for p in self.products.values() ]
    }


################################################################################
# MS Product class
class MSProduct:
  """ Class to manipulate MS product """

  def __init__(self, pid: str, name: str, product_type: str):
    """ Constructor """
    
    if not re.match(MS_PRODUCT_REGEX, pid):
      raise ValueError(f"Invalid MS product ID: {pid}")

    self.pid = pid
    self.name = name
    self.type = product_type
    self.subType = None
    
    if self.type == "ESU" or self.type == "Windows":
      self.subType = "Workstation"

      if "Server" in self.name:
        self.cptType = "Server"

  def get_id(self) -> str:
    """ Getter for product id """
    return self.pid
        
  def to_string(self) -> str:
    """ Converts instance to string """
    return f"{self.pid}: {self.name}"

  def to_dict(self) -> Dict[str, str]:
    """ Converts instance to dict """
    return {
      "product_id": self.pid,
      "product_name": self.name,
      "product_type": self.type
    }
