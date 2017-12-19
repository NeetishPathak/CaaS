from flask import Flask
from flask import jsonify
from flask import request
from ContainerManager import ContainerManager

APP = Flask(__name__)
CONT_MGR = ContainerManager()

MASTER_IP = "public IP"


@APP.route('/lb/status', methods=['GET'])
def status():
    '''
        Status check to tell if
        load-balancer container is responsive.
    '''
    response = jsonify({'message': 'Load-Balancer is responsive'})
    response.status_code = 200

    return response


@APP.route('/lb/createService', methods=['POST'])
def createService():
    '''
        Provision a service instance to the provided user.
        If the provision is successfully then the IP address and port to access that
        instance is provided.

        Status Codes:
            200 - Service has been created successfully (returns IP and port)
            400 - Data provided is invalid or insufficient
            401 - The user specified does not exist (unauthorized)
            404 - Service specified wasn't found.
            500 - General failure to store service information.
            501 - General failure to provision service.
    '''
    try:
        data = request.get_json(force=True)
        username = data['username']
        sessionID = data['sessionID']
        serviceID = data['serviceID']
    except Exception:
        response = jsonify({'error': "Failed to parse data. 'username', " + \
                                     "'sessionID', and 'serviceID' are required",
                            'data': str(request.data.decode('UTF-8'))})
        response.status_code = 400
        return response

    # Provision the service
    try:
        resp = CONT_MGR.createService(serviceID, username, sessionID)
    except Exception:
        response = jsonify({'error': "Failed to provision service"})
        response.status_code = 501
        return response

    # Return service info.
    if resp['status_code'] == 200:
        resp['data']['service_ip'] = MASTER_IP
    response = jsonify(resp['data'])
    response.status_code = resp['status_code']
    return response


@APP.route('/lb/removeService', methods=['DELETE'])
def removeService():
    '''
        Remove a specified service

        Status Codes:
            200 - Service has been removed successfully
            401 - The user specified does not exist
            404 - General failure to remove service.
            405 - General failure to update service information
    '''
    try:
        data = request.get_json(force=True)
        username = data['username']
        sessionID = data['sessionID']
        serviceID = data['serviceID']
    except Exception:
        response = jsonify({'error': "Failed to parse data. 'username', " + \
                                     "'sessionID', and 'serviceID' are required",
                            'data': str(request.data.decode('UTF-8'))})
        response.status_code = 400
        return response

    # Remove the service
    try:
        resp = CONT_MGR.removeService(serviceID, username, sessionID)
    except Exception as err:
        # response = jsonify({'error': 'Failed to remove service.'})
        response = jsonify({'error': str(err)})
        response.status_code = 404
        return response

    response = jsonify(resp['data'])
    response.status_code = resp['status_code']

    return response

if __name__ == '__main__':
    APP.run(debug=True,host='0.0.0.0', port=8081)
