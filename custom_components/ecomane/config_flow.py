"""The Eco Mane Config Flow."""

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant, callback

from .const import (
    CONFIG_SELECTOR_IP,
    CONFIG_SELECTOR_NAME,
    DEFAULT_IP_ADDRESS,
    DEFAULT_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


@callback
def configured_instances(hass: HomeAssistant) -> set[str]:
    """Return a set of configured instances."""

    return {entry.data["name"] for entry in hass.config_entries.async_entries(DOMAIN)}


class EcoManeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Eco Mane."""

    VERSION = 0
    MINOR_VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""

        _LOGGER.debug("async_step_user")
        errors = {}
        if user_input is not None:
            # ユーザ入力の検証
            if user_input[CONFIG_SELECTOR_NAME] in configured_instances(self.hass):
                # 既に同じ名前のエントリが存在する場合はエラー
                errors["base"] = "name_exists"
            else:
                # エントリを作成
                return self.async_create_entry(
                    title=user_input[CONFIG_SELECTOR_NAME], data=user_input
                )

        # ユーザ入力フォームのスキーマ
        data_schema = vol.Schema(
            {
                vol.Required(
                    CONFIG_SELECTOR_NAME,
                    default=DEFAULT_NAME,
                ): str,
                vol.Required(CONFIG_SELECTOR_IP, default=DEFAULT_IP_ADDRESS): str,
            }
        )

        # ユーザ入力フォームを表示
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
