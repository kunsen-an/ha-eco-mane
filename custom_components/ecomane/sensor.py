"""The Eco Mane Sensor."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    DOMAIN as SENSOR_DOMAIN,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    SENSOR_CIRCUIT_ENERGY_SELECTOR,
    SENSOR_CIRCUIT_ENERGY_SERVICE_TYPE,
    SENSOR_CIRCUIT_POWER_SERVICE_TYPE,
    SENSOR_CIRCUIT_PREFIX,
    SENSOR_CIRCUIT_SELECTOR_CIRCUIT,
    SENSOR_CIRCUIT_SELECTOR_PLACE,
    SENSOR_CIRCUIT_SELECTOR_POWER,
)
from .coordinator import (
    EcoManeCircuitEnergySensorEntityDescription,
    EcoManeCircuitPowerSensorEntityDescription,
    EcoManeDataCoordinator,
    EcoManeUsageSensorEntityDescription,
)
from .name_to_id import ja_to_entity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities from a config entry."""
    # Access data stored in hass.data
    coordinator: EcoManeDataCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    sensor_dict = coordinator.data
    power_sensor_total = coordinator.circuit_total

    ecomane_energy_sensors_descs = coordinator.usage_sensor_descs

    sensors: list[SensorEntity] = []
    _LOGGER.debug("sensor.py async_setup_entry sensors: %s", sensors)
    # 使用量センサーのエンティティのリストを作成
    for usage_sensor_desc in ecomane_energy_sensors_descs:
        sensor = EcoManeUsageSensorEntity(coordinator, usage_sensor_desc)
        sensors.append(sensor)

    # 電力センサーのエンティティのリストを作成
    for sensor_num in range(power_sensor_total):
        prefix = f"{SENSOR_CIRCUIT_PREFIX}_{sensor_num:02d}"
        place = sensor_dict[f"{prefix}_{SENSOR_CIRCUIT_SELECTOR_PLACE}"]
        circuit = sensor_dict[f"{prefix}_{SENSOR_CIRCUIT_SELECTOR_CIRCUIT}"]
        _LOGGER.debug(
            "sensor.py async_setup_entry sensor_num: %s, prefix: %s, place: %s, circuit: %s",
            sensor_num,
            prefix,
            place,
            circuit,
        )
        sensors.append(
            EcoManeCircuitPowerSensorEntity(coordinator, prefix, place, circuit)
        )
        sensors.append(
            EcoManeCircuitEnergySensorEntity(coordinator, prefix, place, circuit)
        )
    # センサーが見つからない場合はエラー
    if not sensors:
        raise ConfigEntryNotReady("No sensors found")

    # エンティティを追加 (update_before_add=False でオーバービューに自動で登録されないようにする)
    async_add_entities(sensors, update_before_add=False)
    _LOGGER.debug("sensor.py async_setup_entry has finished async_add_entities")


class EcoManeUsageSensorEntity(CoordinatorEntity, SensorEntity):
    """EcoMane UsageS ensor."""

    _attr_has_entity_name = True
    # _attr_name = None # Noneでも値を設定するとtranslationがされない
    _attr_unique_id: str | None = None
    _attr_attribution = "Usage data provided by Panasonic ECO Mane HEMS"
    _attr_entity_description: EcoManeUsageSensorEntityDescription | None = None
    _attr_device_class: SensorDeviceClass | None = None
    _attr_state_class: str | None = None
    _attr_native_unit_of_measurement: str | None = None

    _attr_div_id: str = ""
    _attr_description: str | None = None

    _ip_address: str | None = None

    def __init__(
        self,
        coordinator: EcoManeDataCoordinator,
        usage_sensor_desc: EcoManeUsageSensorEntityDescription,
    ) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator=coordinator)

        # ip_address を設定
        self._ip_address = coordinator.ip_address

        # 使用量 sensor_id (_attr_div_id) を設定
        sensor_id = usage_sensor_desc.key
        self._attr_div_id = sensor_id

        # 使用量 entity_description を設定
        self._attr_entity_description = usage_sensor_desc
        self._attr_description = description = usage_sensor_desc.description

        # 使用量 translation_key を設定
        self._attr_translation_key = usage_sensor_desc.translation_key

        # 使用量 entity_id を設定
        self.entity_id = f"{SENSOR_DOMAIN}.{DOMAIN}_{usage_sensor_desc.translation_key}"

        # 使用量 _attr_unique_id を設定
        if (
            coordinator is not None
            and coordinator.config_entry is not None
            and description is not None
        ):
            self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{usage_sensor_desc.translation_key}"

        # 使用量 device_class, state_class, native_unit_of_measurement を設定
        self._attr_device_class = usage_sensor_desc.device_class
        self._attr_state_class = usage_sensor_desc.state_class
        self._attr_native_unit_of_measurement = (
            usage_sensor_desc.native_unit_of_measurement
        )

        # デバッグログ
        _LOGGER.debug(
            "usage_sensor_desc.name: %s, _attr_translation_key: %s, _attr_div_id: %s, entity_id: %s, _attr_unique_id: %s",
            usage_sensor_desc.name,
            self._attr_translation_key,
            self._attr_div_id,
            self.entity_id,
            self._attr_unique_id,
        )

    @property
    def native_value(self) -> str:
        """State."""
        value = self.coordinator.data.get(self._attr_div_id)  # 使用量
        if value is None:
            return ""
        return str(value)

    @property
    def device_info(
        self,
    ) -> DeviceInfo:  # エンティティ群をデバイスに分類するための情報を提供
        """Return the device info."""
        ip_address = self._ip_address
        return DeviceInfo(  # 使用量のデバイス情報
            identifiers={(DOMAIN, "daily_usage_" + (ip_address or ""))},
            name="Daily Usage",
            manufacturer="Panasonic",
            translation_key="daily_usage",
        )


