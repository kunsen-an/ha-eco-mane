"""Coordinator for Eco Mane HEMS component."""

import asyncio
from collections.abc import Generator
from dataclasses import dataclass
from datetime import timedelta
import logging

import aiohttp
from bs4 import BeautifulSoup, NavigableString
from bs4.element import Tag

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy, UnitOfMass, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    ENTITY_NAME,
    KEY_IP_ADDRESS,
    POLLING_INTERVAL,
    RETRY_INTERVAL,
    SENSOR_CIRCUIT_CGI,
    SENSOR_CIRCUIT_ENERGY_CGI,
    SENSOR_CIRCUIT_ENERGY_SELECTOR,
    SENSOR_CIRCUIT_PREFIX,
    SENSOR_CIRCUIT_SELECTOR_BUTTON,
    SENSOR_CIRCUIT_SELECTOR_CIRCUIT,
    SENSOR_CIRCUIT_SELECTOR_PLACE,
    SENSOR_CIRCUIT_SELECTOR_POWER,
    SENSOR_CIRCUIT_SELECTOR_PREFIX,
    SENSOR_TODAY_CGI,
)

_LOGGER = logging.getLogger(__name__)


# 電力センサーのエンティティのディスクリプション
@dataclass(frozen=True, kw_only=True)
class EcoManeCircuitPowerSensorEntityDescription(SensorEntityDescription):
    """Describes EcoManeCirucuitPower sensor entity."""

    service_type: str


# 電力量センサーのエンティティのディスクリプション
@dataclass(frozen=True, kw_only=True)
class EcoManeCircuitEnergySensorEntityDescription(SensorEntityDescription):
    """Describes EcoManeCircuitEnergy sensor entity."""

    service_type: str


# 使用量センサーのエンティティのディスクリプション
@dataclass(frozen=True, kw_only=True)
class EcoManeUsageSensorEntityDescription(SensorEntityDescription):
    """Describes EcoManeUsage sensor entity."""

    description: str


