greplin-nagios-utils: checkserver
=================================

Simple server that checks status of memcached messages from services
--------------------------------------------------------------

### Dependencies

[Tornado](/facebook/tornado)

### Usage

Checkserver checks memached for data in the form of a JSONified string ala:

    {'state':'OK: The service is working ok', 'timestamp':11123123}
    
The key for memcached should be the same as the argument that gets passed to memcached_check.sh. 
If you do YOUR_NAGIOS_COMMAND!important_service) the checkserver is going to look after the key 'important_server'    


Using checkserver is simple, run an instance of the server, and then add a nagios command(commands.cfg)

#Note that this is looking in the default folder for scripts, you can also specify absolute path
	define command {
	    command_name    memcached_check
	    command_line    $USER1$/memcacade_check.sh $ARG1$
	}

and then a service which uses the command

	define service {
	    use                     your-service-type
	    service_description     Your Description Here
	    check_command           memcached_check!look_for_this_key_in_memcache
	    hostgroup_name          your-hostgroup
	}

Author: Simon Johansson
