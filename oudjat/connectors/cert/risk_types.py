from enum import Enum


class RiskType(Enum):
    """Enumeration describing possible risk values"""

    N_A = {"en": "Not specified", "fr": "Non spécifié"}
    EOP = {"en": "Elevation Of Privilege", "fr": "Élévation de privilèges"}
    RCE = {"en": "Remote Code Execution", "fr": "Exécution de code arbitraire à distance"}
    DOS = {"en": "Denial of Service", "fr": "Déni de service"}
    SFB = {"en": "Security Bypass", "fr": "Contournement de la politique de sécurité"}
    IDT = {"en": "Identity Theft", "fr": "Usurpation d'identité"}
    ID = {"en": "Information Disclosure", "fr": "Atteinte à la confidentialité des données"}
    TMP = {"en": "Integrity Violation", "fr": "Atteinte à l'intégrité des données"}
    XSS = {"en": "Code Injection", "fr": "Exécution de code arbitraire"}

    # TODO: Docstrings
    @property
    def en(self) -> str:
        return self._value_["en"]

    @property
    def fr(self) -> str:
        return self._value_["fr"]

    @staticmethod
    def risk_name(risk: "RiskType") -> str:
        """
        Returns the name of the given risk

        Args:
            risk (RiskType) : risk type to return the name of

        Returns:
            str : risk name
        """

        return risk.name
