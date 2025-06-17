#!/usr/bin/python3

import argparse
import csv
import fnmatch
import importlib
import logging
import os
import pathlib
import sys
from os import path

import jinja2

filedir = path.dirname(path.abspath(__file__))
os.chdir(filedir)

def cli():
    def parse_key_value_strings(s):
        result = {}
        for pair in s.split(","):
            if "=" not in pair:
                raise argparse.ArgumentTypeError(f"Invalid format: {pair}")
            key, value = pair.split("=", 1)
            result[key] = value
        return result

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--verbose", "-v", action="count", default=0)
    parser.add_argument("--data", default=pathlib.Path(path.join(filedir, "../IRCodeData/赤外線データ20171225.csv")).resolve(), help="CSV file path containing IR data")

    subpersers = parser.add_subparsers()
    subpersers.required = True

    parser_send = subpersers.add_parser("send")
    parser_send.add_argument("--manifacturer", required=True)
    parser_send.add_argument("--device", required=True)
    parser_send.add_argument("--function", required=True)
    parser_send.add_argument("--set", default={}, type=parse_key_value_strings, help="set values for template", metavar="key1=val1[,key2=value2...]")

    return parser.parse_args()

def run(data):
    argv_org = sys.argv

    module = "IR-remocon02-commandline"
    sys.argv = [module, "t", data]
    importlib.import_module(module)

    sys.argv = argv_org

args = cli()
verbosity: int = args.verbose
csvfile: str = args.data
manifacturer: str = args.manifacturer
device: str = args.device
function: str = args.function
values: str = args.set

loglevels: list[int] = [logging.WARNING, logging.INFO, logging.DEBUG]
logging.basicConfig(level=loglevels[min(verbosity, len(loglevels)-1)])
logger = logging.getLogger(__name__)

codes: list[str] = []
with open(path.join(csvfile), newline="") as csvdata:
    line: int = 0
    for row in csv.reader(csvdata):
        line += 1
        if len(row) < 3:
            logger.debug(f"skip line {line} from data file: the number of row is {len(row)} < 3")
            continue
        if not fnmatch.fnmatchcase(manifacturer, row[0]) or not fnmatch.fnmatchcase(device, row[1]) or not fnmatch.fnmatchcase(function, row[2]):
            continue
        logger.debug(f"line {line} matched: {row}")
        codes.append(row[3])
if len(codes) == 0:
    logger.error("invalid input: line unmatched")
    sys.exit(1)

code: str = "".join(codes)
logger.info(f"selected template: {code}")

template = jinja2.Template(code, undefined=jinja2.StrictUndefined)
raw = template.render(values)
logger.info(f"send data: {raw}")

run(data=raw.encode().decode("utf-8"))
