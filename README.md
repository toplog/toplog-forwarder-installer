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

`[-a]` Add file(s) to existing Toplog stream

`[-c]` Change current log stream

`[-r]` Reinstalls the forwarder

`[-u]` Uninstalls the forwarder
