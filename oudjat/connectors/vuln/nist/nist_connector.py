"""A module that handles the connection to Nist and Nist API."""

import re
from typing import Dict, List, Tuple, Union

from oudjat.utils.color_print import ColorPrint

from ..cve_connector import CVEConnector


class NistConnector(CVEConnector):
    """A class that handles connection with Nist API to retrieve CVE informations."""

    # ****************************************************************
    # Attributes & Constructors

    URL = "https://nvd.nist.gov/"
    API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

    # ****************************************************************
    # Methods

    def search(
        self,
        search_filter: Union[str, List[str]],
        attributes: Union[str, List[str]] = None,
        raw: bool = False,
        **kwargs,
    ) -> List[Dict]:
        """
        Search the API for CVEs.

        Retrieves vulnerability information from the NIST API based on the provided CVE IDs.
        If `search_filter` is not a list, it converts it to one. Similarly, if `attributes` is provided but not a list, it converts it to a list.
        It iterates over each CVE ID in `search_filter`, constructs the API endpoint URL for that CVE, and connects to retrieve data.
        If a valid response is received, it extracts vulnerability information and filters it based on the specified attributes before appending it to the result list.

        Args:
            search_filter (Union[str, List[str]])       : A single CVE ID or a list of CVE IDs to be searched.
            attributes (Union[str, List[str]], optional): A single attribute name or a list of attribute names to filter the retrieved vulnerability data by. Defaults to None.
            raw (bool)                                  : Weither to return the raw result or the unified one
            kwargs (Dict)                               : Additional arguments that will be passed to connect method

        Returns:
            List[Dict]: A list of dictionaries containing filtered vulnerability information for each provided CVE ID.
        """

        res = []

        if not isinstance(search_filter, list):
            search_filter = [search_filter]

        if attributes is not None and not isinstance(attributes, list):
            attributes = [attributes]

        # Vuln filter function
        def key_in_attr(item: Tuple) -> bool:
            return item[0] in attributes

        for cve in search_filter:
            if not re.match(r"CVE-\d{4}-\d{4,7}", cve):
                continue

            cve_target = NistConnector.get_cve_api_url(cve)
            self.connect(cve_target, **kwargs)

            if self.connection is not None:
                vuln = self.connection.get("vulnerabilities", [])

                if len(vuln) > 0:
                    vuln = vuln[0].get("cve", {})

                else:
                    ColorPrint.yellow(f"No data for vulnerability {cve}")
                    continue

                if not raw:
                    vuln = self.unify_cve_data(vuln)

                if attributes is not None:
                    vuln = dict(filter(key_in_attr, vuln.items()))

                res.append(vuln)

        return res

    def unify_cve_data(self, cve: Dict) -> Dict:
        """
        Filter and reorganize cve data properties in order to obtain a unified format accross CVE connectors.

        Args:
            cve (Dict): cve data as a dictionary

        Returns:
            Dict: formated dictionary
        """

        base_format = self.UNIFIED_FORMAT

        try:
            base_format["id"] = cve.get("id")
            base_format["status"] = cve.get("vulnStatus", None)

            base_format["dates"]["published"] = cve.get("published", None)
            base_format["dates"]["updated"] = cve.get("lastModified", None)

            base_format["description"] = cve.get("descriptions", None)[0].get("value", None)
            base_format["source"] = [r["url"] for r in cve.get("references", [])]

            metrics = cve.get("metrics", {})

            if len(list(metrics)) > 0:
                metric_data = metrics.get(list(metrics.keys())[0], [])[0]
                cvss_data = metric_data.get("cvssData", {})

                base_format["metrics"]["score"] = cvss_data.get("baseScore", 0)
                base_format["metrics"]["version"] = float(cvss_data.get("version", 4.0))
                base_format["metrics"]["severity"] = cvss_data.get("baseSeverity", "INFO")

                base_format["vectors"]["vectorString"] = cvss_data.get("vectorString", "")
                base_format["vectors"]["attackVector"] = cvss_data.get("attackVector", None)

                base_format["requirements"]["privilegesRequired"] = cvss_data.get(
                    "privilegesRequired", None
                )
                base_format["requirements"]["attackRequirements"] = cvss_data.get(
                    "attackRequirements", "NONE"
                )

        except ValueError as e:
            raise ValueError(
                f"{__class__.__name__}.unify_cve_data::An error occured while unifying cve data...\n{e}"
            )

        return base_format

    # ****************************************************************
    # Static methods

    @staticmethod
    def get_cve_url(cve: str) -> str:
        """
        Return the Nist website URL of the given CVE.

        Args:
            cve (str): the ref string of the CVE

        Returns:
            str: Nist vuln detail URL based on the provided CVE
        """

        return f"{NistConnector.URL}vuln/detail/{cve}"

    @staticmethod
    def get_cve_api_url(cve: str) -> str:
        """
        Return the Nist website URL of the given CVE.

        Args:
            cve (str): the ref string of the CVE

        Returns:
            str: Nist vuln detail URL based on the provided CVE
        """

        return f"{NistConnector.API_URL}?cveId={cve}"
