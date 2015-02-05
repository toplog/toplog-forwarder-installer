[![Stories in Ready](https://badge.waffle.io/toplog/toplog-forwarder-installer.png?label=ready&title=Ready)](https://waffle.io/toplog/toplog-forwarder-installer)
toplog-forwarder-installer
==========================

This script installs the [forwarder](https://github.com/elasticsearch/logstash-forwarder/) that ships your logs to us!

###Requirements:
* Python 2.7
* Valid authentication token from [Toplog](https://app.toplog.io/streams/installation)
* A log file you want to analyse

###Supported OS:
* Debian Linux
* Red Hat Linux

###Installation:
Create an account at https://app.toplog.io/

Generate your unique authentication token at https://app.toplog.io/streams/installation

Execute `sudo python install.py` in your terminal.

This will prompt you to create a Toplog stream, set a log file to send to us and install the forwarder.

###Command args:

`[-h]` Displays install script's command args

`[-c]` Change a stream currently being forwarded by this machine

`[-a]` Add file to an existing stream

`[-l]` List streams currently being forwarded by this machine

`[-d]` Disable a stream currently being forwarded by this machine

`[-r]` Reinstalls the forwarder

`[-u]` Uninstalls the forwarder

###More info:
This script will install our packaged [logstash-forwarder](https://github.com/elasticsearch/logstash-forwarder/)
and set it up as a init.d or sysconfig service.

###Files written to:
A number of files will be created/modified upon installation & various configuration options.

* Install Directory: `/usr/bin/toplog/logstash-forwarder/`
  * Public SSL certicate: `./ssh/toplog-forwarder.pub`
  * Logstash-forwarder configuration files: `./conf.d`
  * Service scripts:
    * Debian: `/etc/init.d/logstash-forwarder`, `/etc/default/logstash-forwarder`
    * Red Hat: `/etc/init.d/logstash-forwarder`, `/etc/sysconfig/logstash-forwarder`
