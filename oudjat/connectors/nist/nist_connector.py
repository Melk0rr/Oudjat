import json
import re
from typing import Dict, List, Union

import requests

from oudjat.connectors import Connector
from oudjat.utils import ColorPrint

NIST_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"


class NistConnector(Connector):
    """NIST API Connector class"""

    # ****************************************************************
    # Attributes & Constructors

    def __init__(self):
        """Constructor"""

        super().__init__(target=NIST_API_URL)

    # ****************************************************************
    # Methods

    def connect(self, target: str) -> None:
        """Test connection to NIST API"""
        self.connection = None

        try:
            headers = {"Accept": "application/json"}
            req = requests.get(target, headers=headers)

            if req.status_code == 200:
                self.connection = json.loads(req.content.decode("utf-8"))

        except ConnectionError as e:
            raise ConnectionError(f"Could not connect to {self.target}\n{e}")

    def search(
        self, search_filter: Union[str, List[str]], attributes: Union[str, List[str]] = None
    ) -> List[Dict]:
        """Searches the API for CVEs"""

        res = []

        if not isinstance(search_filter, list):
            search_filter = [search_filter]

        if attributes is not None and not isinstance(attributes, list):
            attributes = [attributes]

        for cve in search_filter:
            if not re.match(r"CVE-\d{4}-\d{4,7}", cve):
                continue

            cve_target = f"{self.target}?cveId={cve}"
            self.connect(cve_target)

            if self.connection is not None:
                vuln = self.connection.get("vulnerabilities", [])

                if len(vuln) > 0:
                    vuln = vuln[0].get("cve", {})

                else:
                    ColorPrint.yellow(f"No data for vulnerability {cve}")
                    continue

                if attributes is not None:
                    vuln = {k: v for k, v in vuln.items() if k in attributes}

                res.append(vuln)

        return res
