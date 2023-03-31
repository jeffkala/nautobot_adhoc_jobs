from datetime import datetime

from django.db.models import Q
from nautobot.dcim.filters import DeviceFilterSet
from nautobot.dcim.models import Device
from nautobot.extras.jobs import Job, MultiObjectVar
from nautobot_plugin_nornir.constants import NORNIR_SETTINGS
from nautobot_plugin_nornir.plugins.inventory.nautobot_orm import NautobotORMInventory
from nornir import InitNornir
from nornir.core.plugins.inventory import InventoryPluginRegister

InventoryPluginRegister.register("nautobot-inventory", NautobotORMInventory)


class DebugInventoryJob(Job):
    """Job to debug stuff."""
    devices = MultiObjectVar(model=Device, required=False)

    def run(self, data, commit):  # pylint: disable=too-many-branches
        """Run config compliance report script."""
        # pylint: disable=unused-argument
        query = {}
        query.update({"id": data["devices"].values_list("pk", flat=True)})
        raw_qs = Q()
        base_qs = Device.objects.filter(raw_qs)
        devices_filtered = DeviceFilterSet(data=query, queryset=base_qs)
        try:
            with InitNornir(
                runner=NORNIR_SETTINGS.get("runner"),
                logging={"enabled": False},
                inventory={
                    "plugin": "nautobot-inventory",
                    "options": {
                        "credentials_class": NORNIR_SETTINGS.get("credentials"),
                        "params": NORNIR_SETTINGS.get("inventory_params"),
                        "queryset": devices_filtered.qs,
                        "defaults": {"now": datetime.now()},
                    },
                },
            ) as nornir_obj:
                self.log_info('defaults', nornir_obj.inventory.defaults)
                self.log_info('dict', nornir_obj.inventory.dict())
                self.log_info('groups', nornir_obj.inventory.groups)
                self.log_info('hosts', nornir_obj.inventory.hosts)

        except Exception as err:
            self.log_failure(None, err)
            raise

jobs = [DebugInventoryJob]
