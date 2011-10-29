#!/usr/bin/env python
"""Code for testing the property system."""
import redis
import time
import livetech.prop.prop as prop

r = redis.Redis(host="localhost", port=6379, db=0)
h = prop.RedisPropertyHierarchy(r)
p = h.getProperty("live.teams.1.hostname")
print p.getValue()

p2 = p.get("sub")
p2.setValue('v1')
p3 = p.get("sub.sub2")# p2.get("sub2")

class Listener(prop.PropertyListener):
  def propertyChanged(self, prop):
    print "Listener ", prop, "p2", p2.getValue()

def callback(prop):
  print "callback", prop, "p3", p3.getValue()

# Note that listeners and callbacks are called when they are added
p2.addPropertyListener(Listener())
p3.addCallback(callback)

T=.05
time.sleep(T)
# on updates
print 'Set p2 v2'
p2.setValue('v2')
time.sleep(T)

# and now for both the listener and callback
print 'Set p3 v3'
p3.setValue('v3')

time.sleep(T)
print p2.getValue()
print p3.getValue()

A = 100
time.sleep(A)
