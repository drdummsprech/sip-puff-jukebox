from input.SipPuffEvent import SipPuffEvent, SipPuffListener


class SipPuffEventPrinter(SipPuffListener):
    def handle_sip_puff_event(self, event: SipPuffEvent) -> None:
        print("Received event: " + event.__str__())
