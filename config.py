import os
basedir = os.path.abspath(os.path.dirname(__file__))
db_file_name = os.path.join(basedir, 'database.db')

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + db_file_name
SECRET_KEY = "Thisissupposedtobesecret!"
SQLALCHEMY_TRACK_MODIFICATIONS = False

NAT_PORT_RANGE = (49152, 65534)
CLUSTER_SUBNET = "10.0.0.0/24"
MANAGEMENT_IP = "192.168.1.100"
MOCK_RUN = False
DEFAULT_RAM = 200
DEFAULT_CPU = 1
CONTAINER_NAME_LEN = 15
CON_SHARED_DIR = os.path.join("/", "root")  # This directory in the containers will be NFS mounted
SERVER_SHARED_DIR = os.path.join("/", "home", "shared")  # This directory is mounted on the servers
MASTER_SHARED_DIR = os.path.join("/", "home", "master", "shared")
DEFAULT_CONTAINER_USENAME = "root"
DEFAULT_CONTAINER_PASSWORD = "passwd123"
COMPUTE_NODE_STATUS_DICT = {0: "available", 1: "down", "default": "unknown"}
CONTAINER_STATUS_DICT = {0: "available", 1: "down"}
"""
COMPUTE_NODE_HEALTH_CHECK_INTERVAL = 200  # seconds
CONTAINER_HEALTH_CHECK_INTERVAL = 220  # seconds
GARBAGE_COLLECTOR_INTERVAL = 320
"""
HEALTH_CHECK_INTERVAL = 100
# If CONTAINER_HEALTH_QUERY_PORT & CONTAINER_HEALTH_QUERY_URI is
# changed here then these parameters MUST be changed in
# container_health_report.py on each compute node.
CONTAINER_HEALTH_QUERY_PORT = 65535
CONTAINER_HEALTH_QUERY_URI = "checkhealth"

# DB Entries.
COMPUTE_NODES = [["10.0.0.1", 4], ["10.0.0.2", 16], ["10.0.0.3", 64]]
DEFAULT_USERS_LIST = [["wade", "wade@ncsu.edu"],
                        ["prit", "prit@ncsu.edu"],
                        ["priya", "priya@ncsu.edu"],
                        ["priyal", "priyal@ncsu.edu"],
                        ["nikhil", "nikhil@ncsu.edu"],
                        ["neetish", "neetish@ncsu.edu"],
                        ["admin", "admin@ncsu.edu"]]
DEFAULT_PASSWORD = "admin@123"
DEFAULT_IMAGES_LIST = [["ansible", "ansible", 1],
                       ["ruby", "ruby on ubuntu", 2],
                       ["ubuntu_ssh", "ubuntu 14.04", 3],
                       ["flask", "flask on ubuntu", 4],
                       ["ansible1", "ansible1", 5]]

DOCKER_REGISTRY_URI = "10.0.0.1:5000"
