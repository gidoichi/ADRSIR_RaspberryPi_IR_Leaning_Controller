#!/usr/bin/env python3

import argparse
import importlib
import sys
from typing import Dict, Optional

import flask
import flask_restx

app = flask.Flask(__name__)
api = flask_restx.Api(app)

def cli():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--csvfile", help="CSV file path containing IR data")

    return parser.parse_args()

def run(manifacturer: str, device: str, function: str, parameters: Dict[str, str] = {}, csvfile: Optional[str] = None):
    argv_org: list[str] = sys.argv

    module: str = "Sample.I2C0x52-IR.IR-remocon10-csvbase"
    sys.argv = [
        module,
        "--manifacturer", manifacturer,
        "--device", device,
        "--function", function,
    ]
    if len(parameters) > 0:
        params: str = ",".join([f"{k}={v}" for k, v in parameters])
        sys.argv.extend(["--set", params])
    if csvfile is not None:
        sys.argv.extend(["--data", csvfile])

    importlib.import_module(module)

    sys.argv = argv_org

@api.route("/manifacturers/<manifacturer>/devices/<device>/functions/<function>")
class Manifacturer(flask_restx.Resource):
    # TODO: remove
    def get(self, manifacturer, device, function):
        return {
            "Hello": "World"
        }

    def post(self, manifacturer: str, device: str, function: str):
        parameters = flask.request.get_json()
        run(manifacturer=manifacturer, device=device, function=function, parameters=parameters, csvfile=csvfile)
        # controller.Run(manifacturer=manifacturer, device=device, function=function, parameters={"templerature": 16, "power", "medium"})

csvfile: Optional[str] = None

if __name__ == "__main__":
    args = cli()
    csvfile = args.csvfile

    app.run(host="0.0.0.0")
