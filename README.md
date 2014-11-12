[![Stories in Ready](https://badge.waffle.io/toplog/toplog-forwarder-installer.png?label=ready&title=Ready)](https://waffle.io/toplog/toplog-forwarder-installer)
toplog-forwarder-installer
==========================

The script that installs the forwarder and configuration.

###Requirements:
Ruby (at least version 1.9.3)

#### Ubuntu 12.04: Update to Ruby 1.9.3
To update to the correct ruby version, follow these step [Link](https://leonard.io/blog/2012/05/installing-ruby-1-9-3-on-ubuntu-12-04-precise-pengolin/ "Outside Link")

###Supported OS:

*	 Debian Linux 

* 	 Red Hat Linux 


In Time there will be different installers for the following deployments: 

*	Windows

*	Mac OS X

###Installation:

`sudo ruby install.rb`

Command args:

`[-h]` Displays install script's command args

`[-c]` Changes the forwarder's configuration and restarts the forwarder

`[-r]` Reinstalls the forwarder

`[-u]` Uninstalls the forwarder

### What the install.rb script does:

* Installer: asks for the users auth key (get from toplog account)
* Installer: Authenticates against the app.toplog.io server, fetches the user's log types
 * a json object containing the list of the log types and their IDs is returned to the installer
* Installer: presents the list to the user, 
* User: selects log type based on the presented ID
* Installer: asks the User which log file they want to monitor (full path)
* Installer: asks if they want to set up more, 
 * if so, repeat log type selection, file selection, continue this loop as many times as the user selects "yes"
* Installer: Once done, send the pairings of log type ID and file path to app.toplog.io (along with Auth Key), server will respond with a stream ID as well as other logstash-forwarder configuration details
* Installer: Takes this response (json), builds the logstash-forwarder config, pulls down the correct dep, init, etc files for logstash-forwarder (based on OS) from our public copies, places in the correct places (/usr/bin/toplog) and starts up the forwarder
