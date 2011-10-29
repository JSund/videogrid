#!/usr/bin/env python

import socket
import sys
from optparse import OptionParser
import redis
import videogrid
import livetech.prop.prop as prop

def main():
	parser = OptionParser()
	hostname = socket.gethostname().split('.')[0]
	parser.add_option("-r", "--redis",
			metavar="REDIS",
			help="redis host:port [default: %default]",
			default="localhost:6379")
	parser.add_option("-n", "--name",
			help="live client name [default: %default]",
			default=hostname)

	(opts, args) = parser.parse_args()

	client = opts.name

	redis_host = opts.redis.split(':')[0]
	redis_port = int(opts.redis.split(':')[1])
	redis_client = redis.Redis(host=redis_host, port=redis_port, db=0)
	hierarchy = prop.RedisPropertyHierarchy(redis_client)
	client_prop = hierarchy.getProperty("live.clients." + client + ".video")

	teams_prop = hierarchy.getProperty("live.teams")
	preview_prop = client_prop.get("preview")
	selected_prop = hierarchy.getProperty((preview_prop.get("destination").getValue()))
	videogrid.GridMixer(client, preview_prop, teams_prop, selected_prop).run()

if __name__ == '__main__':
	main()
