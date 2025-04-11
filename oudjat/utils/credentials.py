# INFO: Helper functions to handle credentials

import getpass

import keyring


def save_credentials(service: str, username: str, password: str) -> None:
    """
    This function uses the `keyring` library to securely store the provided credentials (username and password) for a specified service in an encrypted
    vault. If the operation is successful, no value is returned. Otherwise, it will raise a `keyring.errors.PasswordSetError` if there's an issue setting the password.

    Args:
        service (str) : The identifier for the service or application where the credentials are being stored.
        username (str): The username to be associated with these credentials.
        password (str): The password that corresponds to the given username.

    Raises:
        keyring.errors.PasswordSetError: If there is an error while attempting to save the password.
    """

    try:
        keyring.set_password(service, username, password)

    except keyring.errors.PasswordSetError as e:
        raise (f"Error while saving credentials for {service}:{username}\n{e}")


def get_credentials(service: str) -> keyring.credentials.SimpleCredential:
    """
    This function attempts to retrieve stored credentials from the `keyring` using the provided service name. If no credentials are found, it prompts the
    user to enter their username and password manually, which are then saved in the keyring before being returned. It also handles errors that may occur during
    retrieval or if there's an issue with the keyring itself by raising a `keyring.errors.KeyringError`.

    Args:
        service (str): The identifier for the service from which to retrieve credentials.

    Returns:
        keyring.credentials.SimpleCredential: An object containing the retrieved username and password.

    Raises:
        keyring.errors.KeyringError: If there is an error while retrieving the credentials or if the keyring operation fails.
    """

    try:
        cred = keyring.get_credential(service, "")

        if cred is None:
            print(f"\nNo stored credentials for {service}. Please enter your credentials:")

            # Ask user's credentials
            username = input("Username: ")
            password = getpass.getpass("Password: ")

            # Saving credentials
            save_credentials(service, username, password)
            cred = keyring.credentials.SimpleCredential(username, password)

    except keyring.errors.KeyringError as e:
        raise (f"\nAn error occured while retreiving user's credentials for {service}\n{e}")

    return cred


def del_credentials(service: str, username: str) -> None:
    """
    This function removes stored credentials from the `keyring` using both the service identifier and the specified username. If the operation is successful,
    no value is returned. Otherwise, it will raise a `keyring.errors.PasswordDeleteError` if there's an issue deleting the password.

    Args:
        service (str) : The identifier for the service from which to delete credentials.
        username (str): The username whose associated credentials are to be deleted.

    Raises:
        keyring.errors.PasswordDeleteError: If there is an error while attempting to delete the password.
    """

    try:
        keyring.delete_password(service, username)

    except keyring.errors.PasswordDeleteError as e:
        raise (f"Error while deleting password for {service}:{username}\n{e}")
