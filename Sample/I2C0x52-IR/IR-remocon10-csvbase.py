#!/usr/bin/python3

import argparse
import csv
import fnmatch
import json
import logging
import os.path
import pathlib
import subprocess
from enum import StrEnum
from typing import Dict, Optional

import jinja2

filedir = os.path.dirname(os.path.abspath(__file__))

class Row:
    def __init__(self, manifacture: str, device: str, function: str, code: str):
        self.manifacture = manifacture
        self.device = device
        self.function = function
        self.code = code

class CliSubcommand(StrEnum):
    GET = "get"
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
    parser.add_argument("--data", default=pathlib.Path(os.path.join(filedir, "../IRCodeData/赤外線データ20171225.csv")).resolve(), help="CSV file path containing IR data")

    subpersers = parser.add_subparsers(dest="subcommand")
    subpersers.required = True

    parser_get = subpersers.add_parser(CliSubcommand.GET)
    parser_get.add_argument("--manifacturer", required=True)
    parser_get.add_argument("--device", required=True)
    parser_get.add_argument("--function", required=True)

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

def search(csvfile: str, logger, manifacturer: Optional[str], device: Optional[str], function: Optional[str]) -> list[Row]:
    matched: list[Row] = []

    with open(os.path.join(csvfile), newline="") as csvdata:
        line: int = 0
        for row in csv.reader(csvdata):
            line += 1
            if len(row) < 3:
                logger.debug(f"skip line {line} from data file: the number of row is {len(row)} < 3")
                continue

            if manifacturer is None:
                pass
            elif device is None:
                if not fnmatch.fnmatchcase(manifacturer, row[0]):
                    continue
            elif function is None:
                if not fnmatch.fnmatchcase(manifacturer, row[0]) or not fnmatch.fnmatchcase(device, row[1]):
                    continue
            else:
                if not fnmatch.fnmatchcase(manifacturer, row[0]) or not fnmatch.fnmatchcase(device, row[1]) or not fnmatch.fnmatchcase(function, row[2]):
                    continue

            matched.append(Row(row[0], row[1], row[2], row[3]))

    return matched

def listKeys(csvfile, logger, manifacturer: Optional[str], device: Optional[str], function: Optional[str]) -> Dict[str, list[str]]:
    searched = search(csvfile, logger, manifacturer=manifacturer, device=device, function=function)

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
    process = subprocess.run(["./IR-remocon02-commandline.py", "t", data], capture_output=True, cwd=os.path.dirname(os.path.abspath(__file__)))
    if process.returncode != 0:
        raise Exception(f"Failed to send data: {process.stderr.decode()}")

parsed_args = cli()
verbosity: int = parsed_args.verbose
csvfile: str = parsed_args.data

loglevels: list[int] = [logging.WARNING, logging.INFO, logging.DEBUG]
logging.basicConfig(level=loglevels[min(verbosity, len(loglevels)-1)])
logger = logging.getLogger(os.path.basename(__file__))

match parsed_args.subcommand:
    case CliSubcommand.GET:
        searched = search(csvfile, logger, parsed_args.manifacturer, parsed_args.device, parsed_args.function)
        if len(searched) == 0:
            raise Exception("No matching data found in the CSV file")

        codes: list[str] = [row.code for row in searched]
        code: str = "".join(codes)
        print(code)

    case CliSubcommand.LIST:
        manifacturer: Optional[str] = parsed_args.manifacturer
        device: Optional[str] = parsed_args.device
        function: Optional[str] = parsed_args.function

        if manifacturer is None and device is not None:
            raise argparse.ArgumentTypeError("Invalid combination of parameters: 'manifacturer' must be specified if 'device' is specified")
        if device is None and function is not None:
            raise argparse.ArgumentTypeError("Invalid combination of parameters: 'device' must be specified if 'function' is specified")

        obj = listKeys(csvfile, logger, manifacturer, device, function)
        print(json.dumps(obj))

    case CliSubcommand.SEND:
        values: str = parsed_args.set

        searched = search(csvfile, logger, parsed_args.manifacturer, parsed_args.device, parsed_args.function)
        if len(searched) == 0:
            raise Exception("No matching data found in the CSV file")

        codes: list[str] = [row.code for row in searched]
        code: str = "".join(codes)
        logger.info(f"selected template: {code}")

        template = jinja2.Template(code, undefined=jinja2.StrictUndefined)
        raw = template.render(values)
        logger.info(f"send data: {raw}")

        send(data=raw.encode().decode("utf-8"))
