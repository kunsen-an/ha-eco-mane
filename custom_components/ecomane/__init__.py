"""The Eco Mane HEMS integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONFIG_SELECTOR_IP, DOMAIN, PLATFORMS
from .coordinator import EcoManeDataCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up ecomane from a config entry."""

    ip = config_entry.data[CONFIG_SELECTOR_IP]

    # DataCoordinatorを作成
    coordinator = EcoManeDataCoordinator(hass, ip)
    # 初期データ取得
    await coordinator.async_config_entry_first_refresh()
    if not coordinator.last_update_success:
        raise ConfigEntryNotReady("async_config_entry_first_refresh() failed")

    # データを hass.data に保存
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = coordinator
    _LOGGER.debug("__init__.py config_entry.entry_id: %s", config_entry.entry_id)

    # エンティティの追加
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    # 正常にセットアップ出来たら True を返却
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    # エンティティのアンロード
    unload_ok = await hass.config_entries.async_forward_entry_unload(
        config_entry, Platform.SENSOR
    )

    # クリーンアップ処理
    if unload_ok:
        # EcoManeDataCoordinatorを削除
        hass.data[DOMAIN].pop(config_entry.entry_id, None)

    return unload_ok
