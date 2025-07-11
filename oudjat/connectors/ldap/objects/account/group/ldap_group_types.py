"""A simple module to define LDAP group types as a bit flag."""

from oudjat.utils.bit_flag import BitFlag


class LDAPGroupType(BitFlag):
    """LDAP group type values."""

    GLOBAL_DISTRIB = 2
    DOMAIN_DISTRIB = 4
    UNIVERSAL_DISTRIB = 8
    GLOBAL_SECURITY = -2147483646
    DOMAIN_SECURITY = -2147483644
    UNIVERSAL_SECURITY = -2147483640

