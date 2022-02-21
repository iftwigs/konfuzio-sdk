"""Command Line interface to the konfuzio_sdk package."""

import logging
import sys
from getpass import getpass

from konfuzio_sdk import KONFUZIO_HOST
from konfuzio_sdk.api import create_new_project
from konfuzio_sdk.data import download_training_and_test_data
from konfuzio_sdk.api import init_env

sys.tracebacklimit = 0

logger = logging.getLogger(__name__)

CLI_ERROR = """
Please enter a valid command line option.
----------------------------------------

konfuzio_sdk init
    add the API Token as .env file to connect to the Konfuzio Server, i.e. Host
konfuzio_sdk create_project >NAME<
    Create a new project on the Konfuzio Server. Returns the ID of the new project.
konfuzio_sdk export_project >ID<
    Download the data from a project by ID to migrate it to another Host.

These commands should be run inside of your working directory.

A bug report can be filed at https://github.com/konfuzio-ai/document-ai-python-sdk/issues. Thanks!
"""


def main():
    """CLI of Konfuzio SDK."""
    _cli_file_path = sys.argv.pop(0)  # NOQA
    if sys.argv and sys.argv[0] == 'init':
        user = input("Username you use to login to Konfuzio Server: ")
        password = getpass("Password you use to login to Konfuzio Server: ")
        host = str(input("Server Host URL (press [ENTER] for https://app.konfuzio.com): ") or KONFUZIO_HOST)
        init_env(user=user, password=password, host=host)
    elif sys.argv and sys.argv[0] == 'export_project' and sys.argv[1].isdigit():
        download_training_and_test_data(id_=int(sys.argv[1]))
    elif sys.argv and sys.argv[0] == 'create_project' and sys.argv[1]:
        create_new_project(sys.argv[1])
    else:
        print(CLI_ERROR)
        return -1
    return 0


if __name__ == "__main__":
    main()
