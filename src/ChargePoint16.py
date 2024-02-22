from datetime import datetime
from ocpp.routing import on
from ocpp.v16 import ChargePoint as cp
from ocpp.v16 import call
from ocpp.v16 import call_result
from ocpp.v16.enums import Action, RegistrationStatus, AuthorizationStatus
from ocpp.v16.datatypes import IdTagInfo, MeterValue
from csms_backend import proc_message, get_idtags_status, create_transaction, update_meter_value, stop_transaction, update_charger_status


class ChargePoint(cp):
    """ChargePoint."""


    # ChargePoint에 정의된 function을 재정의하여 추가로 메시지를 저장하도록 처리
    async def route_message(self, raw_msg):
        await super().route_message(raw_msg)
        crgr_id = self.id.split('/')[-1]
        print(f"ChargePoint {crgr_id} : {raw_msg}")
        proc_message(crgr_id, raw_msg)

        """
        CSMS -> Charger Test Code
        """

    @on(Action.GetConfiguration)
    def on_get_configuration(self, **kwargs):

        return call_result.GetConfigurationPayload(
            status=RegistrationStatus.accepted,
        )



    # async def send_get_configuration(self):
    #     request = call.GetConfigurationPayload(
    #         key=["AuthorizationRemoteTxRequests"]
    #     )
    #
    #     response = await self.call(request)
    #
    #     if response.status == RegistrationStatus.accepted:
    #         print("Sent to charger")

    @on(Action.BootNotification)
    def on_boot_notification(
        self, charge_point_vendor: str, charge_point_model: str, **kwargs
    ):
        """on_boot_notification.

        :param charge_point_vendor:
        :type charge_point_vendor: str
        :param charge_point_model:
        :type charge_point_model: str
        :param kwargs:
        """
        return call_result.BootNotificationPayload(
            current_time=datetime.utcnow().isoformat(),
            interval=10,
            status=RegistrationStatus.accepted,
        )

    @on(Action.StatusNotification)
    def on_status_notification(
        self, connector_id: int, error_code:str, status: str, **kwargs
    ):
        """on_status_notification.

        :param connector_id:
        :type connector_id: int
        :param error_code:
        :type error_code: str
        :param status:
        :type status: str
        :param kwargs:
        """
        update_charger_status(self.id, connector_id, status, error_code)
        return call_result.StatusNotificationPayload(
        )

    @on(Action.Heartbeat)
    def on_heartbeat(
        self, **kwargs
    ):
        return call_result.HeartbeatPayload(
            current_time=datetime.utcnow().isoformat()
        )

    @on(Action.Authorize)
    def on_authorize(
        self, id_tag: str, **kwargs
    ):
        """on_authorize.

        :param id_tag:
        :type id_tag: str
        :param kwargs:
        """

        return call_result.AuthorizePayload(
            id_tag_info = IdTagInfo(
                status= get_idtags_status(id_tag, self.id),
                parent_id_tag = None,
                expiry_date = datetime.utcnow().isoformat()
            )
        )

    @on(Action.StartTransaction)
    def on_start_transaction(
        self, id_tag: str, meter_start:int, connector_id:int, **kwargs
    ):
        """
        TODO: Implement db_save transaction
        :param id_tag:
        :param kwargs:
        :return:
        """

        transaction_id = create_transaction(self.id, connector_id, id_tag, meter_start)

        return call_result.StartTransactionPayload(

            transaction_id= transaction_id,
            id_tag_info = IdTagInfo(
                status= get_idtags_status(id_tag, self.id),
                parent_id_tag = None,
                expiry_date = datetime.utcnow().isoformat()
            )
        )

    @on(Action.MeterValues)
    def on_meter_values(
        self, connector_id: int, transaction_id:int, meter_value:MeterValue, **kwargs
    ):
        """on_meter_values.

        :param connector_id:
        :type connector_id: int
        :param transaction_id:
        :type transaction_id: int
        :param meter_value:
        :type meter_value: MeterValue
        :param kwargs:
        """

        meters = meter_value[0]['sampled_value']
        meter = 0
        for m in meters:
            if m.get('measurand') == 'Energy.Active.Import.Register' :
                meter = m.get('value', 0)

        update_meter_value(self.id, connector_id, transaction_id, meter)
        return call_result.MeterValuesPayload(
        )


    @on(Action.StopTransaction)
    def on_stop_transaction(
        self, transaction_id:int, timestamp:str, meter_stop: int, **kwargs
    ):
        """on_stop_transaction.

        :param transaction_id:
        :type transaction_id: int
        :param timestamp:
        :type timestamp: str
        :param meter_stop:
        :type meter_stop: int
        :param kwargs:
        """
        id_status = True
        status = AuthorizationStatus.accepted if id_status is True else AuthorizationStatus.blocked
        stop_transaction(self.id, transaction_id, meter_stop)

        return call_result.StopTransactionPayload(
            id_tag_info=IdTagInfo(
                status=status,
                parent_id_tag=None,
                expiry_date=datetime.utcnow().isoformat()
            )
        )
