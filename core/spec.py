from core.client import LostarkAPIClient
from collections import Counter
import re
import json


ACCESSORIES_GRADE = {
    "낙인력": {
        "8.00%": "상",
        "4.80%": "중",
        "2.15%": "하",
    },
    "추가 피해": {
        "2.60%": "상",
        "1.60%": "중",
        "0.60%": "하",
    },
    "적에게 주는 피해": {
        "2.00%": "상",
        "1.20%": "중",
        "0.55%": "하",
    },
    "공격력": {
        "1.55%": "상",
        "0.95%": "중",
        "0.40%": "하",
        "390": "상",
        "195": "중",
        "80": "하",
    },
    "무기 공격력": {
        "3.00%": "상",
        "1.80%": "중",
        "0.80%": "하",
        "960": "상",
        "480": "중",
        "195": "하",
    },
    "세레나데, 신앙, 조화 게이지 획득량": {
        "6.00%": "상",
        "3.60%": "중",
        "1.60%": "하",
    },
    "아군 공격력 강화 효과": {
        "5.00%": "상",
        "3.00%": "중",
        "1.35%": "하",
    },
    "치명타 피해": {
        "4.00%": "상",
        "2.40%": "중",
        "1.10%": "하",
    },
    "치명타 적중률": {
        "1.55%": "상",
        "0.95%": "중",
        "0.40%": "하",
    },
    "아군 피해량 강화 효과": {
        "7.50%": "상",
        "4.50%": "중",
        "2.00%": "하",
    },
}


class SpecClient(LostarkAPIClient):
    def __init__(self, name: str):
        self.name = name
        self.spec = {}

    def get_spec(self):
        self._set_gem()
        self._set_equipment()

    def _set_gem(self):
        path = f"/armories/characters/{self.name}/gems"
        response = self._get_response(path=path, method="GET")
        gems = response.json()["Gems"]
        gem_list = []
        for gem in gems:
            gem_full = gem["Name"]
            gem_name = re.sub(r"<[a-zA-z \'=#/0-9]+>", "", gem_full)
            gem_level_str, gem_type_str, *_ = gem_name.split(" ")
            gem_level = re.match(r"[0-9]+", gem_level_str).group()
            gem_type = gem_type_str[:2]
            gem_list.append(f"{gem_level} {gem_type}")
        gem_dict = dict(Counter(gem_list))
        self.spec["gem"] = gem_dict

    def _set_equipment(self):
        path = f"/armories/characters/{self.name}/equipment"
        response = self._get_response(path, method="GET")
        gears, accessories = response.json()[:6], response.json()[6:11]
        self._set_gear(gears)
        self._set_accessories(accessories)

    def _set_gear(self, gears):
        gear_dict = {}
        for gear in gears:
            gear_type = gear["Type"]
            gear_grade = gear["Grade"]
            gear_enforce = int(gear["Name"].split(" ")[0].replace("+", ""))
            tooltip = gear["Tooltip"]
            try:
                gear_transcendence_level = int(
                    re.sub(
                        r"<[a-zA-Z/0-9=# \']+>|[가-힣\[\] ]+",
                        "",
                        re.search(r"\[초월[a-zA-z0-9</>#\' =]+단계", tooltip).group(),
                    )
                )
            except AttributeError:
                gear_transcendence_level = None
            gear_elixir_infos = []
            if gear_type != "무기":
                elixir_tooltips = re.findall(
                    r"[\[가-힣\]]+</FONT> [가-힣a-zA-Z<>0-9 \'#=\(\).\]\[]+Lv.[0-9]",
                    tooltip,
                )
                for et in elixir_tooltips:
                    e_type = re.match(r"[\[가-힣\]]+", et).group()
                    e_name = re.search(r">[ 가-힣\(\) ]+", et).group()[1:].strip()
                    e_level = int(re.search(r">Lv.[0-9]", et).group()[4])

                    elixir_info = {"type": e_type, "name": e_name, "level": e_level}
                    gear_elixir_infos.append(elixir_info)

            gear_info = {
                "grade": gear_grade,
                "enforce": gear_enforce,
                "transcendence_level": gear_transcendence_level,
                "elixir": gear_elixir_infos,
            }
            gear_dict[gear_type] = gear_info

        self.spec["gear"] = gear_dict

    def _set_accessories(self, accessories):
        accessory_dict = {}
        for accessory in accessories:
            accessory_type = accessory["Type"]
            accessory_grade = accessory["Grade"]
            tooltip = accessory["Tooltip"]
            effects_str = re.findall(
                r">[가-힣 +%0-9.]+",
                json.loads(tooltip)["Element_005"]["value"]["Element_001"],
            )
            effects = []
            for effect in effects_str:
                name, value = effect.split(" +")
                name = name.replace(">", "")
                try:
                    grade = ACCESSORIES_GRADE[name][value]
                except KeyError:
                    grade = None
                effect_dict = {"name": name, "value": value, "grade": grade}
                effects.append(effect_dict)
            accessory_info = {"grade": accessory_grade, "effects": effects}
            if accessory_type in accessory_dict:
                accessory_dict[accessory_type].append(accessory_info)
            else:
                accessory_dict[accessory_type] = [accessory_info]

        self.spec["accessory"] = accessory_dict

    def _set_engarving(self):
        engarving_list = []
        path = f"/armories/characters/{self.name}/engravings"
        response = self._get_response(path, method="GET")
        engarvings = response.json()["ArkPassiveEffects"]
        for engarving in engarvings:
            grade = engarving["Grade"]
            level = engarving["Level"]
            name = engarving["Name"]
            stone_level = engarving["AbilityStoneLevel"]
            engarving_info = {
                "grade": grade,
                "level": level,
                "name": name,
                "stone_level": stone_level,
            }
            engarving_list.append(engarving_info)

        self.spec["engarvings"] = engarving_list
