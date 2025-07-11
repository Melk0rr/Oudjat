"""A module dedicated to the cert command."""

from multiprocessing import Pool
from typing import Dict, List

from oudjat.connectors.cert.certfr import CERTFRConnector, CERTFRPage
from oudjat.control.vulnerability import CVE
from oudjat.utils.color_print import ColorPrint

from .target import Target


class Cert(Target):
    """A class to handle Cert command."""

    def __init__(self, options: Dict):
        """
        Create a new instance of Cert command.

        Args:
            options (Dict): options passed to the command.
        """

        super().__init__(options)

        self.connector = CERTFRConnector()
        self.connector.connect()

        self.unique_targets = set()

        # Handle keywords initialization
        if self.options["--keywords"] or self.options["--keywordfile"]:
            super().str_file_option_handle("--keywords", "--keywordfile")

        # If option is provided: retrieve alerts from RSS feed
        if self.options["--feed"]:
            print("Parsing CERT pages from feed...")

            feed_items = CERTFRConnector.parse_feed(
                self.options["TARGET"][0], self.options["--filter"]
            )
            self.options["TARGET"] = feed_items

            print(f"\n{len(feed_items)} alerts since the {self.options['--filter']}")

        for target in self.options["TARGET"]:
            if CERTFRPage.is_valid_ref(target) or CERTFRPage.is_valid_link(target):
                self.unique_targets.add(target)
                ColorPrint.green(f"Gathering data from {target}")

            else:
                ColorPrint.red(
                    f"Error connecting to {target}! Make sure it is a resolvable address"
                )

    def keyword_check(self, target: "CERTFRPage") -> List[str]:
        """
        Look for provided keywords in the results.

        Args:
            target (CERTFRPage): page to search the keywords in.
        """

        matched = [k for k in self.options["--keywords"] if k.lower() in target.get_title().lower()]

        msg = f"No match for {target.get_ref()}..."
        if len(matched) > 0:
            msg = f"\n{target.get_ref()} matched for {'-'.join(matched)}"

        print(msg)
        return matched

    def cert_process(self, target: str) -> Dict:
        """
        CERT process method to deal with cert data.

        Args:
            target (str): url to run the process on
        """
        cert_data = {}

        try:
            cert_page = self.connector.search(search_filter=target)[0]
            cert_data = cert_page.to_dict()

            # Resolve CVE data
            CVE.resolve_cve_data(cves=cert_page.get_cves(), cve_data=self.options["--cve-list"])
            max_cves = CVE.max_cve(cert_page.get_cves())

            cert_data["cvss"] = 0

            if max_cves is not None and len(max_cves) > 0:
                cert_data["cves"] = [cve.get_ref() for cve in max_cves]
                cert_data["cvss"] = max_cves[0].get_cvss()
                cert_data["documentations"].extend([cve.get_link() for cve in max_cves])

                # Joins lists if any
                if self.options["--export-csv"]:
                    for k, v in cert_data.items():
                        if isinstance(v, list):
                            cert_data[k] = ",".join(v)

            # If keywords are provided in any way: compare them with results
            cert_data["match"] = ""
            if self.options["--keywords"]:
                cert_data["match"] = "-".join(self.keyword_check(cert_page))

        except Exception as e:
            ColorPrint.red(f"An error occured while processing {target}\n{e}")

        return cert_data

    def run(self) -> None:
        """Run the Cert command from the cli module."""

        with Pool(processes=5) as pool:
            for cert_data in pool.imap_unordered(self.cert_process, self.unique_targets):
                self.results.append(cert_data)

        if self.options["--export-csv"]:
            super().res_2_csv()
