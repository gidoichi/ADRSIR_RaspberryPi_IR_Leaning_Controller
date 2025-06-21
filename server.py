#!/usr/bin/env python3

import argparse
import importlib
import sys
from os import path
from typing import Dict, Optional

import flask
import flask_restx

filedir = path.dirname(path.abspath(__file__))

app = flask.Flask(__name__)
api = flask_restx.Api(app)

def cli():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--csvfile", help="CSV file path containing IR data")

    return parser.parse_args()

def run(command: str,
        manifacturer: Optional[str] = None,
        device: Optional[str] = None,
        function: Optional[str] = None,
        parameters: Dict[str, str] = {},
        csvfile: Optional[str] = None):
    argv_org: list[str] = sys.argv

    module: str = "Sample.I2C0x52-IR.IR-remocon10-csvbase"
    sys.path.append(filedir)
    sys.argv = [module]
    if csvfile is not None:
        sys.argv.extend(["--data", csvfile])
    sys.argv.append(command)
    if manifacturer is not None:
        sys.argv.extend(["--manifacturer", manifacturer])
    if device is not None:
        sys.argv.extend(["--device", device])
    if function is not None:
        sys.argv.extend(["--function", function])
    if len(parameters) > 0:
        params: str = ",".join([f"{k}={v}" for k, v in parameters.items()])
        sys.argv.extend(["--set", params])

    csvbase = getattr(importlib.import_module(module), "main")
    res = csvbase()

    sys.argv = argv_org

    return res

@api.route("/manifacturers")
class Manifacturers(flask_restx.Resource):
    def get(self):
        return run("list", csvfile=csvfile)["manifacturers"]

@api.route("/manifacturers/<manifacturer>/devices")
class Devices(flask_restx.Resource):
    def get(self, manifacturer: str):
        return run("list", manifacturer, csvfile=csvfile)["devices"]

@api.route("/manifacturers/<manifacturer>/devices/<device>/functions")
class Functions(flask_restx.Resource):
    def get(self, manifacturer: str, device: str):
        return run("list", manifacturer, device, csvfile=csvfile)["functions"]

@api.route("/manifacturers/<manifacturer>/devices/<device>/functions/<function>")
class Function(flask_restx.Resource):
    def post(self, manifacturer: str, device: str, function: str):
        parameters = flask.request.get_json()
        run("send", manifacturer, device, function, parameters=parameters, csvfile=csvfile)

csvfile: Optional[str] = None

if __name__ == "__main__":
    args = cli()
    csvfile = args.csvfile

    app.run(host="0.0.0.0")
