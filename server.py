#!/usr/bin/env python3

import argparse
import json
import logging
import os.path
import subprocess
from typing import Any, Dict, Optional

import flask
import waitress
from flask import Flask
from flask_restx import Api, Resource

filedir = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
api = Api(app)

def cli():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--csvfile", help="CSV file path containing IR data")
    parser.add_argument("--verbose", "-v", action="count", default=0)

    return parser.parse_args()

def run(subcommand: str,
        manifacturer: Optional[str] = None,
        device: Optional[str] = None,
        function: Optional[str] = None,
        parameters: Dict[str, str] = {},
        csvfile: Optional[str] = None) -> bytes:

    command: list[str] = ["./Sample/I2C0x52-IR/IR-remocon10-csvbase.py"]
    if csvfile is not None:
        command.extend(["--data", csvfile])
    command.append(subcommand)
    if manifacturer is not None:
        command.extend(["--manifacturer", manifacturer])
    if device is not None:
        command.extend(["--device", device])
    if function is not None:
        command.extend(["--function", function])
    if len(parameters) > 0:
        params: str = ",".join([f"{k}={v}" for k, v in parameters.items()])
        command.extend(["--set", params])

    app.logger.debug(f"Running command: {' '.join(command)}")
    process = subprocess.run(command, capture_output=True, cwd=os.path.dirname(os.path.abspath(__file__)))
    if process.returncode != 0:
        raise Exception(f"command failed with return code {process.returncode}: {process.stderr.decode()}")

    return process.stdout

@api.route("/manifacturers")
class Manifacturers(Resource):
    def get(self):
        result: bytes = b""
        try:
            result = run("list", csvfile=csvfile)
        except Exception as e:
            flask.abort(500, f"error: {str(e)}")

        lst = {}
        try:
            lst = json.loads(result)
        except json.JSONDecodeError:
            flask.abort(500, f"error: failed to decode JSON response: {result.decode()}")

        if type(lst) is not dict or "manifacturers" not in lst:
            flask.abort(500, f"error: 'manifacturers' not found in response: {lst}")
        return lst["manifacturers"]

@api.route("/manifacturers/<manifacturer>/devices")
class Devices(Resource):
    def get(self, manifacturer: str):
        result: bytes = b""
        try:
            result = run("list", manifacturer, csvfile=csvfile)
        except Exception as e:
            flask.abort(500, f"error: {str(e)}")

        lst = {}
        try:
            lst = json.loads(result)
        except json.JSONDecodeError:
            flask.abort(500, f"error: failed to decode JSON response: {result.decode()}")

        if type(lst) is not dict or "devices" not in lst:
            return flask.abort(500, f"Internal server error: 'devices' not found in response: {lst}")
        return lst["devices"]

@api.route("/manifacturers/<manifacturer>/devices/<device>/functions")
class Functions(Resource):
    def get(self, manifacturer: str, device: str):
        result: bytes = b""
        try:
            result = run("list", manifacturer, device, csvfile=csvfile)
        except Exception as e:
            flask.abort(500, f"error: {str(e)}")

        lst = {}
        try:
            lst = json.loads(result)
        except json.JSONDecodeError:
            flask.abort(500, f"error: failed to decode JSON response: {result.decode()}")

        if type(lst) is not dict or "functions" not in lst:
            return flask.abort(500, f"Internal server error: 'functions' not found in response: {lst}")
        return lst["functions"]

@api.route("/manifacturers/<manifacturer>/devices/<device>/functions/<function>")
class Function(Resource):
    def post(self, manifacturer: str, device: str, function: str):
        parameters = flask.request.get_json()
        try:
            run("send", manifacturer, device, function, parameters=parameters, csvfile=csvfile)
        except Exception as e:
            return flask.abort(500, f"error: {str(e)}")

        return {"status": "success", "message": "Command sent successfully"}, 200

args = cli()
csvfile: Optional[str] = args.csvfile
verbosity: int = args.verbose

loglevels: list[int] = [logging.WARNING, logging.INFO, logging.DEBUG]
loglevel: int = loglevels[min(verbosity, len(loglevels)-1)]
app.logger.setLevel(loglevel)
logging.getLogger('waitress').setLevel(loglevel)

waitress.serve(app)
