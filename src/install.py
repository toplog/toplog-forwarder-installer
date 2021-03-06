 #!/usr/bin/env python
import urllib
import urllib2
import json
import re
import os.path
import readline, glob
import subprocess
import sys

global toplog_server
global version
global log_directory
global install_directory
global config_directory
toplog_server = "https://app.toplog.io"
file_server = "http://files.toplog.io"
version = "1.3"
install_directory = "/usr/local/logstash-forwarder/"
log_directory = "/var/log/logstash-forwarder/"
config_directory = "/etc/logstash-forwarder/conf.d/"

def request_toplog(endpoint, method, data = None):
    headers = {"Accept": "application/json"}
    url = globals()["toplog_server"] + endpoint
    request = urllib2.Request(url, data, headers)
    try:
        response = urllib2.urlopen(request)
        if(response.getcode() == 200):
            body = response.read()
            data = json.loads(body)
        else:
            data = False
        response.close()
    except (urllib2.HTTPError, ValueError) as e:
        data = False

    return data

def download_file(cloud_file, path, server = file_server):
    url = "%(server)s/%(cloud_file)s" % vars()
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))

    file_name = url.split("/")[-1]
    u = urllib2.urlopen(url)
    f = open(path, "wb")
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    print "Downloading: %s Bytes: %s" % (file_name, file_size)

    file_size_dl = 0
    block_sz = 8192
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break

        file_size_dl += len(buffer)
        f.write(buffer)
        status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
        status = status + chr(8)*(len(status)+1)
        print status,

    f.close()

def print_success(task, log_directory):
    print "Successfully %(task)s. Please check %(log_directory)slogstash-forwarder.log to confirm" % vars()

def set_logrotate(log_directory):
    content = "%(log_directory)slogstash-forwarder.log {\n\tdaily\n \trotate 5\n \tcopytruncate\n \tdelaycompress\n \tcompress\n \tnotifempty\n \tmissingok\n }\n" % vars()
    f = open("/etc/logrotate.d/toplog", "wb")
    f.write(content)
    f.close

def install_forwarder(distrib):
    if distrib == "debian":
        download_file("logstash-forwarder_1.2_amd64.deb", "/opt/logstash-forwarder/logstash-forwarder_master_amd64.deb")
        print "Installing Logstash-Forwarder . . ."
        subprocess.call(["dpkg", "-i", "/opt/logstash-forwarder/logstash-forwarder_master_amd64.deb"])
        download_file("logstash_forwarder_1.3_debian.init", "/etc/init.d/logstash-forwarder")
        download_file("logstash_forwarder_1.3_debian.defaults", "/etc/default/logstash-forwarder")
    elif distrib == "redhat":
        download_file("logstash-forwarder_1.2_x86_64.rpm", "/opt/logstash-forwarder/logstash-forwarder_1.2_x86_64.rpm")
        print "Installing Logstash-Forwarder . . ."
        subprocess.call(["rpm", "-i", "/opt/logstash-forwarder/logstash-forwarder_1.2_x86_64.rpm"])
        download_file("logstash_forwarder_1.3_redhat.init", "/etc/init.d/logstash-forwarder")
        download_file("logstash_forwarder_1.3_redhat.sysconfig", "/etc/sysconfig/logstash-forwarder")
    else:
        print "Exception, unrecognized distribution %(distrib)s" % vars()
        exit()

    if not os.path.exists(install_directory):
        os.makedirs(install_directory)
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
        set_logrotate(log_directory)
    subprocess.call(["cp", "-rf", "/opt/logstash-forwarder/bin", install_directory])
    subprocess.call(["rm", "-rf", "/opt/logstash-forwarder"])
    download_file("toplog-forwarder.pub", "/etc/logstash-forwarder/ssl/toplog-forwarder.pub")
    subprocess.call(["chmod", "640", "/etc/logstash-forwarder/ssl/toplog-forwarder.pub"])
    #set up forwarder as service
    subprocess.call(["chmod", "0755", "/etc/init.d/logstash-forwarder"])
    subprocess.call(["/etc/init.d/logstash-forwarder", "start"])
    print_success("installed TopLog's Logstash-Forwarder", log_directory)

