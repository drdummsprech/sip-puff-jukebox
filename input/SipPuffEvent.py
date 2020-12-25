from abc import ABC, abstractmethod
from enum import Enum, auto


class SipPuffEvent(Enum):
    """
    Enum for the different inputs the sip/puffg switch can trigger

    These events are mutually exclusive in the sense that a single user interaction should not trigger multiple events.
    If a user sips long and strong, there should neither be a short event emitted when a long event is emitted later
    and there shouldn't be a weak event when a strong one gets emitted.
    """
    SHORT_WEAK_SIP = auto()
    SHORT_STRONG_SIP = auto()
    SHORT_WEAK_PUFF = auto()
    SHORT_STRONG_PUFF = auto()
    LONG_WEAK_SIP = auto()
    LONG_STRONG_SIP = auto()
    LONG_WEAK_PUFF = auto()
    LONG_STRONG_PUFF = auto()

    @staticmethod
    def get_all_puff_events():
        return (
            SipPuffEvent.SHORT_STRONG_PUFF,
            SipPuffEvent.SHORT_WEAK_PUFF,
            SipPuffEvent.LONG_STRONG_PUFF,
            SipPuffEvent.LONG_WEAK_PUFF
        )

    @staticmethod
    def get_all_sip_events():
        return (
            SipPuffEvent.SHORT_STRONG_SIP,
            SipPuffEvent.SHORT_WEAK_SIP,
            SipPuffEvent.LONG_STRONG_SIP,
            SipPuffEvent.LONG_WEAK_SIP
        )


class SipPuffListener(ABC):
    """ Interface for something receiving sip/puff events """

    @abstractmethod
    def handle_sip_puff_event(self, event: SipPuffEvent) -> None:
        pass
