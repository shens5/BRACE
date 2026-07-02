from gpiozero import Button
import time
from typing import Any, NamedTuple
from brace.RealTimeGraphing.Graphing.IDataProducer import IDataProducer
from multiprocessing import Event
from multiprocessing.synchronize import Condition
from multiprocessing.sharedctypes import Synchronized
from paho.mqtt import client as mqtt
import pickle

import logging
logger = logging.getLogger("logger")
class Trigger(NamedTuple):
    """
        NamedTuple data object that describes a trigger state (0 when not pressed, 1 when pressed).
    """
    triggerState: bool
    t: float

class ButtonPress(IDataProducer):
    """
        IDataProducer class that continually checks a pin for whether or not it is pressed to determine the synchronization
        state. The default topic to use is "trigger" which sends out a message which can be used for event driven
        actions (such as displaying text when the trigger is pressed).
    """
    TRIGGER_TOPIC = "trigger"
    def __init__(self, buttonPin: int, UPDATE_RATE_PER_SECOND: int, startTime: Synchronized = None, 
                 triggerTopicName: str = None, dataTopicName: str = None):
        
        """
            :param buttonPin: The GPIO pin that should be used as input.
            :type buttonPin: int
            :param UPDATE_RATE_PER_SECOND: The number of times that this should update when in use.
            :type UPDATE_RATE_PER_SECOND: int
            :param startTime: Start time value that is synchronized between IDataProducer objects.\
            Should be None if considered the primary (which should start the time) and the synchronized Value object otherwise.
            :type multiprocessing.Value (float)
            :param triggerTopicName: Separate MQTT topic for event triggering when button is pressed. No parameter \
            leaves this value at default "trigger".
            :type triggerTopicName: str
            :param dataTopicName: Name of the MQTT data topic where data should be sent. No parameter \
            leaves this value at the default value.
            :type dataTopicName: str
        """
        if triggerTopicName is not None:
            ButtonPress.TRIGGER_TOPIC = triggerTopicName

        if dataTopicName is not None:
            IDataProducer.DATA_TOPIC = dataTopicName

        self.buttonPin = buttonPin
        self.exit = Event()
        self.sendData = Event()

        # Keep-alive = 0 means no attempt to check for pings. If this doesn't work, just set keep-alive to a large number
        self.mqttClient = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqttClient.connect("localhost", 8080, keepalive = 0)

        self.queuedDataElements = []
        self.maxQueueElements = 6 # Max number of elements that should be stored before publishing.
        super().__init__(UPDATE_RATE_PER_SECOND, 0, startTime)
        
    def resetAllState(self) -> None:
        """
            Resets the multiprocessing Events of this object.

            :return: None
            :type: None
        """
        self.exit.clear()
        self.sendData.clear()

    def onTrigger(self) -> None:
        """
            Callback function defined to publish message to the TRIGGER_TOPIC for event driven code.

            :return: None
            :rtype: None
        """
        self.mqttClient.publish(ButtonPress.TRIGGER_TOPIC, True)

    def stopProcess(self) -> None:
        """
            Stops the process by setting the event flag.

            :return: None
            :rtype: None
        """
        self.exit.set()

    def startSend(self) -> None:
        """
            Starts sending data by setting the event flag.

            :return: None
            :rtype: None
        """
        self.sendData.set()

    def stopSend(self) -> None:
        """
            Stops sending data by clearing the event flag.

            :return: None
            :rtype: None
        """
        self.sendData.clear()

    def publishDataToMqtt(self, force: bool = False) -> None:
        """
            Sends messages to the MQTT IDataProducer topic. Messages are buffered and sent when the max number of
            elements is reached. It can also be forced with a parameter.

            :param force: An boolean parameter to force the element to be published to the MQTT topic without reaching the target elements.
            :type force: bool
            :return: None
            :rtype: None
        """
        # Messages are batched, otherwise it seems to affect CAN writes due to apparent overloaded socket spillover.
        # Send when the number of elements is met, or if it was reset in the middle (before elements have been made).
        if force or (len(self.queuedDataElements) == self.maxQueueElements) or (len(self.queuedDataElements) < self.maxQueueElements and not self.sendData.is_set()):
            publishMessage = self.mqttClient.publish(IDataProducer.DATA_TOPIC, pickle.dumps(self.queuedDataElements))
            publishMessage.wait_for_publish()
            self.queuedDataElements.clear()

    def start(self, timeSynchronizationCondition: Condition = None, **kwargs: dict[str, Any]) -> None:
        """
            Starts the process loop by initializing a button under pulldown position with a bounce time of 0.1 ms.
            Data is sent out when the target number of elements is reached and when the sendData Event is set.

            :param timeSynchronizationCondition: A Condition that is shared to stop the Event from running until \
            the primary IDataProducer initializes the shared start time. Default: None
            :type timeSynchronizationCondition: multiprocessing.Condition
            :param kwargs: Keyword arguments (unused).
            :type kwargs: dict[str, Any]
            :return: None
            :rtype: None
        """
        button = Button(pin = self.buttonPin, pull_up = False, bounce_time = 0.0001)
        button.when_activated = self.onTrigger

        updateStartTime = time.perf_counter()
        self.setSharedStartTime(updateStartTime, timeSynchronizationCondition)

        try:
            while not self.exit.is_set():
                currentTime = time.perf_counter()
                nextUpdateTime = currentTime + self.UPDATE_TIME
                button.wait_for_active(self.UPDATE_TIME)

                if self.sendData.is_set(): # This needs to be the more precise timer though.
                    buttonData = Trigger(triggerState = bool(button.value), t = time.perf_counter() - self.startTime.value)
                    self.queuedDataElements.append(buttonData)
                    self.publishDataToMqtt()
                elif len(self.queuedDataElements) > 0: # Clear the elements if not set to prevent leakage onto next session.
                    self.queuedDataElements.clear()

                sleepTime = nextUpdateTime - time.perf_counter()
                if sleepTime > 0:
                    time.sleep(sleepTime)
        finally:
            self.mqttClient.disconnect()
            button.close()