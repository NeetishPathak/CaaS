import pdb
import random
import string
import warnings
import subprocess as sp

import sqlite3
from flask_login.utils import login_user
from sqlalchemy.dialects.oracle.zxjdbc import SQLException
from werkzeug.security import generate_password_hash, check_password_hash

from models import User, Images, Containers, ComputeNode, logger, DelContainers
from config import CLUSTER_SUBNET, MANAGEMENT_IP, NAT_PORT_RANGE, MOCK_RUN, CONTAINER_NAME_LEN, COMPUTE_NODE_STATUS_DICT


def db_not_found_error(db):
    raise Exception("Database connection db={0} is Invalid.".format(db))


class DatabaseManager(object):
    """ A class which will interact the system database.
    """
    def __init__(self, db):
        """ Initialize database connection """
        self.db = db
        iptable_rule = "iptables -{0} FORWARD -m state -d {1} --state NEW,RELATED,ESTABLISHED -j ACCEPT"
        delete_cmd = iptable_rule.format("D", CLUSTER_SUBNET)
        try:
            sp.call(delete_cmd, shell=True)
        except Exception as e:
            logger.info("Iptable rule didn't exist")
        add_cmd = iptable_rule.format("I", CLUSTER_SUBNET)
        out = sp.call(add_cmd, shell=True)
        if out == 0:
            logger.info("Success added IP Table rule {0}".format(add_cmd))
        else:
            logger.error("Failure in adding IP table rule {0}".format(add_cmd))
            raise Exception("Failed to add IP table rule")

    @staticmethod
    def execute_bash_command(command):
        if MOCK_RUN:
            logger(command)
        else:
            output = sp.call(command, shell=True, stderr=sp.STDOUT)
            logger.debug(output)

    def add_user(self, name, email, password):
        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(username=name, email=email, password=hashed_password)
        self.db.session.add(new_user)
        self.db.session.commit()
        return True

    @staticmethod
    def get_all_users():
        return User.query.all()

    @staticmethod
    def get_user(id):
        return User.query.get(int(id))

    @staticmethod
    def get_user_by_name(username):
        return User.query.filter_by(username=username).first()

    @staticmethod
    def get_all_images():
        return Images.query.all()

    @staticmethod
    def get_image(image_id):
        return Images.query.get(int(image_id))

    @staticmethod
    def get_image_by_name(image_name):
        return Images.query.filter_by(image_name=image_name).first()

    @staticmethod
    def get_all_containers():
        return Containers.query.all()

    @staticmethod
    def get_all_computenodes():
        return ComputeNode.query.all()

    @staticmethod
    def get_all_computeodes_with_load():
        my_list = []
        nodes = ComputeNode.query.all()
        for node in nodes:
            ld = sum([con.image.image_wt for con in node.container])
            my_list.append([node, ld])
        return my_list

    @staticmethod
    def get_alive_computenodes():
        return ComputeNode.query.filter_by(compute_node_status=COMPUTE_NODE_STATUS_DICT[0])

    def set_computenode_status(self, node, res):
        node.compute_node_status = COMPUTE_NODE_STATUS_DICT[res]
        logger.info("Health Check: Server: {0} : {1}".format(
            node.ip_addr, COMPUTE_NODE_STATUS_DICT[res]))
        self.db.session.commit()

    @staticmethod
    def authenticate(username, password, remember_me):
        """ Authenticate a user
            Return True if successful, false otherwise
        """
        user = User.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember=remember_me)
                return True
        return False

    @staticmethod
    def get_user_reservations(user):
        return user.container

    @staticmethod
    def get_floating_ip_address():
        # TODO: return the IP address on which the client should send SSH request
        return MANAGEMENT_IP

    @staticmethod
    def get_available_nat_port():
        # get all used ports
        used_active_ports = set([con.nat_port for con in DatabaseManager.get_all_containers()])
        used_del_ports = set([con.nat_port for con in DatabaseManager.get_all_deleted_containers()])
        used_ports = used_active_ports.union(used_del_ports)
        for nat_port in range(*NAT_PORT_RANGE):
            if nat_port not in used_ports:
                return nat_port

    @staticmethod
    def add_ssh_port_forward_rule(compute_node_ip, docker_port, nat_port=None):
        """
        Installs IP table rules on management node.
        :param self:
        :param compute_node_ip:
        :param docker_port:
        :return:
        sample iptable rule:
        iptables -t nat -I PREROUTING -p tcp -d 152.7.99.163 --dport 34567 -j DNAT --to-destination 192.168.122.138:22
        iptables -I FORWARD -m state -d 192.168.122.0/24 --state NEW,RELATED,ESTABLISHED -j ACCEPT
        """
        iptable_str = "iptables -t nat -I PREROUTING -p tcp -d {0} --dport {1} -j DNAT --to-destination {2}:{3}"
        dest_ip = DatabaseManager.get_floating_ip_address()
        nat_port = nat_port if nat_port else DatabaseManager.get_available_nat_port()
        iptable_str = iptable_str.format(dest_ip, nat_port, compute_node_ip, docker_port)

        DatabaseManager.execute_bash_command(iptable_str )
        return nat_port, dest_ip

    @staticmethod
    def delete_ssh_port_forward_rule(con):
        stt = "iptables -t nat -D PREROUTING -p tcp -d {0} --dport {1} -j DNAT --to-destination {2}:{3}"
        dest_ip = con.management_ip
        nat_port = con.nat_port
        compute_node_ip = con.node.ip_addr
        docker_port = con.docker_port
        stt = stt.format(dest_ip, nat_port, compute_node_ip, docker_port)
        DatabaseManager.execute_bash_command(stt)
        return True

    def update_container(self, container_info):
        """Store the service information in the database.
            Return True if successful, false otherwise
        """
        return True

    def add_container(self, container_id, container_name, nat_port, management_ip,
            docker_port, ram, cpu, username, password,
            node, image, user):
        #pdb.set_trace()
        new_container = Containers(container_id=container_id, container_name=container_name, nat_port=nat_port,
                                   management_ip=management_ip, docker_port=docker_port,
                                   ram=ram, cpu=cpu, container_username=username,
                                   container_passwd=password, node=node, image=image, user=user)
        self.db.session.add(new_container)
        self.db.session.commit()
        return True

    def remove_container(self, container):
        """
            Remove the container information in the database.
            Return True if successful, False otherwise
        :param container: Container object.
        """
        self.db.session.delete(container)
        self.db.session.commit()
        return True

    @staticmethod
    def get_container(container_id):
        """ Query the database for running container's
            information based on its ID.
        :param container_id:
        :return: Container object
        """
        return Containers.query.get(container_id)

    @staticmethod
    def get_container_by_name(con_name):
        """ Query the database for running container's information based on its name.
        :param con_name: string
        :return: container object
        """
        return Containers.query.filter_by(container_name=con_name).first()

    def add_deleted_container(self, con):
        try:
            cons = self.get_all_deleted_containers()
            if con in cons:
                return False
            del_con = DelContainers(container_id=con.container_id,
                                    container_name=con.container_name,
                                    node=con.node, nat_port=con.nat_port)
            self.db.session.add(del_con)
            self.db.session.commit()
        except Exception as e:
            self.db.session.rollback() 
        return True

    @staticmethod
    def get_all_deleted_containers():
        return DelContainers.query.all()

    def remove_deleted_container(self, con):
        self.db.session.delete(con)
        self.db.session.commit()
        return True
