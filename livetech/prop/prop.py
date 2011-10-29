import threading, Queue

class IProperty(object):
    def isSet(self): pass
    def getName(self): pass
    def getValue(self): pass
    def getOwnValue(self): pass
    def setValue(self, value): pass
    def clearValue(self): pass
    def isLinked(self): pass
    def getLink(self): pass
    def setLink(self, link): pass
    def clearLink(self): pass
    def addPropertyListener(self, listener): pass
    def removePropertyListener(self, listener): pass
    def addCallback(self, callback): pass
    def removeCallback(self, callback): pass
    def get(self, sub): pass

    # utility conversions
    def getIntValue(self):
        try:
            return int(self.getValue() or '')
        except ValueError, e:
            return 0
    def getDoubleValue(self):
        try:
            return float(self.getValue() or '')
        except ValueError, e:
            return 0.0
    def getListValue(self, type=str):
        try:
            return map(type, self.getValue().split(','))
        except ValueError, e:
            return []

class RedisProperty(IProperty):
    def __init__(self, redis_client, hierarchy, property_name):
        self.client = redis_client
        self.hierarchy = hierarchy
        self.name = property_name
    def __str__(self):
        return 'RedisProperty("' + self.name + '")'
    def getName(self):
        return self.name
    def isSet(self):
        return self.getOwnValue() is not None
    def getValue(self):
        # TODO: links
        return self.getOwnValue()
    def getOwnValue(self):
        #print 'self.client.get(' + str(self.getName()) + '/' + self.name + '):' + str(self.client.get(self.name))
        return self.client.get(self.name)
    def setValue(self, value):
        self.client.set(self.name, value)
        self._publish()
    def isLinked(self):
        return self.getLink() is not None
    def getLink(self):
        return self.client.get(self.name + '#link')
    def setLink(self, link):
        self.client.set(self.name + '#link', link)
        self._publish()
    def _publish(self):
        message = self.name
        self.client.publish('property', message)
    def addPropertyListener(self, listener):
        self.hierarchy.addPropertyListener(self.name, listener)
    def removePropertyListener(self, listener):
        self.hierarchy.removePropertyListener(self.name, listener)
    def addCallback(self, callback):
        self.hierarchy.addCallback(self.name, callback)
    def removeCallback(self, callback):
        self.hierarchy.removeCallback(self.name, callback)
    def get(self, sub):
        return self.hierarchy.getProperty(self.name + '.' + sub)

class PropertyListener(object):
    def propertyChanged(self, property): pass

class RedisPropertyHierarchy(object):
    def __init__(self, redis_client):
        self.client = redis_client
        self.pipe = self.client.pipeline()
        self.listeners = {} # name: set(listener)
        self.q = Queue.Queue()
        self.listenThread().start()
        self.dispatchThread().start()
    def getProperty(self, name):
        return RedisProperty(self.client, self, name)
    # TODO: support names for listeners here
    def addPropertyListener(self, name, listener):
        if name not in self.listeners:
            self.listeners[name] = set()
        self.listeners[name].add(listener)
        self._notify(listener, self.getProperty(name))
    def removePropertyListener(self, name, listener):
        if name in self.listeners:
            self.listeners[name].discard(listener)
            if not self.listeners[name]:
                del self.listeners[name]
    def addCallback(self, name, callback):
        self.addPropertyListener(name, callback)
    def removeCallback(self, name, callback):
        self.removePropertyListener(name, callback)
    def listenThread(self):
        class ListenThread(threading.Thread):
            def __init__(self):
                threading.Thread.__init__(self)
                self.daemon = True
            def run(self2):
                self.client.subscribe('property')
                for event in self.client.listen():
                    #print 'Event', event, '!!'
                    if event['type'] == 'message':
                        if event['channel'] == 'property':
                            message = event['data']
                            property_name = str(message.split('#')[0])

                            self.q.put(property_name)
        return ListenThread()
    def dispatchThread(self):
        class DispatchThread(threading.Thread):
            def __init__(self):
                threading.Thread.__init__(self)
                self.daemon = True
            def run(self2):
                while True:
                    property_name = self.q.get()
                    prop = self.getProperty(property_name)
                    for listener_interest, listeners in self.listeners.items():
                        if property_name.startswith(listener_interest):
                            for listener in listeners:
                                self._notify(listener, prop)
        return DispatchThread()
    def _notify(self, listener, prop):
        if isinstance(listener, PropertyListener):
            listener.propertyChanged(prop)
        else:
            callback = listener
            callback(prop)