class EcoManeCircuitPowerSensorEntity(CoordinatorEntity, SensorEntity):
    """EcoManePowerSensor."""

    _attr_has_entity_name = True
    # _attr_name = None　# Noneでも値を設定するとtranslationがされない
    _attr_unique_id: str | None = None
    _attr_attribution = "Power data provided by Panasonic ECO Mane HEMS"
    _attr_entity_description: EcoManeCircuitPowerSensorEntityDescription | None = None
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_sensor_id: str

    _ip_address: str | None = None

    def __init__(
        self,
        coordinator: EcoManeDataCoordinator,
        prefix: str,
        place: str,
        circuit: str,
    ) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator=coordinator)

        # ip_address を設定
        self._ip_address = coordinator.ip_address

        # 回路別電力 sensor_id を設定
        sensor_id = f"{prefix}_{SENSOR_CIRCUIT_SELECTOR_POWER}"  # num
        self._attr_sensor_id = sensor_id

        # 回路別電力 entity_description を設定
        self._attr_entity_description = description = (
            EcoManeCircuitPowerSensorEntityDescription(
                service_type=SENSOR_CIRCUIT_POWER_SERVICE_TYPE,
                key=sensor_id,
            )
        )

        # 回路 translation_key を設定
        name = f"{place} {circuit}"
        self._attr_translation_key = ja_to_entity(name)

        # 回路別電力量 entity_id を設定
        self.entity_id = (
            f"{SENSOR_DOMAIN}.{DOMAIN}_{sensor_id}_{self._attr_translation_key}"
        )

        # 回路別電力量 _attr_unique_id を設定
        if (
            coordinator is not None
            and coordinator.config_entry is not None
            and description is not None
        ):
            self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.service_type}_{description.key}"

    @property
    def native_value(self) -> str:
        """State."""
        value = self.coordinator.data.get(self._attr_sensor_id)  # 回路別電力
        if value is None:
            return ""
        return str(value)

    @property
    def device_info(
        self,
    ) -> DeviceInfo:  # エンティティ群をデバイスに分類するための情報を提供
        """Return the device info."""
        ip_address = self._ip_address
        return DeviceInfo(  # 回路別電力のデバイス情報
            identifiers={(DOMAIN, "power_consumption_" + (ip_address or ""))},
            name="Power Consumption",
            manufacturer="Panasonic",
            translation_key="power_consumption",
        )


class EcoManeCircuitEnergySensorEntity(CoordinatorEntity, SensorEntity):
    """EcoManeCircuitEnergySensor."""

    _attr_has_entity_name = True
    # _attr_name = None　# Noneでも値を設定するとtranslationがされない
    _attr_unique_id: str | None = None
    _attr_attribution = "Power data provided by Panasonic ECO Mane HEMS"
    _attr_entity_description: EcoManeCircuitEnergySensorEntityDescription | None = None
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_sensor_id: str

    _ip_address: str | None = None

    def __init__(
        self,
        coordinator: EcoManeDataCoordinator,
        prefix: str,
        place: str,
        circuit: str,
    ) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator=coordinator)

        # ip_address を設定
        self._ip_address = coordinator.ip_address

        # 回路別電力量 sensor_id を設定
        sensor_id = f"{prefix}_{SENSOR_CIRCUIT_ENERGY_SELECTOR}"  # ttx_01
        self._attr_sensor_id = sensor_id

        # 回路別電力量 entity_description を設定
        self._attr_entity_description = description = (
            EcoManeCircuitPowerSensorEntityDescription(
                service_type=SENSOR_CIRCUIT_ENERGY_SERVICE_TYPE,
                key=sensor_id,
            )
        )

        # 回路 translation_key を設定
        name = f"{place} {circuit}"
        self._attr_translation_key = ja_to_entity(name)

        # 回路別電力量 entity_id を設定
        self.entity_id = (
            f"{SENSOR_DOMAIN}.{DOMAIN}_{sensor_id}_{self._attr_translation_key}"
        )

        # 回路別電力量 _attr_unique_id を設定
        if (
            coordinator is not None
            and coordinator.config_entry is not None
            and description is not None
        ):
            self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.service_type}_{description.key}"

    @property
    def native_value(self) -> str:
        """State."""
        value = self.coordinator.data.get(self._attr_sensor_id)  # 回路別電力量
        if value is None:
            return ""
        return str(value)

    @property
    def device_info(
        self,
    ) -> DeviceInfo:  # エンティティ群をデバイスに分類するための情報を提供
        """Return the device info."""
        ip_address = self._ip_address
        return DeviceInfo(  # 回路別電力量のデバイス情報
            identifiers={(DOMAIN, "energy_consumption_" + (ip_address or ""))},
            name="Energy Consumption",
            manufacturer="Panasonic",
            translation_key="energy_consumption",
        )
