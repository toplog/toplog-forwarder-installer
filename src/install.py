 #!/usr/bin/env python
import urllib2
import httplib
import json
import re
import os.path
import readline, glob
import subprocess
import sys
import pprint #TODO: REMOVE THIS

global toplog_server
toplog_server = "app.toplog.io"

def request_toplog(endpoint, method):
    headers = {"Accept": "application/json"}
    connection = httplib.HTTPConnection(globals()["toplog_server"])
    request = connection.request(method, endpoint, "", headers)
    response = connection.getresponse()
    if(response.status == 200):
        body = response.read()
        data = json.loads(body)
    else:
        data = False
    connection.close()
    return data

def download_file(cloud_file, path):
    url = "http://b3f2d1745ecfa432ffd7-9cf6ac512d93e71c4a6d3546d0b6c571.r97.cf2.rackcdn.com/%(cloud_file)s" % vars()
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

def install_forwarder(distrib, config):
    config_path = "/usr/bin/toplog/logstash-forwarder/config.json"
    install_directory = "/var/log/toplog/"
    if not os.path.exists(os.path.dirname(config_path)):
        os.makedirs(os.path.dirname(config_path))
    #write config file
    with open(config_path, "w") as outfile:
        json.dump(config, outfile, indent=4, sort_keys=True)

    if distrib == "debian":
        download_file("/logstash-forwarder_0.3.1_amd64.deb", "/opt/logstash-forwarder/logstash-forwarder_0.3.1_amd64.deb")
        print "Installing Logstash-Forwarder . . ."
        subprocess.call(["dpkg", "-i", "/opt/logstash-forwarder/logstash-forwarder_0.3.1_amd64.deb"])
        download_file("/logstash_forwarder_debian.init", "/etc/init.d/logstash-forwarder")
        download_file("/logstash_forwarder_debian.defaults", "/etc/default/logstash-forwarder")
    elif distrib == "redhat":
        download_file("/logstash-forwarder-0.3.1-1.x86_64.rpm", "/opt/logstash-forwarder/logstash-forwarder-0.3.1-1.x86_64.rpm")
        print "Installing Logstash-Forwarder . . ."
        subprocess.call(["rpm", "-i", "/opt/logstash-forwarder/logstash-forwarder-0.3.1-1.x86_64.rpm"])
        download_file("/logstash_forwarder_redhat.init", "/etc/init.d/logstash-forwarder")
        download_file("/logstash_forwarder_redhat.sysconfig", "/etc/sysconfig/logstash-forwarder")
    else:
        print "Exception, unrecognized distribution %(distrib)s" % vars()
        exit()

    subprocess.call(["cp", "-r", "/opt/logstash-forwarder", "/usr/bin/toplog/"])
    subprocess.call(["rm", "-rf", "/opt/logstash-forwarder"])
    download_file("/toplog-forwarder.pub", "/usr/bin/toplog/logstash-forwarder/ssl/toplog-forwarder.pub")
    subprocess.call(["chmod", "640", "/usr/bin/toplog/logstash-forwarder/ssl/toplog-forwarder.pub"])
    #set up forwarder as service
    subprocess.call(["chmod", "0755", "/etc/init.d/logstash-forwarder"])
    if not os.path.exists(install_directory):
        os.makedirs(install_directory)
    subprocess.call(["touch", "/var/log/toplog/logstash-forwarder.log"])
    subprocess.call(["/etc/init.d/logstash-forwarder", "start"])
    print "Successfully installed TopLog's Logstash-Forwarder. Please check /var/log/toplog/logstash-forwarder.log to confirm"


def create_stream(token, path, user_type_id, stream_name):
    escaped_stream_name = urllib2.quote(stream_name)
    endpoint = "/streams?access_token=%(token)s&configuration_id=%(user_type_id)s&name=%(escaped_stream_name)s" % vars()
    response = request_toplog(endpoint, "POST")

    if response:
        for file_config in response["files"]:
            file_config["paths"] = [path]
            file_config["fields"]["key"] = token
            return response
    else:
        print "Error: Could not create stream %(stream_name)s. Please try again" % vars()
        exit()

