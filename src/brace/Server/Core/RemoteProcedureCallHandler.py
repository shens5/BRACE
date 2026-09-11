from paho.mqtt import client as mqtt
from multiprocessing import Queue

class RemoteProcedureCallHandler():
    def __init__(self, commandTopic: str = None, username: str = None, password: str = None, port: int = 1883):
        self.commandTopic = commandTopic if commandTopic is not None else "remotecommands/command"
        self.mqttHost = 'localhost' # May be changed to an external host in the future.

        self.username = username
        self.password = password
        self.port = port
    
    def onMessage(self, client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
        """
            The callback for when a PUBLISH message is received from the server, which places the command message to be served.
        """
        if msg.topic == self.commandTopic:
            self.multiprocessingQueue.put_nowait(msg.payload)

    # Creates MQTT client and queue for handling online message requests.
    def start(self, multiprocessingQueue: Queue) -> None:
        """
            Starts the asynchronous loop for reading MQTT messages. The relevant messages
            are written to the multiprocessingQueue to be used in RobotAssemblyABC to be executed before
            the next iteration is performed.

            :params multiprocessingQueue: Queue that holds pickled messages of RPC functions to call.
            :type multiprocessingQueue: multiprocessing.Queue
            :return: None
            :rtype: None
        """
        self.multiprocessingQueue = multiprocessingQueue
        self.mqttClient = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqttClient.connect(self.mqttHost, self.port, keepalive = 3600)

        if self.username != None:
            self.mqttClient.username_pw_set(username = self.username, password = self.password)
            
        self.mqttClient.on_message = self.onMessage
        self.mqttClient.subscribe(self.commandTopic)
        
        try:
            self.mqttClient.loop_forever() # This runs on the main thread, therefore ends when signal is passed.
        finally:
            self.mqttClient.disconnect()