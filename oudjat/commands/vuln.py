"""A module dedicated to the Vuln command."""

from multiprocessing import Pool
from typing import Dict

from oudjat.control.vulnerability import CVE
from oudjat.utils import ColorPrint

from .target import Target


class Vuln(Target):
    """CVE Target."""

    def __init__(self, options: Dict) -> None:
        """
        Create a new instance of the Vuln command.

        Args:
            options (Dict): options passed to the command
        """

        super().__init__(options)

        self.unique_cves = set()
        target_cves = set(self.options["TARGET"])

        print(f"{len(target_cves)} CVEs to investigate...\n")

        for ref in target_cves:
            try:
                cve = CVE(ref)
                self.unique_cves.add(cve)

            except ValueError:
                ColorPrint.red(f"Invalid CVE reference provided {ref}")

    def cve_process(self, cve: "CVE") -> Dict:
        """
        Process ran on each cve.

        Args:
            cve (CVE): the CVE to run the process on.

        Returns:
            Dict: CVE data
        """

        cve.parse_nist()
        return cve.to_dict(minimal=False)

    def run(self) -> None:
        """Run cve target."""

        with Pool(processes=5) as pool:
            for cve_dict in pool.imap_unordered(self.cve_process, self.unique_cves):
                self.results.append(cve_dict)

        if self.options["--export-csv"]:
            super().res_2_csv()
