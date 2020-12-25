import time
from enum import Enum, auto
from typing import Optional

from input import IPressureSensor
from input.SingleSensorReferenceFilter import SingleSensorReferenceFilter
from input.SipPuffEvent import SipPuffEvent, SipPuffListener


class InputState(Enum):
    """ Internal class for the sip-puff state machine"""
    IDLE = auto()
    MEASURING = auto()
    FINISHED_WAITING = auto()


class PressureInput:
    """
    Turns readings from a pressure sensor into Sip-Puff input events

    Attributes:
        debug               Flag to set for some debugging output

        short_action_min_time       Minimum duration for a short input event in seconds
        long_Action_min_time        Minimum duration for a long input event in seconds

        weak_action_thresh          Minimum pressure differential in Pascal to consider the input weak instead of idle
        weak_action_hysteresis      Hysteresis around the weak action threshold in Pascal
        strong_action_thresh        Same as the weak one, but for the step from weak to strong input
        strong_action_hysteresis    See above
    """

    __pressure_sensor: IPressureSensor  # Sensor to detect puffing and sipping
    __reference_pressure_filter = SingleSensorReferenceFilter()  # Filter for estimating the ambient pressure
    __current_state: InputState = InputState.IDLE
    __action_start_time: Optional[float] = None  # Internal bookkeeping, start of the current action
    __action_pressure_history: [float] = []  # History of pressure values during the current action

    debug: bool = False

    short_action_min_time: float = 0.2
    long_Action_min_time: float = 1.0

    weak_action_thresh: float = 400
    weak_action_hysteresis: float = 10

    strong_action_thresh: float = 700
    strong_action_hysteresis: float = 30

    __listeners: [SipPuffListener] = []

    def __init__(self, sensor: IPressureSensor):
        self.__pressure_sensor = sensor

    def __notify_listeners(self, event: SipPuffEvent):
        if self.debug:
            print("Notifying listeners of event: " + event.__str__())
        for listener in self.__listeners:
            listener.handle_sip_puff_event(event)

    def register_listener(self, listener: SipPuffListener):
        self.__listeners.append(listener)

    def update(self):
        """
        Takes a reading from the underlying sensor and processes it.
        This should be called in a loop externally.
        :return: None, A side effect of this method might be the emission of a :class:SipPuffEvent to listeners
        """
        sensor_value = self.__pressure_sensor.get_pressure_in_Pascal()
        self.__reference_pressure_filter.update(sensor_value)

        reference_value = self.__reference_pressure_filter.get_ambient_pressure_estimation()
        pdiff = sensor_value - reference_value

        if self.debug:
            print("Reference value: " + str(reference_value))
            print("Sensor value: " + str(sensor_value))
            print("Pressure difference: " + str(pdiff))

        if self.__current_state == InputState.IDLE:
            self.__update_IDLE(pdiff)
        elif self.__current_state == InputState.MEASURING:
            self.__update_MEASURING(pdiff)
        elif self.__current_state == InputState.FINISHED_WAITING:
            self.__update_FINISHED_WAITING(pdiff)
        else:
            raise Exception("Untreated enum value for input state: " + self.__current_state.__str__())

    def get_current_duration(self) -> Optional[float]:
        if self.__action_start_time is None:
            return None
        else:
            return time.perf_counter() - self.__action_start_time

    def __get_action_avg_pressure(self) -> float:
        if len(self.__action_pressure_history) < 1:
            return 0
        else:
            return sum(self.__action_pressure_history) / len(self.__action_pressure_history)

    def __update_IDLE(self, pdiff):
        # clear bookkeeping
        self.__action_start_time = None
        self.__action_pressure_history.clear()

        # Ignore no sipping or puffing
        if abs(pdiff) < self.weak_action_thresh:
            return

        if self.debug:
            print("Changing mode from to measuring for next cycle")

        # Start the timer and add the observation
        self.__action_start_time = time.perf_counter()
        self.__action_pressure_history.append(pdiff)

        # Change state to Measuring
        self.__current_state = InputState.MEASURING

    def __update_MEASURING(self, pdiff):
        # Check if we are past the duration for a long event
        if self.get_current_duration() > self.long_Action_min_time:
            self.__current_state = InputState.FINISHED_WAITING
            if self.debug:
                print("Changing mode to waiting for next cycle")

            avg_pressure = self.__get_action_avg_pressure()

            # Order matters here. Match the extreme conditions first!
            if avg_pressure < -self.strong_action_thresh:
                self.__notify_listeners(SipPuffEvent.LONG_STRONG_SIP)
            elif avg_pressure > self.strong_action_thresh:
                self.__notify_listeners(SipPuffEvent.LONG_STRONG_PUFF)
            elif avg_pressure < -self.weak_action_thresh:
                self.__notify_listeners(SipPuffEvent.LONG_WEAK_SIP)
            elif avg_pressure > self.weak_action_thresh:
                self.__notify_listeners(SipPuffEvent.LONG_WEAK_PUFF)
            else:
                pass

            return

        # If we slip below the hysteresis around 0, the action is over
        if abs(pdiff) < self.weak_action_thresh - self.weak_action_hysteresis:
            self.__current_state = InputState.IDLE

            # Have we cleared the minimum time for an action?
            if self.get_current_duration() < self.short_action_min_time:
                return

            avg_pressure = self.__get_action_avg_pressure()
            if avg_pressure < -self.strong_action_thresh:
                self.__notify_listeners(SipPuffEvent.SHORT_STRONG_SIP)
            elif avg_pressure > self.strong_action_thresh:
                self.__notify_listeners(SipPuffEvent.SHORT_STRONG_PUFF)
            elif avg_pressure < -self.weak_action_thresh:
                self.__notify_listeners(SipPuffEvent.SHORT_WEAK_SIP)
            elif avg_pressure > self.weak_action_thresh:
                self.__notify_listeners(SipPuffEvent.SHORT_WEAK_PUFF)
            else:
                pass

            return

        # Append measurement at the end if we do not stop
        # We want to ignore the measurement that's falling below the threshold
        self.__action_pressure_history.append(pdiff)

    def __update_FINISHED_WAITING(self, pdiff):
        # This state is for waiting out the time after a long input
        # without triggering a new one
        if abs(pdiff) < self.weak_action_thresh - self.weak_action_hysteresis:
            self.__current_state = InputState.IDLE
            if self.debug:
                print("Changing mode to idle for next cycle")