def store_stream(token, path, user_type_id, stream_name):
    endpoint = "/streams"
    data = urllib.urlencode({'access_token': token, 'configuration_id': user_type_id, 'name': stream_name})
    response = request_toplog(endpoint, "POST", data)

    if response:
        for file_config in response["files"]:
            file_config["paths"] = [path]
            file_config["fields"]["key"] = token
            return response
    else:
        print "Error: Could not create stream %(stream_name)s. Please try again" % vars()
        exit()

def uninstall_forwarder(distrib, uninstall_directory = install_directory):
    subprocess.call(["service", "logstash-forwarder", "stop"])

    if distrib == "debian":
        subprocess.call(["dpkg", "--remove", "logstash-forwarder"])
    elif distrib == "redhat":
        subprocess.call(["rpm", "-e", "logstash-forwarder-0.3.1-1.x86_64"])
    else:
        print "Exception, unrecognized method in request_toplog"

    subprocess.call(["rm", "-rf", uninstall_directory])
    if os.path.exists(log_directory):
        subprocess.call(["rm", "-rf", log_directory])
    print "Successfully uninstalled TopLog Logstash-Forwarder uploader"

def get_path():
    path_selected = False
    print "Please enter full path to the log file you wish to forward (example: /path/to/my.log)"

    while not path_selected:
        readline.set_completer_delims(" \t\n;")
        readline.parse_and_bind("tab: complete")
        path = raw_input()
        if os.path.isfile(path):
            path_selected = True
        else:
            print "File not found, please try again"

    return path

def send_request(request, token):
    endpoint = "/%(request)s?access_token=%(token)s" % vars()
    return request_toplog(endpoint, "GET")

def check_token(request):
    token_valid = False
    while not token_valid:
        print "Please enter your authentication token:"
        token = raw_input()
        data = send_request(request, token)
        if data is not False:
            token_valid = True
        else:
            print "Error, authentication token not valid. Please re-enter or generate a new token"
    return (token, data)

def get_data(request, required = True):
    token, data = check_token(request)
    if not data and required:
        if request == "logs":
            print "Error, no log types found. You must create a log type to continue."
        elif request == "streams":
            print "Error, no streams found. Please enter 'sudo python install' to create a stream."
    return (token, data)

def confirm_prompt(message):
    confirm_valid = False
    while not confirm_valid:
        print message + " [yes/no]"
        confirm = raw_input()
        if (confirm.lower() == "y" or confirm.lower() == "yes"):
            confirm = True
            confirm_valid = True
        elif (confirm.lower() == "n" or confirm.lower() == "no"):
            confirm = False
            confirm_valid = True
        else:
            print "Error, invalid response. Please only enter 'yes' or 'no'"
    return confirm

def create_stream_keys(streams):
    stream_keys = {}
    counter = 0
    for (stream_id, name) in streams.items():
        counter += 1
        stream_keys[counter] = stream_id

    return stream_keys

def list_streams(streams, stream_keys, message):
    print message
    for (stream_id_key, stream_id) in stream_keys.items():
        name = streams[stream_id]
        print "%(stream_id_key)s: %(name)s" % vars()

def get_local_streams(streams = None):
    local_streams = {}
    filenames = next(os.walk(config_directory))[2]
    for file in filenames:
        stream_id = os.path.splitext(file)[0]
        if stream_id in streams:
            local_streams[stream_id] = streams[stream_id]

    return local_streams

def select_stream(streams, stream_keys, task = "select", dir = config_directory):
    stream_selected = False
    while not stream_selected:
        print "Please enter the corresponding id number of the stream you wish to %(task)s forwarding:" % vars()
        user_input = raw_input()
        if(user_input.isdigit()):
            user_stream_id = int(user_input)
        if(stream_keys[user_stream_id] in streams):
            config_path = "%(dir)s%(user_stream_id)s.json" % vars()
            if not os.path.exists(config_path):
                stream_selected = True
            else:
                overwrite = confirm_prompt("Warning: files on this machine are currently being forwarded for this stream.\nThis will destroy the previous configuration. Would you like to continue?")
                if overwrite:
                    stream_selected = True
        else:
            print "Error, stream not found"

    return stream_keys[user_stream_id]

