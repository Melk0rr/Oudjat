"""
A SOC toolbox and maybe more if I have the time.

Usage:
    oudjat cert (-t TARGET | -f FILE) [options]   [--feed] [--filter=FILTER]
                                                  [--keywords=KEYWORDS | --keywordfile=FILE]
    oudjat vuln (-t TARGET | -f FILE) [options]
    oudjat kpi (-d DIRECTORY) (-s SOURCES) [options] [--config=CONFIG] [--history=HIST] [--history-gap=GAP]
    oudjat sc (-t TARGET | -f FILE) (--sc-url=SC_URL) [--sc-mode=SC_MODE]
    oudjat -h | --help
    oudjat -V | --version

Commands
    cert                            parse data from cert page
    kpi                             generates kpi
    vuln                            parse CVE data from Nist page

Options:
    -a --append                     append to the output file
    -c --config=CONFIG              specify config file
    -d --directory                  set target (reads from file, one domain per line)
    -f --file                       set target (reads from file, one domain per line)
    -h --help                       show this help message and exit
    -H --history=HIST               check kpis for last n element
    -l --cve-list=CVE_LIST          provide a list of cve to be used as a database and reduce the amount of requests
    -o --output=FILENAME            save to filename
    -s --sources=SOURCES            kpi source files
    -S --silent                     simple output, one per line
    -t --target                     set target (comma separated, no spaces, if multiple)
    -v --verbose                    print debug info and full request output
    -V --version                    show version and exit
    -x --export-csv=CSV             save results as csv
    --history-dates=DATES           gap between elements

Cert-options:
    --feed                          run cert mode from a feed
    --filter=FILTER                 date filter to apply with feed option (e.g. 2023-03-10)
    --keywords=KEYWORDS             set keywords to track (comma separated, no spaces, if multiple)
    --keywordfile=KEYWORDFILE       set keywords to track (file, one keyword per line)

Exemples:
    oudjat cert -t https://cert.ssi.gouv.fr/alerte/feed/ --feed --filter "2023-03-13"
    oudjat cert -f ./tests/certfr.txt --export-csv ./tests/certfr_20230315.csv --keywordfile ./tests/keywords.txt
    oudjat vuln -f ./tests/cve.txt --export-csv ./tests/cve_20230313.csv

Help:
    For help using this tool, please open an issue on the Github repository:
    https://github.com/Melk0rr/Oudjat
"""

import sys
import time
from typing import Any

from docopt import docopt

import oudjat.commands
from oudjat.banner import banner
from oudjat.utils import ColorPrint, StdOutHook, TimeConverter

from . import __version__ as VERSION

COMMAND_OPTIONS = {
    "vuln": oudjat.commands.vuln.Vuln,
    "cert": oudjat.commands.cert.Cert,
    "kpi": oudjat.commands.kpi_factory.KPIFactory,
    # "sc"  : oudjat.commands.SC,
}


def command_switch(options: dict[str, str]) -> Any:
    """
    Script command switch case.
    """

    command_name = next(command for command in COMMAND_OPTIONS.keys() if options[command])
    return COMMAND_OPTIONS[command_name](options)


def main() -> None:
    """
    Program entry point that runs each time the 'oudjat' command line is executed.
    """

    try:
        if sys.version_info < (3, 0):
            sys.stdout.write("Sorry, requires Python 3.x\n")
            sys.exit(1)

        start_time = time.time()
        options = docopt(__doc__, version=VERSION)

        original_stdout = sys.stdout

        if options["--output"] or options["--silent"]:
            sys.stdout = StdOutHook(options["FILENAME"], options["--silent"], options["--output"])

        if not options["--target"] and not options["--file"] and not options["--directory"]:
            ColorPrint.red("Target required! Use -h to see usage. Either -f or -t")
            return

        if options["--target"] and options["--file"]:
            ColorPrint.red("Please only supply one target method - either -f or -t.")
            return


        ColorPrint.blue(banner)

        command = command_switch(options)
        command.run()

        print(
            f"\nWatchers infos search took {
                TimeConverter.seconds_to_str(time.time() - start_time)
            }s"
        )

        sys.stdout = original_stdout

    except KeyboardInterrupt:
        print("\nQuitting...")
        sys.exit(0)
