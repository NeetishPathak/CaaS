"""
 This is a standalone script to insert
 bulk entries in DB for testing purposes.
"""

import pdb
import random
import subprocess

from werkzeug.security import generate_password_hash
from config import db_file_name, COMPUTE_NODE_STATUS_DICT, DEFAULT_USERS_LIST
from config import DEFAULT_PASSWORD, COMPUTE_NODES, DEFAULT_IMAGES_LIST
from models import User, ComputeNode, Containers, Images


def insert_default_entries(db):
    # Create users

    for name, email in DEFAULT_USERS_LIST:
        hashed_password = generate_password_hash(DEFAULT_PASSWORD, method='sha256')
        u = User(username=name, email=email, password=hashed_password)
        db.session.add(u)

    for node in COMPUTE_NODES:
        default_status = COMPUTE_NODE_STATUS_DICT[0]
        c = ComputeNode(ip_addr=node[0], compute_node_status=default_status, compute_node_wt=node[1])
        db.session.add(c)

    # Create Images
    for i, (name, desc, wt) in enumerate(DEFAULT_IMAGES_LIST):
        im = Images(image_name=name, image_wt=wt, description=desc)
        db.session.add(im)

    db.session.commit()

def add_dummy_container_s(db):
    # DO NOT CALL THIS METHOD. Not in sync with current DB schema.
    users = User.query.all()
    nodes = ComputeNode.query.all()
    images = Images.query.all()
    container_lst = [["c1", "5432", "5432"],
                     ["c2", "5433", "5433"],
                     ["c3", "5434", "5434"],
                     ["c4", "5435", "5435"],
                     ["c5", "5436", "5436"],
                     ["c6", "5437", "5437"],
                     ["c7", "5438", "5438"],
                     ["c8", "5439", "5439"],
                     ["c9", "5440", "5440"],
                     ["c10", "5441", "5441"],
                     ["c11", "5442", "5442"],
                     ["c12", "5443", "5443"]]
    for i, (name, nat, doc) in enumerate(container_lst):
        x = random.choice(nodes)
        y = random.choice(users)
        z = random.choice(images)
        c = Containers(container_name=name, nat_port=nat, management_ip="192.168.0.100", docker_port=doc,
                       container_username="root", container_status="available", user=y, node=x, image=z)
        db.session.add(c)
    containers = Containers.query.all()
    for con in containers:
        print("{0}, by User: {1} on Node: {2}, of Image: {3}".format(con, con.user.username, con.node.ip_addr, con.image.image_name))


if __name__ == "__main__":
    from models import db as dba
    try:
        insert_default_entries(dba)
    except Exception as e:
        subprocess.call("rm -rf {0}".format(db_file_name), shell=True, stdout=subprocess.PIPE)
        raise e