def disable_stream():
    disable_complete = False
    token, streams = get_data("streams")
    while not disable_complete:
        local_streams = get_local_streams(streams)
        if local_streams:
            stream_keys = create_stream_keys(local_streams)
            list_streams(local_streams, stream_keys, "The following streams are currently being forwarded from this machine:")
            print "Which stream would you like to disable? (This will not disable any other forwarders for this stream.)"
            stream_id = select_stream(local_streams, stream_keys, "disable")
            name = local_streams[stream_id]
            config = config_directory + "%(stream_id)s.json" % vars()
            os.remove(config)
            print "Stream %(name)s disabled" % vars()
            if len(local_streams) > 1:
                disable_complete = not confirm_prompt("Would you like to disable another stream?")
            else:
                disable_complete = True
        else:
            print "No streams currently being forwarded. Please enter 'sudo python install.py -h' to see full list of possible command arguments."
            exit()

    return (token, streams)

def get_stream_config(token, path, user_stream_id):
    endpoint = "/streams/%(user_stream_id)s/generate_configuration?access_token=%(token)s" % vars()
    response = request_toplog(endpoint, "GET")
    if response:
        for file_config in response["files"]:
            file_config["paths"] = [path]
            file_config["fields"]["key"] = token
            return response
    else:
        print "Error: Could not get configuration for stream %(user_stream_id)s. Please try again" % vars()
        exit()

def get_network_config(token):
    endpoint = "/streams/generate_network_configuration?access_token=%(token)s" % vars()
    response = request_toplog(endpoint, "GET")
    if response:
        return response
    else:
        print "Error: Could not get network configuration. Please try again" % vars()
        exit()

def add_file_to_stream_config(stream_config):
    is_multiple = False
    add_complete = False

    while not add_complete:
        if is_multiple:
            path = get_path()
            stream_config["files"][0]["paths"].append(path)
        confirm_valid = False
        while not confirm_valid:
            print "Would you like to add another file to your stream [yes/no]?"
            confirm = raw_input()
            if (confirm.lower() == "y" or confirm.lower() == "yes"):
                if not is_multiple:
                    is_multiple = True
                confirm_valid = True
            elif (confirm.lower() == "n" or confirm.lower() == "no"):
                add_complete = True
                confirm_valid = True
            else:
                print "Error, invalid response. Please only enter 'yes' or 'no'"

    return stream_config

def add_file_to_stream(token = None, streams = None):
    add_complete = False
    if not token and not streams:
        token, streams = get_data("streams")
    stream_keys = create_stream_keys(streams)

    while not add_complete:
        type_selected = False
        list_streams(streams, stream_keys, "You have created the following streams:")
        user_stream_id = select_stream(streams, stream_keys, "add")
        path = get_path()
        config = get_stream_config(token, path, user_stream_id)
        stream_config = add_file_to_stream_config(config)
        write_config(config, config['files'][0]['fields']['stream_id'])
        add_complete = not confirm_prompt("Would you like to add to another stream?")

    net_config = get_network_config(token)
    write_config(net_config, "network")


def write_config(config, name, dir = config_directory):
    config_path = "%(dir)s%(name)s.json" % vars()
    if not os.path.exists(os.path.dirname(config_path)):
        os.makedirs(os.path.dirname(config_path))
    #write config file
    with open(config_path, "w") as outfile:
        json.dump(config, outfile, indent=4, sort_keys=True)

def create_stream(token = None):
    config_complete = False
    if token:
        types = send_request("logs", token)
    else:
        token, types = get_data("logs", True)

    type_keys = create_stream_keys(types)
    while not config_complete:
        type_selected = False

        list_streams(types, type_keys, "You have created the following log types:")
        while not type_selected:
            print "Please enter the corresponding id number of the log type you wish to forward"
            user_input = raw_input()
            if(user_input.isdigit()):
                user_type_id = int(user_input)
                if(type_keys[user_type_id] in types):
                    type_selected = True
                else:
                    print "Error, log type not found"

        path = get_path()

        print "Please enter a name for your stream:"
        stream_name = raw_input()
        config = store_stream(token, path, type_keys[user_type_id], stream_name)
        stream_config = add_file_to_stream_config(config)
        write_config(stream_config, config['files'][0]['fields']['stream_id'])

        config_complete = not confirm_prompt("Would you like to create another stream?")

        print "Stream %(stream_name)s created." % vars()

    net_config = get_network_config(token)
    write_config(net_config, "network")

def force_reinstall(distrib, version):
    print "It appears you have previously installed with version < %(version)s\nUpdating will require reinstallation & re-adding of streams\n Warning: You will need to enter your authentication token." % vars()
    update = confirm_prompt("Would you like to continue?")
    if update:
        uninstall_forwarder(distrib, "/usr/bin/toplog/logstash-forwarder/")
        default_install(distrib)
        exit()
    else:
        exit()

