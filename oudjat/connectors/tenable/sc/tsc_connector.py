import re
from typing import Dict, List, Tuple
from urllib.parse import urlparse

from tenable.sc import TenableSC

from oudjat.connectors.connector import Connector
from oudjat.utils import ColorPrint

from .tsc_asset_list_types import TSCAssetListType
from .tsc_severities import TenableSCSeverity


class TenableSCConnector(Connector):
    # ****************************************************************
    # Attributes & Constructors

    BUILTIN_FILTERS = {"exploitable": ("exploitAvailable", "=", "true")}

    def __init__(
        self, target: str, service_name: str = "OudjatTenableSCAPI", port: int = 443
    ) -> None:
        """Constructor"""

        scheme = "http"
        if port == 443:
            scheme += "s"

        if not re.match(r"http(s?):", target):
            target = f"{scheme}://{target}"

        super().__init__(target=urlparse(target), service_name=service_name, use_credentials=True)
        self.target = urlparse(f"{self.target.scheme}://{self.target.netloc}")
        self.connection: TenableSC = None
        self.repos = None

    # ****************************************************************
    # Methods

    # INFO: Getters
    def get_repos(self) -> List:
        """Returns repositories list"""
        return self.repos

    # INFO: Base connector methods
    def connect(self) -> None:
        """Connects to API using connector parameters"""
        connection = None
        try:
            connection = TenableSC(
                host=self.target.netloc,
                access_key=self.credentials.username,
                secret_key=self.credentials.password,
            )

            ColorPrint.green(f"Connected to {self.target.netloc}")
            self.connection = connection
            self.repos = self.connection.repositories.list()

        except Exception as e:
            raise e

    def check_connection(self) -> None:
        """Checks if the connection is initialized"""
        if self.connection is None:
            raise ConnectionError("Connection not initialized")

    def disconnect(self) -> None:
        """Disconnect from API"""
        del self.connection
        self.connection = None
        self.repos = None

    def search(self, search_type: str, *args, **kwargs) -> List:
        """Searches the API for elements"""
        self.check_connection()

        search_type = search_type.upper()
        search_options = {"VULNS": self.search_vulns}

        if search_type not in search_options.keys():
            raise ValueError(f"Invalid search type {search_type}")

        search = None
        try:
            search = search_options[search_type](*args, **kwargs)

        except Exception as e:
            raise e

        return list(search)

    # INFO: Vulns
    def search_vulns(
        self, *severities: List[str], key_exclude: List[str] = None, tool: str = "vulndetails"
    ) -> Dict:
        """Retreive the current vulnerabilities"""

        filters = [self.BUILTIN_FILTERS["exploitable"]]
        if severities is not None:
            filters.append(self.build_severity_filter(severities))

        search = self.connection.analysis.vulns(*filters, tool=tool)
        return list(search)

    def build_severity_filter(self, *severities: List[str]) -> Tuple:
        """Returns a severity filter based on the provided severities"""
        sev_scores = ",".join([f"{TenableSCSeverity[sev].value}" for sev in list(*severities)])
        return "severity", "=", sev_scores

    # INFO: Asset lists
    def create_asset_list(
        self,
        name: str,
        list_type: TSCAssetListType = TSCAssetListType.COMBINATION,
        description: str = None,
        ips: List[str] = None,
        dns_names: List[str] = None,
    ) -> None:
        """Creates a new asset list"""

        if self.connection is None:
            raise ConnectionError(
                "TenableSCConnector.create_asset_list::Can't create asset list if connection is not initialized"
            )

        try:
            self.connection.asset_lists.create(
                name=name,
                description=description,
                list_type=list_type.value,
                ips=ips,
                dns_names=dns_names,
            )

        except Exception as e:
            raise e

    def delete_asset_list(self, id=int) -> None:
        """Deletes an asset list based on given id"""

        # TODO: Ability to delete multiple asset lists
        if self.connection is None:
            raise ConnectionError(
                "TenableSCConnector.delete_asset_list::Can't delete asset list if connection is not initialized"
            )

        try:
            self.connection.asset_lists.delete(id=id)

        except Exception as e:
            raise e

    # TODO: Edit asset list
