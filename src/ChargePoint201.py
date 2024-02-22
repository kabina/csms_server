from datetime import datetime
from ocpp.routing import on
from ocpp.v201 import ChargePoint as cp
from ocpp.v201 import call_result
from csms_backend import proc_message, get_idtags_status, create_transaction, update_meter_value, stop_transaction, update_charger_status

class ChargePoint(cp):
    """ChargePoint."""

    @on("BootNotification")
    def on_boot_notification(self, charging_station, reason, **kwargs):
        """on_boot_notification.

        :param charging_station:
        :param reason:
        :param kwargs:
        """
        return call_result.BootNotificationPayload(
            current_time=datetime.utcnow().isoformat(), interval=10, status="Accepted"
        )

    @on("Heartbeat")
    def on_heartbeat(self):
        print("Got a Heartbeat!")
        return call_result.HeartbeatPayload(
            current_time=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S") + "Z"
        )
