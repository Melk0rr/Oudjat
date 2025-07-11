"""A module to handle KPI command."""

import json
from multiprocessing import Pool
from typing import Dict, List, Tuple

from oudjat.control.data import DataFilter, DataSet
from oudjat.control.kpi import KPI
from oudjat.utils.color_print import ColorPrint, FileHandler

from .base import Base


class KPIFactory(Base):
    """A class to handle KPI command."""

    def __init__(self, options: Dict):
        """
        Create a new instance of KPIFactory command.

        Args:
            options (Dict): options passed to the command
        """

        super().__init__(options)

        config_file = open(self.options["--config"])
        self.config = json.load(config_file)

        self.options["--sources"] = list(filter(None, self.options["--sources"].split(",")))

        if self.options["--history"]:
            self.options["--history"] = list(filter(None, self.options["--history"].split(",")))

        self.iteration_count = 1
        if self.options["--history"]:
            self.iteration_count = len(self.options["--history"])

        # Separating the different types of source files
        self.data_sources = self.assign_sources()
        self.source_index = 0
        self.current_sources = {}

        config_filters = self.config.get("filters", {})
        self.filters = {
            k: DataFilter(fieldname=f["field"], value=f["value"]) for k, f in config_filters.items()
        }
        self.scopes = {}

        self.kpi_list = self.config["kpis"]
        self.results = []

    def assign_sources(self) -> Dict:
        """Assign data sources filenames to matching kpi types."""

        sources = {}

        # Test auto detect
        # files = glob.glob(f"{self.options['DIRECTORY']}/kpi_acc_computers*.csv")

        for k, ds in self.config.get("data_sources", {}).items():
            sources[k] = [src for src in self.options["--sources"] if ds in src]

        return sources

    def handle_exception(self, e: Exception, message: str = "") -> None:
        """
        Handle exception for the current class.

        Args:
            e (Exception): exception tu raise
            message (str): exception message
        """

        if self.options["--verbose"]:
            print(e)

        if message:
            ColorPrint.red(message)

    def import_kpi_sources(self, index: int = 0) -> Dict:
        """
        Import specified index of kpi sources.

        Args:
            index (int): index of sources
        """

        print(f"Importing {', '.join([s[0] for s in self.data_sources.values()])}...")

        current_data = {}
        self.source_index = index

        for k in self.data_sources.keys():
            current_data[k] = []

            if self.data_sources[k][index] is not None:
                current_data[k] = FileHandler.import_csv(
                    f"{self.options['DIRECTORY']}/{self.data_sources[k][index]}.csv", delimiter="|"
                )

        return current_data

    def build_source_environment(self, index: int = 0) -> None:
        """
        Import data sources and build scopes based on these sources.

        Args:
            index (int): index of source env
        """

        self.current_sources = self.import_kpi_sources(index)

        print("Building scopes...")
        config_scopes = self.config.get("scopes", {})
        current_scopes = {}

        for k, scope in config_scopes.items():
            s_perimeter = scope.get("perimeter")
            s_filters = [self.filters.get(f) for f in scope.get("filters", [])]
            current_scopes[k] = DataSet(
                name=scope.get("name"),
                perimeter=s_perimeter,
                scope=self.current_sources.get(s_perimeter),
                filters=s_filters,
            )

        self.scopes = current_scopes

    def kpi_process(self, kpi: Dict) -> Tuple[int, List[Dict]]:
        """
        Target process to deal with url data.

        Args:
            kpi (Dict): the kpi the process will be ran on
        """

        kpi_data = []

        kpi_controls = DataFilter.gen_from_dict(kpi.get("controls", []))
        # kpi_source = self.current_sources[kpi["perimeter"]]
        kpi_i = KPI(name=kpi["name"], perimeter=kpi["perimeter"], filters=kpi_controls)

        print(f"\n{kpi_i.get_name()}")

        for s in kpi["scopes"]:
            # Build the scope to pass to the kpi
            sd = DataSet.merge_sets(f"Build - {s['name']}", [self.scopes[b] for b in s["build"]])
            scope_i = DataSet(name=s["name"], perimeter=kpi_i.get_perimeter(), scope=sd)

            # Pass the scope to the kpi and get conformity data
            kpi_i.set_initial_scope(scope_i)
            kpi_data.append(kpi_i.to_dict())
            kpi_i.print_value(prefix=f"=> {scope_i.get_name()}: ")

        return (kpi_i, kpi_data)

    def kpi_thread_loop(self) -> None:
        """Run kpi thread loop."""

        print("Generating KPIs...")
        with Pool(processes=5) as pool:
            for kpi_res in pool.imap_unordered(self.kpi_process, self.kpi_list):
                self.results.extend(kpi_res[1])

    def run(self) -> None:
        """Run the command."""

        for i in range(self.iteration_count):
            self.build_source_environment(i)
            self.kpi_thread_loop()

        if self.options["--export-csv"] and len(self.results) > 0:
            append = True if self.options["--append"] else False
            FileHandler.export_csv(
                self.results, self.options["--export-csv"], delimiter="|", append=append
            )
