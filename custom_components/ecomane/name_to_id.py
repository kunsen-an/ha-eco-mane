"""Creating a translation dictionary from Japanese to English."""

# 日本語からエンティティ名への変換辞書
ja_to_entity_translation_dict = {
    "購入電気量": "electricity_purchased",
    "CO2削減量": "co2_reduction",
    "CO2排出量": "co2_emissions",
    "ガス消費量": "gas_consumption",
    "太陽光発電量": "solar_power_energy",
    "売電量": "electricity_sales",
    "水消費量": "water_consumption",
    " 太陽光": "solar_panel",
    "キッチン 照明＆コンセント": "kitchen_lighting_and_outlets",
    "キッチン 食器洗い乾燥機": "kitchen_dishwasher",
    "キッチン（下） コンセント": "kitchen_lower_outlets",
    "キッチン（上） コンセント": "kitchen_upper_outlets",
    "ダイニング エアコン": "dining_air_conditioner",
    "ダイニング 照明＆コンセント": "dining_lighting_and_outlets",
    "ダイニング（南） 照明＆コンセント": "dining_south_lighting_and_outlets",
    "ダイニング（北） コンセント": "dining_north_outlets"
}


# 日本語名をエンティティ名に変換
def ja_to_entity(name: str) -> str:
    """Translate Japanese name to entity name."""
    return ja_to_entity_translation_dict.get(name, name)
