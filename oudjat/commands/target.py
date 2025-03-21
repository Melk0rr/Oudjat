from multiprocessing import Pool
from typing import Dict, List

from oudjat.model.vulnerability import CVE
from oudjat.utils import ColorPrint, export_csv, import_csv, str_file_option_handle

from .base import Base


class Target(Base):
    """Main enumeration module"""

    def __init__(self, options: Dict):
        """Initialization function"""
        super().__init__(options)
        self.results: List[Dict] = []

        str_file_option_handle(self, "TARGET", "FILE")

        # If a csv of cve is provided, populate CVE instances
        if self.options["--cve-list"]:
            print("Importing cve data...")

            def cve_import_callback(reader):
                cve_instances = []

                with Pool(processes=5) as pool:
                    for cve in pool.imap_unordered(CVE.create_from_dict, reader):
                        cve_instances.append(cve)

                return cve_instances

            cve_import = import_csv(self.options["--cve-list"], cve_import_callback)
            self.options["--cve-list"] = cve_import

    def handle_exception(self, e: Exception, message: str = "") -> None:
        """Function handling exception for the current class"""
        if self.options["--verbose"]:
            print(e)

        if message:
            ColorPrint.red(message)

    def res_2_csv(self) -> None:
        """Write the results into a CSV file"""
        print("\nExporting results to csv...")
        export_csv(self.results, self.options["--export-csv"], "|")

    def run(self) -> None:
        """Main function called from the cli module"""
        # Retreive IP of target and run initial configuration
        self.init()
