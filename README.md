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
