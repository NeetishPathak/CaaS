"""
MUST BE RUN AS ROOT.

This script shall run on the compute nodes and when
a get query is made it shall ping all the containers
currently running and return the status of ping.
"""
import pdb
import json
import subprocess as sp
from flask import Flask, request, abort, jsonify
DEFAULT_PORT = 65535

app = Flask(__name__)


@app.route('/checkhealth', methods=['POST'])
def get_container_health():
    if not request.json:
        abort(400)
    container_names = json.loads(request.data.decode('utf-8'))
    result = dict()
    for con in container_names:
        try:
            asd = sp.check_output("docker inspect {0}".format(con), shell=True, stderr=sp.STDOUT)
            asd = json.loads(asd.decode('utf-8'))[0]
            status = asd["State"]["Status"]
            result[con] = status
        except sp.CalledProcessError:
            result[con] = -99
    return jsonify(result), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=DEFAULT_PORT)
