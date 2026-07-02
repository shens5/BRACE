from abc import ABC, abstractmethod
from multiprocessing import Value
from multiprocessing.synchronize import Condition
from multiprocessing.sharedctypes import Synchronized

class IDataProducer(ABC):
    """
        A class for data producers that run on an update rate that create NamedTuple
        datapoints. These are generally then read in by the AnimatedGraphManager.
        These datapoints can be synchronized in time with a shared start time.
    """
    DATA_TOPIC = "datatypes"
    
    def __init__(self, UPDATE_RATE_PER_SECOND: int, TRIAL_TIME: float = 0, startTime: Synchronized = None):
        """
            :param UPDATE_RATE_PER_SECOND: The number of times this data producer class should run per second.
            :type UPDATE_RATE_PER_SECOND: int
            :param TRIAL_TIME: How long the trial is intended to take. Deprecated.
            :type TRIAL_TIME: float
            :param startTime: A multiprocessing double floating point Value type. If the startTime is None, then
                this initializing IDataProducer is considered the primary starting IDataProducer that other
                secondary IDataProducers should share the startTime from. All secondary IDataProducers should
                pass in the primary startTime.
            :type startTime: multiprocessing.Value
        """
        self.UPDATE_TIME = 1 / UPDATE_RATE_PER_SECOND
        self.TRIAL_TIME = TRIAL_TIME
        if startTime:
            self.startTime = startTime
        else:
            self.startTime = Value('d')
        self._createdStartTime = startTime == None # if it didn't exist, this function is responsible for its own startTime 

    def getSharedStartTime(self) -> Synchronized:
        """
            Gets the shared startTime for this IDataProducer. This should be used to get the primary IDataProducer
            startTime that should be shared for all the secondaries.

            :return: The shared start time that should be shared between the IDataProducers.
            :rtype: multiprocessing.Value
        """
        return self.startTime
    
    def setSharedStartTime(self, updateStartTime: float, timeSynchronizationCondition: Condition = None) -> None:
        """ 
            This should be started in the running loop of each IDataProducer. 
            Sets the startTime value only if this startTime is the primary to synchronize
            the startTime values. If it is the secondary datastream, then it will pause execution until
            the synchronized time is set from the primary.

            :param updateStartTime: A double-precision floating point number representing
                the start time before the while loop. This value is used to synchronize startTime
                in multiple processes to achieve more accurate timing.
            :type updateStartTime: float
            :param timeSynchronizationCondition: Multiprocessing condition that pauses execution of the subprocess
                until the primary sets up the startTime.
            :type timeSynchronizationCondition: multiprocessing.synchronize.Condition
            :return: None
            :rtype: None
        """
        if timeSynchronizationCondition:
            if self._createdStartTime:
                # Prevent multiple processes from changing at same time.
                with timeSynchronizationCondition:
                    self.startTime.value = updateStartTime
                    timeSynchronizationCondition.notify_all()
            elif self.startTime.value == 0: # The start time is not ready yet.
                with timeSynchronizationCondition:
                    timeSynchronizationCondition.wait()
        else:
            self.startTime.value = updateStartTime # Without condition, just independently handle time.
                    
    @abstractmethod
    # Synchronized[float] is currently not accepted. See future version.
    def start(self, timeSynchronizationCondition: Condition = None, **kwargs) -> None:
        """ 
            Main update function that runs through data logic and produces output data. Output data in the form of a NamedTuple is
            added into a shared queue between producer and consumer.

            :param timeSynchronizationCondition: Condition that pauses secondaries flow until the time is set by a primary.
            :type timeSynchronizationCondition: multiprocessing.synchronize.Condition
            :param kwargs: Keyword arguments that should be passed in for all other IDataProducers implementing this function.
            :type kwargs: dict[str, Any]
            :return: None
            :rtype: None
        """
        pass