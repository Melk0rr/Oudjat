from enum import Enum

class LDAPSearchTypes(Enum):
  user = {
    "filter": "(&(objectClass=user)(!(objectClass=computer)))",
    "attributes": [
      "accountExpires",
      "cn",
      "description",
      "employeeID",
      "givenName",
      "lastLogon",
      "mail",
      "objectSid",
      "pwdLastSet",
      "sn",
      "sAMAccountName",
      "title",
      "userAccountControl",
      "whenChanged",
      "whenCreated"
    ]
  }

  person = {
    "filter": "(&(objectClass=person)(!(objectClass=computer)))",
    "attributes": [
      "accountExpires",
      "cn",
      "description",
      "employeeID",
      "givenName",
      "lastLogon",
      "mail",
      "objectSid",
      "pwdLastSet",
      "sn",
      "sAMAccountName",
      "title",
      "userAccountControl",
      "whenChanged",
      "whenCreated"
    ]
  }

  computer = {
    "filter": "(objectClass=computer)",
    "attributes": [
      "cn",
      "description",
      "lastLogon",
      "objectSid",
      "operatingSystem",
      "operatingSystemVersion",
      "pwdLastSet",
      "userAccountControl",
      "whenChanged",
      "whenCreated"
    ]
  }

  group = {
    "filter": "(objectClass=group)",
    "attributes": []
  }

  ou = {
    "filter": "(objectClass=organizationalUnit)",
    "attributes": []
  }