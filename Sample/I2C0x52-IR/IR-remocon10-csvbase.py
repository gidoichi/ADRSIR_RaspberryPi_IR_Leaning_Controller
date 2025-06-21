#!/usr/bin/python3

import argparse
import csv
import fnmatch
import importlib
import json
import logging
import pathlib
import sys
from enum import StrEnum
from os import path
from typing import Dict, Optional

import jinja2

filedir = path.dirname(path.abspath(__file__))

class Row:
    def __init__(self, manifacture: str, device: str, function: str, code: str):
        self.manifacture = manifacture
        self.device = device
        self.function = function
        self.code = code

class CliSubcommand(StrEnum):
    LIST = "list"
    SEND = "send"

def cli():
    def parse_key_value_strings(s: str):
        result: Dict[str, str] = {}
        for pair in s.split(","):
            if "=" not in pair:
                raise argparse.ArgumentTypeError(f"Invalid format: {pair}")
            key, value = pair.split("=", 1)
            result[key] = value
        return result

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--verbose", "-v", action="count", default=0)
    parser.add_argument("--data", default=pathlib.Path(path.join(filedir, "../IRCodeData/赤外線データ20171225.csv")).resolve(), help="CSV file path containing IR data")

    subpersers = parser.add_subparsers(dest="subcommand")
    subpersers.required = True

    parser_list = subpersers.add_parser(CliSubcommand.LIST)
    parser_list.add_argument("--manifacturer")
    parser_list.add_argument("--device")
    parser_list.add_argument("--function")

    parser_send = subpersers.add_parser(CliSubcommand.SEND)
    parser_send.add_argument("--manifacturer", required=True)
    parser_send.add_argument("--device", required=True)
    parser_send.add_argument("--function", required=True)
    parser_send.add_argument("--set", default={}, type=parse_key_value_strings, help="set values for template", metavar="key1=val1[,key2=value2...]")

    return parser.parse_args()

def search(manifacturer: Optional[str], device: Optional[str], function: Optional[str]) -> list[Row]:
    matched: list[Row] = []

    with open(path.join(csvfile), newline="") as csvdata:
        line: int = 0
        for row in csv.reader(csvdata):
            line += 1
            if len(row) < 3:
                logger.debug(f"skip line {line} from data file: the number of row is {len(row)} < 3")
                continue

            if manifacturer is None:
                pass
            elif device is None:
                if not fnmatch.fnmatchcase(row[0], manifacturer):
                    continue
            elif function is None:
                if not fnmatch.fnmatchcase(row[0], manifacturer) or not fnmatch.fnmatchcase(row[1], device):
                    continue
            else:
                if not fnmatch.fnmatchcase(row[0], manifacturer) or not fnmatch.fnmatchcase(row[1], device) or not fnmatch.fnmatchcase(row[2], function):
                    continue

            matched.append(Row(row[0], row[1], row[2], row[3]))

    return matched

def listKeys(manifacturer: Optional[str], device: Optional[str], function: Optional[str]) -> Dict[str, list[str]]:
    searched = search(manifacturer=manifacturer, device=device, function=function)

    if manifacturer is None:
        listed = {row.manifacture for row in searched}
        return {"manifacturers": [key for key in listed]}
    elif device is None:
        listed = {row.device for row in searched}
        return {"devices": [key for key in listed]}
    elif function is None:
        listed = {row.function for row in searched}
        return {"functions": [key for key in listed]}
    else:
        raise Exception("search parameters: at least one parameter must be None")

def send(data) -> None:
    argv_org = sys.argv

    module: str = "IR-remocon02-commandline"
    sys.path.append(filedir)
    sys.argv = [module, "t", data]
    importlib.import_module(module)

    sys.argv = argv_org

def main():
    loglevels: list[int] = [logging.WARNING, logging.INFO, logging.DEBUG]
    logging.basicConfig(level=loglevels[min(verbosity, len(loglevels)-1)])
    logger = logging.getLogger(__name__)

    match args.subcommand:
        case CliSubcommand.LIST:
            manifacturer: Optional[str] = args.manifacturer
            device: Optional[str] = args.device
            function: Optional[str] = args.function

            if manifacturer is None and device is not None:
                raise argparse.ArgumentTypeError("Invalid combination of parameters: 'manifacturer' must be specified if 'device' is specified")
            if device is None and function is not None:
                raise argparse.ArgumentTypeError("Invalid combination of parameters: 'device' must be specified if 'function' is specified")

            obj = listKeys(manifacturer, device, function)
            if __name__ == "__main__":
                print(json.dumps(obj))
            else:
                return obj

        case CliSubcommand.SEND:
            values: str = args.set

            searched = search(args.manifacturer, args.device, args.function)

            codes: list[str] = [row.code for row in searched]
            code: str = "".join(codes)
            logger.info(f"selected template: {code}")

            template = jinja2.Template(code, undefined=jinja2.StrictUndefined)
            raw = template.render(values)
            logger.info(f"send data: {raw}")

            send(data=raw.encode().decode("utf-8"))

args = cli()
verbosity: int = args.verbose
csvfile: str = args.data

if __name__ == "__main__":
    main()