def check_outdated(distrib):
    outdated_1_3 = os.path.exists("/usr/bin/toplog/logstash-forwarder/bin/")
    if outdated_1_3:
        force_reinstall(distrib, '1.3')

def check_installed(required):
    installed = os.path.exists(install_directory)
    if installed and not required:
        print "It appears the TopLog Forwarder is already installed. Any changes will be applied to current installation."
    elif not installed and required:
        print "It appears the TopLog Forwarder is not installed, please run 'sudo python install.py -h' for a list of command args"
        exit()

    return installed

def restart_service(task):
    print "Restarting logstash-forwarder service . . ."
    subprocess.call(["service", "logstash-forwarder", "restart"])
    print_success(task, log_directory)

def default_install(distrib):
    installed = check_installed(False)

    token, data = get_data("streams", False)
    if data:
        if confirm_prompt("It appears you have streams created. Would you like to forward a log to an existing stream?"):
            add_file_to_stream(token, data)
        else:
            create_stream(token)
    else:
        create_stream(token)
    if not installed:
        install_forwarder(distrib)
    else:
        restart_service("created stream(s)")

def add_stream():
    installed = check_installed(False)
    if not installed:
        print "It appears the TopLog Forwarder is not installed. Will install after completing configuration"
        add_file_to_stream()
        install_forwarder(distrib)
    else:
        add_file_to_stream()
        restart_service("added stream(s)")

def list_local_streams():
    check_installed(True)
    token, streams = get_data("streams")
    local_streams = get_local_streams(streams)
    local_stream_keys = create_stream_keys(local_streams)
    if local_streams:
        list_streams(local_streams, local_stream_keys, "The following streams are currently being forwarded from this machine:")
    else:
        print "No streams currently being forwarded. Please enter 'sudo python install.py -h' to see full list of possible command arguments."

#check permissions
if not os.geteuid() == 0:
    print "You need root permissions to do run this script. Please enter 'sudo python install.py'"
    exit()

#check distrib
try:
    FNULL = open(os.devnull, 'w')
    code = subprocess.call(["which", "dpkg", ">/dev/null", "2>/dev/null"], stdout=FNULL, stderr=subprocess.STDOUT)
except OSError as e:
    distrib = "redhat"

if code != 1:
    distrib = "redhat"
else:
    distrib = "debian"

check_outdated(distrib)

#command args
change_host = False
if len(sys.argv) > 1:
    if ("--host" in sys.argv):
        key = sys.argv.index("--host")
        host_key = key + 1
        if len(sys.argv[host_key]) > 1:
            toplog_server = sys.argv[host_key]
            print "Host server set to %(toplog_server)s" % vars()
            change_host = True
        else:
            print "Invalid hostname"
            exit()

    if "-u" in sys.argv:
        check_installed(True)
        uninstall_forwarder(distrib)
    elif "-r" in sys.argv:
        check_installed(True)
        uninstall_forwarder(distrib)
        create_stream()
        install_forwarder(distrib)
    elif "-c" in sys.argv:
        check_installed(True)
        token, streams = disable_stream()
        add_file_to_stream(token, streams)
        restart_service("changed streams")
    elif "-a" in sys.argv:
        add_stream()
    elif "-l" in sys.argv:
        list_local_streams()
    elif "-d" in sys.argv:
        check_installed(True)
        disable_stream()
        restart_service("disabled stream(s)")
    elif ("-h" in sys.argv or "--help"in sys.argv):
        print "Default usage: Create topLog stream & install Logstash-Forwarder"
        print "[-r] Reinstall Logstash-Forwarder"
        print "[-u] Uninstall Logstash-Forwarder"
        print "[-c] Change a stream currently being forwarded by this machine"
        print "[-a] Add file to an existing stream"
        print "[-l] List streams currently being forwarded by this machine"
        print "[-d] Disable a stream currently being forwarded by this machine"
        print "[-h] or [--help] List install.py command args"
    elif change_host:
        default_install(distrib)
    else:
        print "Invalid argument %s\nPlease enter 'sudo python install.py -h' to see full list of possible command arguments." % sys.argv[1:]
        exit()
else:
    default_install(distrib)
