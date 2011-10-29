#!/usr/bin/env python
"""Code for setting up the property system."""
import redis
import time
import livetech.prop.prop as prop
import sys

r = redis.Redis(host="localhost", port=6379, db=0)
h = prop.RedisPropertyHierarchy(r)
ranges = {
        1: "1-25",
        2: "26-50",
        3: "51-75",
        4: "76-100",
        5: "101-105"
}
destination = "live.clients.team.team.team"
for team in range(1,106):
    h.getProperty("live.teams." + str(team) + ".path").setValue("http://192.168.1.14" + ("1" if team % 2 == 1 else "2") + ":" + str(58000 + team))
for client, teams in ranges.iteritems():
    h.getProperty("live.clients.grid-" + str(client) + ".video.preview.destination").setValue(destination)
    h.getProperty("live.clients.grid-" + str(client) + ".video.preview.range").setValue(teams)
    h.getProperty(destination).setValue(1)
sys.exit(0)
