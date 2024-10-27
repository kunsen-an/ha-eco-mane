"""Constants for the Eco Mane HEMS integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "ecomane"
DEFAULT_ENCODING = "UTF-8"  # デフォルトエンコーディング
DEFAULT_NAME = "Panasonic Eco Mane HEMS"
DEFAULT_IP_ADDRESS = "192.168.1.220"

ENCODING = "shift-jis"  # ECOマネのエンコーディング

PLATFORMS = [Platform.SENSOR]
PLATFORM = Platform.SENSOR

ENTITY_NAME = "EcoManeHEMS"

# Config セレクタ
CONFIG_SELECTOR_IP = "ip"
CONFIG_SELECTOR_NAME = "name"

# キー
KEY_IP_ADDRESS = "ip_address"

# 本日の使用量
SENSOR_TODAY_CGI = "ecoTopMoni.cgi"

# 回路
SENSOR_CIRCUIT_CGI = "elecCheck_6000.cgi?disp=2"
SENSOR_CIRCUIT_SELECTOR_PREFIX = "ojt"
SENSOR_CIRCUIT_PREFIX = "em_circuit"
SENSOR_CIRCUIT_SELECTOR_PLACE = "txt"
SENSOR_CIRCUIT_SELECTOR_CIRCUIT = "txt2"
SENSOR_CIRCUIT_SELECTOR_BUTTON = "btn btn_58"
# 回路別電力
SENSOR_CIRCUIT_SELECTOR_POWER = "num"
SENSOR_CIRCUIT_POWER_SERVICE_TYPE = "power"
# 回路別電力量
SENSOR_CIRCUIT_ENERGY_CGI = "resultGraphDiv_4242.cgi"
SENSOR_CIRCUIT_ENERGY_SELECTOR = "ttx_01"
SENSOR_CIRCUIT_ENERGY_SERVICE_TYPE = "energy"

# 時間間隔
RETRY_INTERVAL = 120  # 再試行間隔: 120秒
POLLING_INTERVAL = 60  # ECOマネへのpolling間隔: 60秒