def uninstall_forwarder(distrib):
    subprocess.call(["service", "logstash-forwarder", "stop"])

    if distrib == "debian":
        subprocess.call(["dpkg", "--remove", "logstash-forwarder"])
    elif distrib == "redhat":
        subprocess.call(["rpm", "-e", "logstash-forwarder-0.3.1-1.x86_64"])
    else:
        print "Exception, unrecognized method in request_toplog"

    subprocess.call(["rm", "-rf", "/usr/bin/toplog/"])
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

def add_to_stream():
    is_multiple = False
    token_valid = False
    add_complete = False

    while not token_valid:
        print "Please enter your authentication token:"
        token = raw_input()
        endpoint = "/streams?access_token=%(token)s" % vars()
        streams = request_toplog(endpoint, "GET")
        if streams:
            token_valid = True
        else:
            print "Error, authentication token not valid. Please re-enter or generate a new token"

    type_selected = False
    print "You have created the following streams:"
    for (type_id, name) in streams.items():
        print "%(type_id)s: %(name)s" % vars()

    while not type_selected:
        print "Please enter the corresponding id number of the stream you wish to forward to"
        user_stream_id = raw_input()
        if(user_stream_id.isdigit() and user_stream_id in streams):
            type_selected = True
        else:
            print "Error, stream not found"

    path = get_path()
    stream_config = get_stream_config(token, path, user_stream_id)
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

def change_config():
    config_complete = False
    is_multiple = False
    token_valid = False
    while not config_complete:

        while not token_valid:
            print "Please enter your authentication token:"
            token = raw_input()
            endpoint = "/logs?access_token=%(token)s" % vars()
            types = request_toplog(endpoint, "GET")
            if types:
                token_valid = True
            else:
                print "Error, authentication token not valid. Please re-enter or generate a new token"


        type_selected = False
        print "You have created the following log types:"
        for (type_id, name) in types.items():
            print "%(type_id)s: %(name)s" % vars()

        while not type_selected:
            print "Please enter the corresponding id number of the log type you wish to forward"
            user_type_id = raw_input()
            if(user_type_id.isdigit() and user_type_id in types):
                type_selected = True
            else:
                print "Error, log type not found"

        path = get_path()

        print "Please enter a name for your stream:"
        stream_name = raw_input()
        stream_config = create_stream(token, path, user_type_id, stream_name)
        if is_multiple:
            previous_config["files"].append(stream_config["files"][0])
            stream_config = previous_config

        confirm_valid = False
        while not confirm_valid:
            print "Would you like to create another stream [yes/no]?"
            confirm = raw_input()
            if (confirm.lower() == "y" or confirm.lower() == "yes"):
                if not is_multiple:
                    previous_config = stream_config
                    is_multiple = True
                confirm_valid = True
            elif (confirm.lower() == "n" or confirm.lower() == "no"):
                config_complete = True
                confirm_valid = True
            else:
                print "Error, invalid response. Please only enter 'yes' or 'no'"

    return stream_config

def check_installed(required):
    installed = os.path.exists("/usr/bin/toplog/logstash-forwarder")
    if installed and not required:
        print "It appears the TopLog Forwarder is already installed, please run 'sudo python install.py -h' for a list of command args"
        exit()
    elif not installed and required:
        print "It appears the TopLog Forwarder is not installed, please run 'sudo python install.py -h' for a list of command args"
        exit()
def default_install(distrib):
    check_installed(False)
    config = change_config()
    install_forwarder(distrib, config)

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
        config = change_config()
        install_forwarder(distrib, config)
    elif "-c" in sys.argv:
        check_installed(True)
        change_config()
        subprocess.call(["service", "logstash-forwarder", "restart"])
        print "Successfully updated TopLog's Logstash-Forwarder config, please check /usr/bin/toplog/logs/logstash-forwarder.log to confirm"
    elif "-a" in sys.argv:
        check_installed(False)
        config = add_to_stream()
        install_forwarder(distrib, config)
    elif ("-h" in sys.argv or "--help"in sys.argv):
        print "[-r] Reinstall TopLog Logstash-Forwarder"
        print "[-u] Uninstall TopLog Logstash-Forwarder"
        print "[-c] Change uploader configuration"
        print "[-a] Add to existing stream"
        print "[-h] or [--help] List install.py command args"
    elif change_host:
        default_install(distrib)
    else:
        print "Invalid argument %s\nPlease enter 'sudo python install.py -h' to see full list of possible command arguments" % sys.argv[1:]
        exit()
else:
    default_install(distrib)
