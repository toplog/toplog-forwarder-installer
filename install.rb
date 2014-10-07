#!/usr/bin/env ruby
require 'rubygems'
require 'json'
require 'readline'
require 'net/http'
require 'uri'

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

def install_forwarder(config)
    script_path = File.expand_path(File.dirname(__FILE__))
    #create config
    File.open('/usr/bin/toplog/logstash-forwarder/config.json', 'w') { |file| file.write(config) }
	`sudo mkdir /usr/bin/toplog`
	`sudo dpkg -i $scriptPath/builds/logstash-forwarder_0.3.1_amd64.deb `
	`sudo cp -r /opt/logstash-forwarder /usr/bin/toplog/ `
	`sudo rm -rf /opt/logstash-forwarder`
	`sudo cp -r $scriptPath/ssl /usr/bin/toplog/logstash-forwarder/`
	#set up forwarder as service
	`sudo wget http://toplog.demo/downloads/#{distrib}/toplog.tar.gz`
	`tar -xzvf toplog.tar.gz #{script_path}`
	`sudo cp #{script_path}/client_uploader_deb/logstash_forwarder_debian.init /etc/init.d/logstash-forwarder`
	`sudo chmod 0755 /etc/init.d/logstash-forwarder`
	`sudo cp #{script_path}/client_uploader_deb/logstash_forwarder_debian.defaults /etc/default/logstash-forwarder`
	`sudo mkdir /var/log/toplog/`
	`sudo touch /var/log/toplog/logstash-forwarder.log`
	`sudo /etc/init.d/logstash-forwarder start`

end

#get package based on distrib
if system( "which dpkg >/dev/null 2>/dev/null" )
	distrib = 'debian'
else
	distrib = 'redhat'
end

# get auth token
puts "Please enter your authentication token:"
token = gets.chomp

#get user's log types
endpoint = "http://toplog.demo/configurations?access_token=#{token}"
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
	path = Readline.readline("> ", true)
	if File.exist?(path)
		path_selected = true
	else
		puts "File not found, please try again"
	end
end

puts "Please enter a name for your stream:"
stream_name = gets.chomp

#create stream, get config json
endpoint = URI.escape("http://toplog.demo/streams?access_token=#{token}&configuration_id=#{user_type_id}&name=#{stream_name}")
response = request_toplog(endpoint, 'post')

if response['success']
	#replace path in config
	response['config']['files'].each do |file|
		file['paths'] = path
	end

	#install forwarder
	install_forwarder(response['config'].to_json)

else
	puts "Could not create stream, please try again"
	exit
end

