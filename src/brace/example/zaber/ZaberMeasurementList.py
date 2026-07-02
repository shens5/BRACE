from brace.Server.Core.ComInterface import IInputCom
from brace.Server.Core.MeasurementLists import IMeasurementLists
from brace.example.zaber.ZaberInterface import ZaberInterface
from brace.example.zaber.ArduinoADCInterface import LoadCellInterface

from collections import deque
from typing import override

class ZaberMeasurementLists(IMeasurementLists):
    """
        Set of measurement lists that contains the sensor information
        for the mechanosensitive measurement device.    
    """
    MAX_LEN = 15000
    def __init__(self):
        self.positionMesAll: deque[float] = deque(maxlen = ZaberMeasurementLists.MAX_LEN)
        self.loadCellMesAll: deque[float] = deque(maxlen = ZaberMeasurementLists.MAX_LEN)
        self.newPositionDesAll: deque[float] = deque(maxlen = ZaberMeasurementLists.MAX_LEN)
        self.newPositionInAll: deque[float] = deque(maxlen = ZaberMeasurementLists.MAX_LEN)
        self.calibrationOffsetLoadCell = 0.0
        self.voltageCalibration = 0.5512 # Load cell dependent value.
        self.POUNDS_TO_NEWTON = 4.44822
        self.POUNDS_TO_GRAM = 453.592
        self.deque: deque = deque(maxlen=4)

    @override
    def setupMeasurements(self, inputComs: list[IInputCom]) -> None:
        """
            Sets up the initial measurements at the beginning; avoids off-by-one error issues.

            :param inputComs: The input communications interfaces used in this device.
            :type inputComs: list[IInputComs]
            :return: None
            :rtype: None
        """
        # Run first measurement
        positionMes, loadCellMes = self.readMeasurements(inputComs)
        self.positionMesAll.append(positionMes)
        self.loadCellMesAll.append(loadCellMes)

        # Placeholder values for position.
        self.newPositionDesAll.append(0.0)
        self.newPositionInAll.append(0.0)

    @override
    def setCalibrationOffset(self, inputComs: list[IInputCom]) -> None:
        """
            Sets a calibration value based on the current loadcell voltage that is measured at the instantaneous point
            in time.

            :param inputComs: The input communications interfaces used in this device.
            :type inputComs: list[IInputComs]
            :return: None
            :rtype: None
        """
        _, self.calibrationOffsetLoadCell = self.readMeasurements(inputComs)

    def readMeasurements(self, inputComs: list[IInputCom]) -> tuple[float, float]:
        """
            Reads the measurements from the list of input communications; getting
            the current actuator position from the Zaber actuator and the 
            load cell value from the Arduino.
            
            :param inputComs: The input communications interfaces used in this device.
            :type inputComs: list[IInputComs]
            :return: Tuple of values containing the current position and the load cell voltage.
            :rtype: tuple[float, float]
        """
        posMes = 0
        loadCellMes = 0
        zaberCom = inputComs[0]
        loadcellCom = inputComs[1]
        if zaberCom.isComOn() and isinstance(zaberCom, ZaberInterface):
            posMes = zaberCom.printPosition()
        
        if loadcellCom.isComOn() and isinstance(loadcellCom, LoadCellInterface):
            loadCellMes = loadcellCom.printLoadCellValue()[0] - self.calibrationOffsetLoadCell
        return posMes, loadCellMes

    @override
    def runMeasurements(self, deltaTimeAll: list[float], inputComs: list[IInputCom]) -> None:
        """
            Gets the measurement, appends the values to the appropriate lists,
            also converts the load cell values to proper gram-force measurements.

            :param deltaTimeAll: The list of times in between iteration cycles.
            :type deltaTimeAll: list[float]
            :param inputComs: The input communications interfaces used in this device.
            :type inputComs: list[IInputComs]
            :return: None
            :rtype: None
        """
        #read encoders (position and loadcell) and append data to vectors
        positionMes, loadCellMes = self.readMeasurements(inputComs)
        self.positionMesAll.append(positionMes)
        
        gramsMeasurement = self.voltageCalibration * loadCellMes * self.POUNDS_TO_GRAM # to grams
        self.loadCellMesAll.append(gramsMeasurement)

    def recordOutputValues(self, outputDes: list[float], outputIn: list[float]) -> None:
        """
            Gets the output position values and stores them into the lists.

            :param outputDes: The output position before any safety checks to be recorded.
            :type outputDes: list[float]
            :param outputIn: The output position after safety checks to be recorded.
            :type outputIn: list[float]
            :return: None
            :rtype: None
        """
        [positionDes] = outputDes
        self.newPositionDesAll.append(positionDes)
        [positionIn] = outputIn
        self.newPositionInAll.append(positionIn)

    def getPosMeasurements(self) -> deque[float]:
        """
            Gets the position measurements from this deque. Measurements are rotated out after maximum capacity is hit.
            
            :return: The position measurements from a deque.
            :rtype: collections.deque[float]
        """
        return self.positionMesAll
    
    def getLoadCellMeasurements(self) -> deque[float]:
        """
            Gets the Load cell measurements from this deque. Measurements are rotated out after maximum capacity is hit.
            
            :return: The load cell measurements (gf) from a deque.
            :rtype: collections.deque[float]
        """
        return self.loadCellMesAll