# 使用量センサーのエンティティのディスクリプションのリストを作成
ecomane_usage_sensors_descs = [
    EcoManeUsageSensorEntityDescription(
        name="electricity_purchased",
        translation_key="electricity_purchased",
        description="Electricity purchased 購入電気量",
        key="num_L1",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    EcoManeUsageSensorEntityDescription(
        name="solar_power_energy",
        translation_key="solar_power_energy",
        description="Solar Power Energy / 太陽光発電量",
        key="num_L2",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    EcoManeUsageSensorEntityDescription(
        name="gas_consumption",
        translation_key="gas_consumption",
        description="Gas Consumption / ガス消費量",
        key="num_L4",
        device_class=SensorDeviceClass.GAS,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    EcoManeUsageSensorEntityDescription(
        name="water_consumption",
        translation_key="water_consumption",
        description="Water Consumption / 水消費量",
        key="num_L5",
        device_class=SensorDeviceClass.WATER,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    EcoManeUsageSensorEntityDescription(
        name="co2_emissions",
        translation_key="co2_emissions",
        description="CO2 Emissions / CO2排出量",
        key="num_R1",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    EcoManeUsageSensorEntityDescription(
        name="co2_reduction",
        translation_key="co2_reduction",
        description="CO2 Reduction / CO2削減量",
        key="num_R2",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    EcoManeUsageSensorEntityDescription(
        name="electricity_sales",
        translation_key="electricity_sales",
        description="Electricity sales / 売電量",
        key="num_R3",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
]


class EcoManeDataCoordinator(DataUpdateCoordinator):
    """EcoMane Data coordinator."""

    _attr_circuit_total: int  # 総回路数
    _attr_usage_sensor_descs: list[EcoManeUsageSensorEntityDescription]
    _data_dict: dict[str, str]

    def __init__(self, hass: HomeAssistant, ip_address: str) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=ENTITY_NAME,
            update_interval=timedelta(
                seconds=POLLING_INTERVAL
            ),  # data polling interval
        )

        self._data_dict = {KEY_IP_ADDRESS: ip_address}
        self._session = None
        self._circuit_count = 0
        self._ip_address = ip_address

        self._attr_circuit_total = 0
        self._attr_usage_sensor_descs = ecomane_usage_sensors_descs

    def natural_number_generator(self) -> Generator:
        """Natural number generator."""
        count = 1
        while True:
            yield count
            count += 1

    async def _async_update_data(self) -> dict[str, str]:
        """Update Eco Mane Data."""
        _LOGGER.debug("_async_update_data: Updating EcoMane data")  # debug
        await self.update_usage_data()
        await self.update_circuit_power_data()
        return self._data_dict

    async def update_usage_data(self) -> None:
        """Update usage data."""
        _LOGGER.debug("update_usage_data")
        try:
            # デバイスからデータを取得
            url = f"http://{self._ip_address}/{SENSOR_TODAY_CGI}"
            async with aiohttp.ClientSession() as session:
                response: aiohttp.ClientResponse = await session.get(url)
                if response.status != 200:
                    _LOGGER.error(
                        "Error fetching data from %s. Status code: %s",
                        url,
                        response.status,
                    )
                    raise UpdateFailed(
                        f"Error fetching data from {url}. Status code: {response.status}"
                    )
                # テキストデータを取得する際にエンコーディングを指定
                text_data = await response.text(encoding="shift-jis")
                await self.parse_usage_data(text_data)
                _LOGGER.debug("EcoMane usage data updated successfully")
        except Exception as err:
            _LOGGER.error("Error updating usage data: %s", err)
            raise UpdateFailed("update_usage_data failed") from err
        # finally:

    async def parse_usage_data(self, text: str) -> dict:
        """Parse data from the content."""

        # BeautifulSoupを使用してHTMLを解析
        soup = BeautifulSoup(text, "html.parser")
        # 指定したIDを持つdivタグの値を取得して辞書に格納
        for usage_sensor_desc in ecomane_usage_sensors_descs:
            key = usage_sensor_desc.key
            div = soup.find("div", id=key)
            if div:
                value = div.text.strip()
                self._data_dict[key] = value
        return self._data_dict

    async def update_circuit_power_data(self) -> dict:
        """Update power data."""
        _LOGGER.debug("update_circuit_power_data")
        try:
            # デバイスからデータを取得
            url = f"http://{self._ip_address}/{SENSOR_CIRCUIT_CGI}"
            async with aiohttp.ClientSession() as session:
                self._circuit_count = 0
                for (
                    page_num
                ) in self.natural_number_generator():  # 1ページ目から順に取得
                    url = f"http://{self._ip_address}/{SENSOR_CIRCUIT_CGI}&page={page_num}"
                    response: aiohttp.ClientResponse = await session.get(url)
                    if response.status != 200:
                        _LOGGER.error(
                            "Error fetching data from %s. Status code: %s",
                            url,
                            response.status,
                        )
                        raise UpdateFailed(
                            f"Error fetching data from {url}. Page: {page_num} Status code: {response.status}"
                        )
                    # テキストデータを取得する際に shift-jis エンコーディングを指定
                    text_data = await response.text(encoding="shift-jis")
                    # text_data からデータを取得, 最大ページ total_page に達したら終了
                    total_page = await self.parse_circuit_power_data(
                        text_data, page_num
                    )
                    if page_num >= total_page:
                        break
                self._attr_circuit_total = self._circuit_count
                _LOGGER.debug("Total number of circuits: %s", self._attr_circuit_total)
        except Exception as err:
            _LOGGER.error("Error updating circuit power data: %s", err)
            raise UpdateFailed("update_circuit_power_data failed") from err
        # finally:

        _LOGGER.debug("EcoMane circuit power data updated successfully")
        return self._data_dict

    async def parse_circuit_power_data(self, text: str, page_num: int) -> int:
        """Parse data from the content."""
        # BeautifulSoupを使用してHTMLを解析
        soup = BeautifulSoup(text, "html.parser")
        # 最大ページ数を取得
        maxp = soup.find("input", {"name": "maxp"})
        total_page = 0
        if isinstance(maxp, Tag):
            value = maxp.get("value", "0")
            # Ensure value is a string before converting to int
            if isinstance(value, str):
                total_page = int(value)

        # ページ内の各センサーエンティティのデータを取得
        for button_num in range(1, 9):
            sensor_num = self._circuit_count
            prefix = f"{SENSOR_CIRCUIT_PREFIX}_{sensor_num:02d}"
            div_id = f"{SENSOR_CIRCUIT_SELECTOR_PREFIX}_{button_num:02d}"  # ojt_??

            div_element: Tag | NavigableString | None = soup.find("div", id=div_id)
            if isinstance(div_element, Tag):
                # 回路の(ボタンの)selNo
                button_div = div_element.find(
                    "div",
                    class_=SENSOR_CIRCUIT_SELECTOR_BUTTON,  # btn btn_58
                )  # btn btn_58
                if isinstance(button_div, Tag):
                    a_tag = button_div.find("a")
                    # <a href="javascript:moveCircuitChange('selNo')">...</a>
                    if isinstance(a_tag, Tag) and "href" in a_tag.attrs:
                        href_value = a_tag["href"]
                        # JavaScriptの関数呼び出しを分解
                        if isinstance(href_value, str):
                            js_parts = href_value.split("moveCircuitChange('")
                        if len(js_parts) > 1:
                            selNo = js_parts[1].split("')")[0]
                            self._data_dict[
                                f"{prefix}_{SENSOR_CIRCUIT_SELECTOR_BUTTON}"
                            ] = selNo

                # 場所
                element: Tag | NavigableString | int | None = div_element.find(
                    "div",
                    class_=SENSOR_CIRCUIT_SELECTOR_PLACE,  # txt
                )
                if isinstance(element, Tag):
                    self._data_dict[f"{prefix}_{SENSOR_CIRCUIT_SELECTOR_PLACE}"] = (
                        element.get_text()
                    )  # txt

                # 回路
                element = div_element.find(
                    "div", class_=SENSOR_CIRCUIT_SELECTOR_CIRCUIT
                )  # txt2
                if isinstance(element, Tag):
                    self._data_dict[f"{prefix}_{SENSOR_CIRCUIT_SELECTOR_CIRCUIT}"] = (
                        element.get_text()
                    )  # txt2

                # 電力
                element = div_element.find(
                    "div", class_=SENSOR_CIRCUIT_SELECTOR_POWER
                )  # num
                if isinstance(element, Tag):
                    self._data_dict[f"{prefix}_{SENSOR_CIRCUIT_SELECTOR_POWER}"] = (
                        element.get_text().split("W")[0]
                    )

                # 電力量を取得
                await self.update_circuit_energy_data(
                    page_num, total_page, selNo, prefix
                )

                # 回路数をカウント
                self._circuit_count += 1

                # デバッグログ
                _LOGGER.debug(
                    "page:%s id:%s prefix:%s selNo:%s circuit_power:%s circuit_energy:%s",
                    page_num,
                    div_id,
                    prefix,
                    selNo,
                    self._data_dict[f"{prefix}_{SENSOR_CIRCUIT_SELECTOR_POWER}"],
                    self._data_dict[f"{prefix}_{SENSOR_CIRCUIT_ENERGY_SELECTOR}"],
                )
            else:
                _LOGGER.debug("div_element not found div_id:%s", div_id)
                break

        return total_page

    async def update_circuit_energy_data(
        self, page_num: int, total_page: int, selNo: str, prefix: str
    ) -> None:
        """Update circuit energy data."""
        _LOGGER.debug(
            "update_circuit_energye_data page_num:%s total_page:%s selNo:%s prefix:%s",
            page_num,
            total_page,
            selNo,
            prefix,
        )
        try:
            # デバイスからデータを取得
            url = f"http://{self._ip_address}/{SENSOR_CIRCUIT_ENERGY_CGI}?page={page_num}&maxp={total_page}&disp=0&selNo={selNo}&check=2"
            async with aiohttp.ClientSession() as session:
                response: aiohttp.ClientResponse = await session.get(url)
                if response.status != 200:
                    _LOGGER.error(
                        "Error fetching data from %s. Status code: %s",
                        url,
                        response.status,
                    )
                    raise UpdateFailed(
                        f"Error fetching data from {url}. Status code: {response.status}"
                    )
                # テキストデータを取得する際にエンコーディングを指定
                text_data = await response.text(encoding="shift-jis")

                # 回路別電力量を取得
                circuit_energy = await self.parse_circuit_energy_data(text_data, prefix)
                _LOGGER.debug(
                    "EcoMane circuit energy data updated successfully. circuit_energy:%f",
                    circuit_energy,
                )
        except Exception as err:
            _LOGGER.error("Error updating circuit energy data: %s", err)
            raise UpdateFailed("update_circuit_energy_data failed") from err
        # finally:

    async def parse_circuit_energy_data(self, text: str, prefix: str) -> float:
        """Parse data from the content."""

        # BeautifulSoupを使用してHTMLを解析
        soup = BeautifulSoup(text, "html.parser")
        # 今日の消費電力量を取得 (<div id="ttx_01" class="ttx">今日:1.02kWh　昨日:3.16kWh</div>)
        ttx = soup.find("div", id=SENSOR_CIRCUIT_ENERGY_SELECTOR)  # ttx_01
        if isinstance(ttx, Tag):
            today_parts = ttx.get_text().split("今日:")
            if len(today_parts) > 1:
                today_energy = today_parts[1].split("kWh")[0]
                sensor_id = f"{prefix}_{SENSOR_CIRCUIT_ENERGY_SELECTOR}"
                self._data_dict[sensor_id] = today_energy
                _LOGGER.debug(
                    "prefix:%s circuit_energy:%s",
                    prefix,
                    self._data_dict[sensor_id],
                )
        return float(today_energy)

    async def async_config_entry_first_refresh(self) -> None:
        """Perform the first refresh with retry logic."""
        while True:
            try:
                self.data = await self._async_update_data()
                break
            except UpdateFailed as err:
                _LOGGER.warning(
                    "Initial data fetch failed, retrying in %d seconds: %s",
                    RETRY_INTERVAL,
                    err,
                )
                await asyncio.sleep(RETRY_INTERVAL)  # Retry interval

    @property
    def circuit_total(self) -> int:
        """Total number of power sensors."""
        return self._attr_circuit_total

    @property
    def usage_sensor_descs(self) -> list[EcoManeUsageSensorEntityDescription]:
        """Usage sensor descriptions."""
        return self._attr_usage_sensor_descs

    @property
    def ip_address(self) -> str:
        """IP address."""
        return self._data_dict[KEY_IP_ADDRESS]
