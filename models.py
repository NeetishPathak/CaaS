import datetime

from flask import Flask
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from config import DEFAULT_CPU, DEFAULT_RAM, COMPUTE_NODE_STATUS_DICT

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
logger = app.logger

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))

    def __repr__(self):
        return "\n(User: (id: {0}, name: {1} email: {2}))".format(self.id, self.username, self.email)


class ComputeNode(db.Model):
    __tablename__ = 'computenode'
    id = db.Column(db.Integer, primary_key=True)
    ip_addr = db.Column(db.String(100), unique=True, nullable=False)
    compute_node_status = db.Column(db.String(80), default=COMPUTE_NODE_STATUS_DICT["default"])
    compute_node_wt = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return "\n(Node: (id: {0}, ip: {1}, wt: {2}, status: {3})".format(
            self.id, self.ip_addr, self.compute_node_wt, self.compute_node_status)


class Images(db.Model):
    __tablename__ = 'images'
    image_id = db.Column(db.Integer, primary_key=True)
    image_name = db.Column(db.String(80), unique=True, nullable=False)
    image_wt = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    #compute_node_id = db.Column(db.Integer, db.ForeignKey('computenode.id'), nullable=False)
    #computenode = db.relationship("ComputeNode", backref=db.backref("image", lazy=True))

    def __repr__(self):
        return "\n(Image: (id: {0}, name: {1}, wt: {2}))".format(
            self.image_id, self.image_name, self.image_wt)


class Containers(db.Model):
    __tablename__ = 'containers'
    container_id = db.Column(db.String(80), primary_key=True)
    container_name = db.Column(db.String(80), unique=True, nullable=False)
    nat_port = db.Column(db.Integer, nullable=False, unique=True)
    management_ip = db.Column(db.String(80), nullable=False)
    docker_port = db.Column(db.Integer, nullable=False)
    container_status = db.Column(db.String(80))
    ram = db.Column(db.Integer, nullable=False, default=DEFAULT_RAM)
    cpu = db.Column(db.Integer, nullable=False, default=DEFAULT_RAM)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True, default=datetime.datetime.utcnow)  #TODO:change
    container_username = db.Column(db.String(15))
    container_passwd = db.Column(db.String(70))
    node_id = db.Column(db.Integer, db.ForeignKey('computenode.id'), nullable=False)
    image_id = db.Column(db.Integer, db.ForeignKey('images.image_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    node = db.relationship('ComputeNode', backref=db.backref('container', lazy=True))
    image = db.relationship('Images', backref=db.backref('container', lazy=True))
    user = db.relationship('User', backref=db.backref('container', lazy=True))

    def __repr__(self):
        return "\n(Container: (name: {0}, ram: {1}, cpu: {2}, nat_port: {3}, docker_port: {4}))".format(
            self.container_name, self.ram, self.cpu, self.nat_port, self.docker_port)


class DelContainers(db.Model):
    __tablename__ = 'del_containers'
    container_id = db.Column(db.String(80), primary_key=True)
    container_name = db.Column(db.String(80), nullable=False)
    nat_port = db.Column(db.Integer, nullable=False)
    node_id = db.Column(db.Integer, db.ForeignKey('computenode.id'), nullable=False)
    node = db.relationship('ComputeNode', backref=db.backref('del_container', lazy=True))

    def __repr__(self):
        return "\n(Container: (name: {0}))".format(self.container_name)
