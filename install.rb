#!/usr/bin/env ruby
require 'rubygems'
require 'json'
require 'readline'
require 'net/http'
require 'uri'
require 'fileutils'

$toplog_server = "toplog.demo"

def request_toplog(endpoint, method)
	uri = URI(endpoint)
	case method
	when 'get'
		request = Net::HTTP::Get.new(uri.to_s)
	when 'post'
		request = Net::HTTP::Post.new(uri.to_s)
	else
		puts "Exception, unrecognized method in request_toplog"
	end
	request['Accept'] = 'application/json'
	response = Net::HTTP.start(uri.host, uri.port) {|http|
	  http.request(request)
	}

	return JSON.parse(response.body)

end

def download_file(file, path)

	FileUtils.mkdir_p(File.dirname(path))

	Net::HTTP.start('b3f2d1745ecfa432ffd7-9cf6ac512d93e71c4a6d3546d0b6c571.r97.cf2.rackcdn.com') { |http|
		resp = http.get(file)
		open(path, "wb") { |file| file.write(resp.body) } }

end

def download_cloud_file(file, path)

	FileUtils.mkdir_p(File.dirname(path))

	Net::HTTP.start($toplog_server) { |http|
		resp = http.get(file)
		open(path, "wb") { |file| file.write(resp.body) } }

end

def install_forwarder(distrib, config)
    #create config
    config_path = '/usr/bin/toplog/logstash-forwarder/config.json'
    FileUtils.mkdir_p(File.dirname(config_path))
    File.open(config_path, 'w') { |file| file.write(config) }

	case distrib
	when 'debian'
		download_file('/logstash-forwarder_0.3.1_amd64.deb', '/opt/logstash-forwarder/logstash-forwarder_0.3.1_amd64.deb')
		`sudo dpkg -i /opt/logstash-forwarder/logstash-forwarder_0.3.1_amd64.deb`
		download_file('/logstash_forwarder_debian.init', '/etc/init.d/logstash-forwarder')
		download_file('logstash_forwarder_debian.defaults', '/etc/default/logstash-forwarder')
	when 'redhat'
		download_file('/logstash-forwarder-0.3.1-1.x86_64.rpm', '/opt/logstash-forwarder/logstash-forwarder-0.3.1-1.x86_64.rpm')
		`sudo rpm -i /opt/logstash-forwarder/logstash-forwarder-0.3.1-1.x86_64.rpm`
		download_file('/logstash_forwarder_redhat.init', '/etc/init.d/logstash-forwarder')
		download_file('/logstash_forwarder_redhat.sysconfig', '/etc/sysconfig/logstash-forwarder')
	else
		puts "Exception, unrecognized method in request_toplog"
	end
	`sudo cp -r /opt/logstash-forwarder /usr/bin/toplog/ `
	`sudo rm -rf /opt/logstash-forwarder`
	download_file('/toplog-forwarder.pub', '/usr/bin/toplog/logstash-forwarder/ssl/toplog-forwarder.pub')
	#set up forwarder as service
	`sudo chmod 0755 /etc/init.d/logstash-forwarder`
	FileUtils.mkdir_p('/var/log/toplog/')
	`sudo touch /var/log/toplog/logstash-forwarder.log`
	`sudo /etc/init.d/logstash-forwarder start`
 	puts "Successfully installed TopLog's Logstash-Forwarder. Please check /var/log/toplog/logstash-forwarder.log to confirm"
end

def uninstall_forwarder(distrib)
	`sudo service logstash-forwarder stop`

	case distrib
	when 'debian'
		`sudo rm /etc/default/toplog-forwarder`
		`sudo dpkg --remove logstash-forwarder`
	when 'redhat'
		`sudo rm /etc/sysconfig/toplog-forwarder`
		`sudo rpm -e logstash-forwarder-0.3.1-1.x86_64`
	else
		puts "Exception, unrecognized method in request_toplog"
	end

	`sudo rm /etc/init.d/toplog-forwarder`
	`sudo rm -rf /usr/bin/toplog/`
	puts "Successfully uninstalled TopLog Logstash-Forwarder uploader"

end

def change_config
	# get auth token
	puts "Please enter your authentication token:"
	token = gets.chomp

	#get user's log types
	endpoint = "http://#{$toplog_server}/configurations?access_token=#{token}"
	types = request_toplog(endpoint, 'get')

	#prompt to select type
	puts "You have created the following log types:"
	types.each { |id, name| puts "#{id}: #{name}\n" }
	type_selected = false

	until type_selected
		puts "Please enter the corresponding id number of the log type you wish to forward"
		user_type_id = gets.chomp

		if user_type_id =~ /\A\d+\z/ and types.has_key?(user_type_id)
			type_selected = true
		else
			puts "Error, log type not found"
		end
	end

	path_selected = false
	puts "Please enter full path to the log file you wish to forward (example: /path/to/my.log)"
	#get log path
	until path_selected
		path = Readline.readline("> ", true).rstrip
		if File.exist?(path)
			path_selected = true
		else
			puts "File not found, please try again"
		end
	end

	puts "Please enter a name for your stream:"
	stream_name = gets.chomp

	#create stream, get config json
	endpoint = URI.escape("http://#{$toplog_server}/streams?access_token=#{token}&configuration_id=#{user_type_id}&name=#{stream_name}")
	response = request_toplog(endpoint, 'post')

	if response['success']
		#replace path in config
		response['config']['files'].each do |file|
			file['paths'] = [path]
			file['key'] = token
		end

		#install forwarder
		return JSON.pretty_generate(response['config'])

	else
		puts "Could not create stream, please try again"
		exit
	end

end

def check_installed(required)
	installed = File.directory?('/usr/bin/toplog/logstash-forwarder')
	if installed and !required
		puts "It appears the TopLog Forwarder is already installed, please run 'sudo bash install.sh -h' for a list of command args"
		exit
	elsif !installed and required
		puts "It appears the TopLog Forwarder is not installed, please run 'sudo bash install.sh -h' for a list of command args"
		exit
	end
end

#get package based on distrib
if system( "which dpkg >/dev/null 2>/dev/null" )
	distrib = 'debian'
else
	distrib = 'redhat'
end
if !ARGV[0].nil?
	case ARGV[0]
	when '-u'
		check_installed(true)
		uninstall_forwarder(distrib)
	when '-r'
		check_installed(true)
		uninstall_forwarder(distrib)
		config = change_config
		install_forwarder(distrib, config)
	when '-c'
		check_installed(true)
		change_config
		`sudo service logstash-forwarder restart`
		puts "Successfully updated TopLog's Logstash-Forwarder config, please check /usr/bin/toplog/logs/logstash-forwarder.log to confirm"
	when '-h', '--help'
		puts "[-r] Reinstall TopLog Logstash-Forwarder"
		puts "[-u] Uninstall TopLog Logstash-Forwarder"
		puts "[-c] Change uploader configuration"
		puts "[-h] or [--help] List install.sh command args"
		exit
	else
		puts "Invalid argument #{ARGV[0]}\nPlease enter 'sudo ruby install.rb -h' to see full list of possible command arguments"
		exit
	end
else
	check_installed(false)
	config = change_config
	install_forwarder(distrib, config)

end


