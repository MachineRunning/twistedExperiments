from twisted.internet.protocol import Protocol,  ReconnectingClientFactory, Factory
from sys import stdout
import sys
from twisted.internet import reactor
from twisted.internet import stdio
from twisted.application import internet

### https://twistedmatrix.com/documents/current/core/howto/clients.html

# bugjar twisted_proto_client_troubled_backup_from_no_remote_instance.py 192.168.0.107 12777
# twisted_proto_client.py 127.0.0.1 12777

### ah confusion so about Echo...
#class Echo(protocol):
from twisted.protocols import basic

class ChatStateEnum:
    initialState,testUserName,uniqueUserName,closing = range(1, 5)

## stdio.StandardIO(ChatClient(userName))
## this is not created by a factory!
class ChatClient(basic.LineReceiver):
    delimiter = '\n' # unix terminal style newlines. remove this line
                     ## for use with Telnet
    # from os import linesep as delimiter
    # okay needed delimiter!!! wow....
    def __init__(self,username,externalFact):#,externalConnection):
        self.externalProto = externalFact
        
    def connectionMade(self):
        print 'Connected to local console.'
    
    def lineReceived(self, line):
        if not line: 
            self.transport.write("<"+self.externalProto.userName +"> ")
            sys.stdout.flush()
            return ### if the line is blank skip it
        #print('lineReceived')
        if(line=='quit()'): # or line=='quit()\r\n'):
            print('Closing chat client...')
            self.externalProto.state=ChatStateEnum.closing
            self.externalProto.protocolInstance.message(line)
            #self.transport.loseConnection()
        elif(self.externalProto.state==ChatStateEnum.initialState):
            self.externalProto.userName=line
            self.externalProto.protocolInstance.lineReceived(line)
            #self.externalProto.protocolInstance.message(line)
        else:
            #print(self.externalProto.state)
            self.externalProto.protocolInstance.message(line)
            #print(self.externalProto.userName)
            if(self.externalProto.state==ChatStateEnum.uniqueUserName):
                self.transport.write("<"+self.externalProto.userName +"> ")
                sys.stdout.flush()


        
class RemoteTCPprotocol(basic.LineReceiver):
    def __init__(self):
        self.connectCount=0
        #self.linesRecieved=0
        
    def connectionMade(self):
        print('Connected to remote host. Able to begin sending messages.')
    
    def lineReceived(self, line):
        ### if this is the first time a line is rec'd send the username to the 
        ### server
        if(self.factory.state==ChatStateEnum.initialState):
            self.factory.state=ChatStateEnum.testUserName
            self.sendLine(self.factory.userName)
            #self.linesRecieved+=1
        elif(self.factory.state==ChatStateEnum.testUserName and line=="Name taken, please choose another."):
            print(line)
            #print("What is your name? ")
            sys.stdout.write("What is your name? ")
            sys.stdout.flush()
            self.factory.state=ChatStateEnum.initialState
        elif(self.factory.state==ChatStateEnum.testUserName and line[0:7]=="Welcome"):
            self.factory.state=ChatStateEnum.uniqueUserName
            CURSOR_UP_ONE = '\x1b[1A'
            ERASE_LINE = '\x1b[2K'
            print(ERASE_LINE+line)
            sys.stdout.write("<"+self.factory.userName+"> ")
            sys.stdout.flush()
        else:
            #Using ANSI escape sequence, where ESC[y;xH moves curser to row y, col x:
            #print("\033[6;3HHello")
            #self.linesRecieved+=1
            CURSOR_UP_ONE = '\x1b[1A'
            CLEAR_CUR_LINE = '\x1b[2K'
            MOVE_TO_START_OF_LINE='\x1b[0G'
            ## "\x1b[2K" didn't work but "\x1b[1M" 
            #print(CURSOR_UP_ONE + ERASE_LINE)
            print(CLEAR_CUR_LINE +MOVE_TO_START_OF_LINE+line)
            #sys.stdout.flush()
            #print(line)
            #sys.stdout.flush()
            #sys.stdout.write(line)
            #sys.stdout.write(ERASE_LINE+line)
            #http://stackoverflow.com/questions/959215/removing-starting-spaces-in-python
            #print(ERASE_LINE+line.lstrip())
            #print(repr(line))
            sys.stdout.write("<"+self.factory.userName+"> ")
            sys.stdout.flush()


    def message(self, message):
        #if(self.factory.state==ChatStateEnum.badUserName):
            #self.factory.userName=message
        if(self.factory.state==ChatStateEnum.closing):
            print '.... closed.'
            #self.sendLine(message)
            #self.factory.state=ChatStateEnum.closing
            self.transport.loseConnection()
        else:
            #print(repr(message))
            #self.transport.write(message + '\n')
            self.sendLine(message)


### so using stdio.StandardIO seems to prevent me from using my own factory class
### which I was mainly using to force it to reconnect automatically
## The ClientFactory is in charge of creating the Protocol and also receives events relating to the connection state.
## This allows it to do things like reconnect in the event of a connection error.
### hmmm this is (actually) correct, I am supposed to save data within the client factory

#### hmm so inheriting from ClientFactory was the problem...
#### ie class EchoClientFactory(ClientFactory):
#### at least for the chat server problem
#### stdio.StandardIO
class EchoClientFactory(Factory):
    protocol = RemoteTCPprotocol
    
    ## if (self,username)
    ## username will need to be fed as input on EchoClientFactory()
    def __init__(self,username):
        self.userName = username
        self.state=ChatStateEnum.initialState
        self.protocolInstance=None
        
    def startedConnecting(self, connector):
        print 'Started connecting to remote host.'
        
    def buildProtocol(self, address):
        p = RemoteTCPprotocol()
        p.factory = self
        self.protocolInstance=p
        return p


    def clientConnectionLost(self, connector, reason):
        #f = ReconnectingClientFactory()
        #ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
        if(self.state!=ChatStateEnum.closing):
            print 'Lost connection.  Reason:', reason
            ReconnectingClientFactory.retry(ReconnectingClientFactory(), connector)
        else:
            reactor.stop()
        

    ### not sure what conditions this event is thrown versus connection Lost
    ### or if a connection is lost then does connectionFailed get thrown??
    ### if it fails to connect maybe a firewall is to blame don't try reconnecting
    def clientConnectionFailed(self, connector, reason):
        print 'Connection failed. Reason:', reason
        #ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)
        # ReconnectingClientFactory(maxDelay [sec],initialDelay [sec])
        ## maxDelay=360, no this constructor takes no arguments!
        ReconnectingClientFactory.retry(ReconnectingClientFactory(), connector)


if __name__ == "__main__":
     
    if(len(sys.argv) < 3) :
        print 'Usage : python telnet.py hostname port'
        sys.exit()
    
    host = sys.argv[1]
    port = int(sys.argv[2])

    userName = raw_input("What is your name? ")
    #http://stackoverflow.com/questions/14884193/how-to-detect-if-user-has-entered-any-data-as-a-console-input
    
    
    ### order here is important
    inFact=EchoClientFactory(userName)
    #print(dir(inFact.protocol))
    remoteConnection=reactor.connectTCP(host, port, inFact)

    #### okay so this is critical to understand when you call this function
    #### all text events get sent as data to the lineReceived event
    stdio.StandardIO(ChatClient(userName,inFact))
    
    reactor.run()



    






