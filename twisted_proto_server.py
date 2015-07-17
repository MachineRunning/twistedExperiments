from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
from apscheduler.schedulers.twisted import TwistedScheduler
import socket
#import pprint.pprint
import pprint
##import pdb #python debugger good but command line....

## bugjar twisted_proto_server.py
## needs python-tk package
## needs IDLE (idle-python2.7)


## quite literally chat.py
class Chat(LineReceiver):

    def __init__(self, users,addressDict):
        self.users = users
        self.addressDict=addressDict
        self.name = None
        self.tmpAddress=None
        self.state = "GETNAME"

    def connectionMade(self):
        #pdb.set_trace() python debugger
        
        #test=self.transport
        #pp = pprint.PrettyPrinter(indent=4)
        #pp.pprint(dir(self.transport))
        #pp.pprint(dir(self.transport.getPeer()))

        self.tmpAddress=self.transport.getPeer().host
        print("    "+self.tmpAddress+" connected")
        #addr = self.transport.getPeer().address.host
        self.sendLine("<Server> Retrieving name.")

    def connectionLost(self, reason):
        if self.name in self.users:
            print('    IP Address: '+self.addressDict[self.name]+" Username: " +self.name +" has disconnected")
            del self.users[self.name]
            del self.addressDict[self.name]
            for name, protocol in self.users.iteritems():
                protocol.sendLine(self.name +" has disconnected")

    #def dataReceived

    def lineReceived(self, line):
        #print('    line received')
        if self.state == "GETNAME":
            self.handle_GETNAME(line)
        else:
            self.handle_CHAT(line)
            
    #def rawDataReceived(self, line):
        #if self.state == "GETNAME":
            #self.handle_GETNAME(line)
        #else:
            #self.handle_CHAT(line)

    ### okay so handle_GETNAME isn't working on the python client script
    ### the state is never changing to CHAT
    def handle_GETNAME(self, name):
        #pdb.set_trace()
        if name in self.users:
            self.sendLine("Name taken, please choose another.")
            return
        else:
            #self.sendLine("Welcome, %s!" % (name,))
            self.sendLine("Welcome, %s!" % (name))
            #
            self.name = name
            self.users[name] = self
            self.addressDict[self.name]=self.tmpAddress
            print("    Address {} logged in as {} using TCP".format(self.tmpAddress, name))
            for name, protocol in self.users.iteritems():
                if protocol != self:
                    protocol.sendLine(self.name +" has connected")
            self.state = "CHAT"
            print("    State set equal to chat")

    def handle_CHAT(self, message):
        message = "<%s> %s" % (self.name, message)
        #print("    ....message received "+message)
        for name, protocol in self.users.iteritems():
            if protocol != self:
                #print("    ....message sent")
                protocol.sendLine(message)


class ChatFactory(Factory):

    def __init__(self):
        self.users = {} # maps user names to Chat instances
        self.addressDict = {} # maps user names to ip address strings
        ### so these have to get passed to Chat() in buildProtocol next
        ### then in def __init__ of the Chat class (which inherits from protocol above)
        ### this needs to get set to a protocol attribute 
        
    def buildProtocol(self, addr):
        return Chat(self.users,self.addressDict)

#scheduler = TwistedScheduler()

def statusUpdate():
    print "."

### won't work if using bugjar
#s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#s.connect(("gmail.com",80))
#ipAddress=s.getsockname()[0])
#s.close()

#,interface='127.0.0.2'
reactor.listenTCP(12777, ChatFactory())
#print("Chat server started and running on port "+ipAddress+":12777...")
print("Chat server started and running on port 12777...")

#scheduler.add_job(statusUpdate, 'interval', seconds=60)
#scheduler.start()
reactor.run()
