import os
import pdb
import requests
import subprocess as sp
import threading
from time import sleep

from flask import render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_login import LoginManager, login_required, logout_user, current_user

from lib.DatabaseManager import DatabaseManager
from lib.ContainerManager import ContainerManager
from models import app
from models import db
from db_create import create_db_schema
from db_insert import insert_default_entries

from config import db_file_name, COMPUTE_NODE_STATUS_DICT
from config import CONTAINER_HEALTH_QUERY_URI, HEALTH_CHECK_INTERVAL 
from config import CONTAINER_HEALTH_QUERY_PORT

Bootstrap(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
database = DatabaseManager(db)
con_manager = ContainerManager(database)


@login_manager.user_loader
def load_user(user_id):
    return database.get_user(id=user_id)


class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')


class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if database.authenticate(username=form.username.data,
                                 password=form.password.data,
                                 remember_me=form.password.data):
            if form.username.data =="admin":
                app.logger.info("Login success. Admin User: {0}".format(form.username.data))
                return redirect(url_for('admin_dashboard'))
            else:
                app.logger.info("Login success. User: {0}".format(form.username.data))
                return redirect(url_for('dashboard'))
    app.logger.error("Login failed {0}".format(form.username.data))
    return render_template('login.html', form=form)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()
    if form.validate_on_submit():
        database.add_user(name=form.username.data, email=form.email.data, password=form.password.data)
        app.logger.info("Success User signed up. {0}".format(form.username.data))
        return redirect(url_for('login'))
    app.logger.error("Failed. Signup. {0}".format(form.username.data))
    return render_template('signup.html', form=form)


@app.route('/delete_reservation', methods=['POST'])
@login_required
def delete_reservation():
    container_id = request.form['delete']
    result = con_manager.delete_reservation(container_id)
    if result == 0:
        message = "Success. Container reservation deleted successfully"
    else:
        message = "Error. Error in deleting container reservation"

    images = database.get_all_images()
    reservations = database.get_user_reservations(user=current_user)
    app.logger.info(message)
    return render_template('dashboard.html', name=current_user.username, images=images, user_containers=reservations,
                           error=message)


@app.route('/create_user_reservation', methods=['POST'])
@login_required
def create_user_reservation():
    val = request.form
    app.logger.debug("************ val: *****", val)
    result = con_manager.create_reservation(current_user.username, val)
    if result == 0:
        message = "Success!! Reservation created successfully!!"
    else:
        message = "Error!! Error in creating reservation!!"
    images = database.get_all_images()
    reservations = database.get_user_reservations(user=current_user)
    app.logger.debug(message)
    return render_template('dashboard.html', name=current_user.username, images=images, user_containers=reservations,
                           error = message)

@app.route('/dashboard')
@login_required
def dashboard():
    images = database.get_all_images()
    reservations = database.get_user_reservations(user=current_user)
    return render_template('dashboard.html', name=current_user.username, images=images, user_containers=reservations,
                           error = "")

@app.route('/admin_delete_reservation', methods=['POST'])
@login_required
def admin_delete_reservation():
    container_id = request.form['delete']
    result = con_manager.delete_reservation(container_id)
    if result == 0:
        mssg = "Container reservation deleted successfully"
    else:
        mssg = "Error!! Error in deleting container reservation"
    computeNodes_wt = database.get_all_computeodes_with_load()
    reservations = database.get_all_containers()
    images = database.get_all_images()
    return render_template('adminDashboard.html', name=current_user.username, compute_nodes=computeNodes_wt, reservations=reservations, images=images)

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    computeNodes_wt = database.get_all_computeodes_with_load()
    reservations = database.get_all_containers()
    images = database.get_all_images()
    print("*********priyal*******")
    print(computeNodes_wt)
    return render_template('adminDashboard.html', name=current_user.username, compute_nodes=computeNodes_wt, reservations=reservations, images=images)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


def monitor_server_health():
    try:
        compute_nodes = database.get_all_computenodes()
        for node in compute_nodes:
            # res will be 0 on success
            command = "ping -c 4 {0}".format(node.ip_addr)
            res = sp.call(command, shell=True, stdout=sp.PIPE)
            database.set_computenode_status(node, res)
            if res == 1:  # res == 1 when ping fails
                con_manager.migrate_all_containers(node)
    except Exception as e:  # You must never exit.
        app.logger.exception("Node health monitor received unhandled exception")


def monitor_container_health():
    try:
        compute_nodes = database.get_all_computenodes()
        for node in compute_nodes:
            if node.compute_node_status != "available":
                continue
            url = "http://{0}:{1}/{2}".format(
                node.ip_addr, CONTAINER_HEALTH_QUERY_PORT, CONTAINER_HEALTH_QUERY_URI)
            container_names = [con.container_name for con in node.container]
            if len(container_names) == 0:
                continue
            try:
                app.logger.debug("Health check on {0} for containers \n{1}".format(url, container_names))
                result = requests.post(url, json=container_names)
            except Exception as e:
                app.logger.exception("Failed container health check. Unable to reach node {0}".format(node.ip_addr))
                continue
            if result.status_code != 200:
                app.logger.exception("Container health check failed. status code = {0}".format(result.status_code))
            else:
                health_stat = result.json()
                for con_name, status in health_stat.items():
                    app.logger.debug("Check {0} status = {1}".format(con_name, status))
                    con_manager.update_container_health(con_name, status)
    except Exception:  # You must not exit.
        app.logger.exception("Health monitor received unhandled exception")


def container_garbage_collector():
    try:
        containers = database.get_all_deleted_containers()
        app.logger.debug("Attempting garbage collection on {0}".format(containers))
        for con in containers:
            if con.node.compute_node_status == COMPUTE_NODE_STATUS_DICT[0]:
                if con_manager.kill_container(con) is True:
                    database.remove_deleted_container(con)
                    app.logger.info("Garbage collected container id {0} from node {1}".format(con.container_id, con.node.ip_addr))
                else:
                    app.logger.error("Garbage collector failed for container id {0} from node {1}".format(con.container_id, con.node.ip_addr))
    except Exception as e:
        app.logger.exception("Garbage collector received exception while reaping containers\n{0}".format(e))

def health_monitor():
    while True:
        try:
            monitor_server_health()
            monitor_container_health()
            container_garbage_collector()
        except Exception as e:
            app.logger("Monitor thread received unhandled exception. {0}".format(e));
        sleep(HEALTH_CHECK_INTERVAL)

if __name__ == '__main__':
    if not os.path.isfile(db_file_name):
        create_db_schema()
        insert_default_entries(db)
    #test_suite(con_manager)
    """
    node_status_thread = threading.Thread(target=monitor_server_health)
    node_status_thread.start()
    container_status_thread = threading.Thread(target=monitor_container_health)
    container_status_thread.start()
    garbage_collector_thread = threading.Thread(target=container_garbage_collector)
    garbage_collector_thread.start()
    """
    monitor_thread =  threading.Thread(target=health_monitor)
    monitor_thread.start()
    app.run(host="0.0.0.0", debug=True, use_reloader=False)
