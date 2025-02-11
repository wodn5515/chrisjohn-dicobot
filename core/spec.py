from core.client import LostarkAPIClient
from discord import Embed
import re
import json

GEM_DICT = {
    "1": {"겁화": 0, "작열": 0, "멸화": 0, "홍염": 0},
    "2": {"겁화": 0, "작열": 0, "멸화": 0, "홍염": 0},
    "3": {"겁화": 0, "작열": 0, "멸화": 0, "홍염": 0},
    "4": {"겁화": 0, "작열": 0, "멸화": 0, "홍염": 0},
    "5": {"겁화": 0, "작열": 0, "멸화": 0, "홍염": 0},
    "6": {"겁화": 0, "작열": 0, "멸화": 0, "홍염": 0},
    "7": {"겁화": 0, "작열": 0, "멸화": 0, "홍염": 0},
    "8": {"겁화": 0, "작열": 0, "멸화": 0, "홍염": 0},
    "9": {"겁화": 0, "작열": 0, "멸화": 0, "홍염": 0},
    "10": {"겁화": 0, "작열": 0, "멸화": 0, "홍염": 0},
}


ACCESSORIES_GRADE = {
    "낙인력": {
        "8.00%": "<:HIGH:1338577920888930354>",
        "4.80%": "<:MIDDLE:1338578719559651389>",
        "2.15%": "<:LOW:1338580294965657700>",
    },
    "추가 피해": {
        "2.60%": "<:HIGH:1338577920888930354>",
        "1.60%": "<:MIDDLE:1338578719559651389>",
        "0.60%": "<:LOW:1338580294965657700>",
    },
    "적에게 주는 피해": {
        "2.00%": "<:HIGH:1338577920888930354>",
        "1.20%": "<:MIDDLE:1338578719559651389>",
        "0.55%": "<:LOW:1338580294965657700>",
    },
    "공격력": {
        "1.55%": "<:HIGH:1338577920888930354>",
        "0.95%": "<:MIDDLE:1338578719559651389>",
        "0.40%": "<:LOW:1338580294965657700>",
        "390": "<:HIGH:1338577920888930354>",
        "195": "<:MIDDLE:1338578719559651389>",
        "80": "<:LOW:1338580294965657700>",
    },
    "무기 공격력": {
        "3.00%": "<:HIGH:1338577920888930354>",
        "1.80%": "<:MIDDLE:1338578719559651389>",
        "0.80%": "<:LOW:1338580294965657700>",
        "960": "<:HIGH:1338577920888930354>",
        "480": "<:MIDDLE:1338578719559651389>",
        "195": "<:LOW:1338580294965657700>",
    },
    "세레나데, 신앙, 조화 게이지 획득량": {
        "6.00%": "<:HIGH:1338577920888930354>",
        "3.60%": "<:MIDDLE:1338578719559651389>",
        "1.60%": "<:LOW:1338580294965657700>",
    },
    "아군 공격력 강화 효과": {
        "5.00%": "<:HIGH:1338577920888930354>",
        "3.00%": "<:MIDDLE:1338578719559651389>",
        "1.35%": "<:LOW:1338580294965657700>",
    },
    "치명타 피해": {
        "4.00%": "<:HIGH:1338577920888930354>",
        "2.40%": "<:MIDDLE:1338578719559651389>",
        "1.10%": "<:LOW:1338580294965657700>",
    },
    "치명타 적중률": {
        "1.55%": "<:HIGH:1338577920888930354>",
        "0.95%": "<:MIDDLE:1338578719559651389>",
        "0.40%": "<:LOW:1338580294965657700>",
    },
    "아군 피해량 강화 효과": {
        "7.50%": "<:HIGH:1338577920888930354>",
        "4.50%": "<:MIDDLE:1338578719559651389>",
        "2.00%": "<:LOW:1338580294965657700>",
    },
}


class SpecClient(LostarkAPIClient):
    def __init__(self, name: str):
        self.name = name
        self.spec = {}

    def set_spec(self):
        path = f"/armories/characters/{self.name}?filters=profiles+equipment+cards+gems+engravings+arkpassive"
        response = self._get_response(path, method="GET").json()
        profiles = response["ArmoryProfile"]
        arkpassives = response["ArkPassive"]["Points"]
        gems = response["ArmoryGem"]["Gems"]
        engravings = response["ArmoryEngraving"]["ArkPassiveEffects"]
        equipments = response["ArmoryEquipment"]
        gears, accessories = equipments[:6], equipments[6:11]
        card_effects = response["ArmoryCard"]["Effects"]
        self._set_profiles(profiles, arkpassives)
        self._set_gems(gems)
        self._set_gears(gears)
        self._set_accessories(accessories)
        self._set_cards(card_effects)
        self._set_engravings(engravings)

    def get_embed(self):
        embed = Embed(title=f"군장검사 : {self.name}", color=0x00F44C)

        basic_info = self._get_basic_info_embed()
        gear_title, gear_info = self._get_gear_info_embed()
        accessory_info = self._get_accessory_info_embed()
        engraving_info = self._get_engraving_info_embed()
        link_info = self._get_link_info_embed()
        embed.add_field(name="기본정보", value=basic_info, inline=False)
        embed.add_field(name="보석", value=" | ".join(self.spec["gem"]), inline=False)
        embed.add_field(name=gear_title, value=gear_info, inline=True)
        embed.add_field(name="**악세사리**", value=accessory_info, inline=True)
        embed.add_field(name="각인", value=engraving_info, inline=False)
        embed.add_field(name="카드", value="\n".join(self.spec["card"]), inline=False)
        embed.add_field(name="외부링크", value=link_info)

        embed.set_thumbnail(url=self.spec["profile"]["thumbnail"])

        return embed

    def _get_link_info_embed(self):
        embed_string = f"[즐로아](https://zloa.net/char/{self.name}) | [로아와](https://loawa.com/char/{self.name}) | "
        embed_string += f"[사사게검색기](https://sasagefind.com/?who={self.name})"
        return embed_string

    def _get_engraving_info_embed(self):
        embed_string = ">>> -# 전각을 안 읽었을시 취소선\n"
        for engraving in self.spec["engraving"]:
            if engraving["grade"] != "유물":
                embed_string += f"~~{engraving['name']}~~\n"
            else:
                embed_string += engraving["name"]
                relic_cnt = engraving["level"]
                stone_cnt = engraving["stone_level"]
                if relic_cnt > 0:
                    embed_string += f" | {'<:RELIC:1338586934343241798>'*relic_cnt}"
                if stone_cnt is not None:
                    embed_string += f" | {'<:STONE:1338586888008896672>'*stone_cnt}"
                embed_string += "\n"

        return embed_string

    def _get_basic_info_embed(self):
        profile = self.spec["profile"]
        embed_string = f"""
        >>> 아이템 Lv.{profile["item_level"]} | 전투 Lv.{profile["battle_level"]} | 원정대 Lv.{profile["expedition_level"]}
        서버: {profile["server"]} | 직업: {profile["class"]}\n칭호: {profile["title"]}
        {" | ".join(profile["arkpassive"])}"""
        return embed_string

    def _get_gear_info_embed(self):
        gears = self.spec["gear"]
        part_list_for_order = ["투구", "어깨", "상의", "하의", "장갑", "무기"]
        inheritance = 0
        elixir_cnt = 0
        embed_string = ">>> "

        for part in part_list_for_order:
            gear = gears[part]
            if part != "무기" and gear["grade"] == "고대":
                inheritance += 1
            embed_string += f"**{part}** +{gear['enforce']}"
            if gear["transcendence_level"]:
                embed_string += f" [초월 {gear['transcendence_level']}단계]\n"
            else:
                embed_string += "\n"
            if elixirs := gear["elixir"]:
                for elixir in elixirs:
                    embed_string += (
                        f"-# {elixir['type']} {elixir['name']}: {elixir['level']}\n"
                    )
                    elixir_cnt += elixir["level"]

        return f"**장비** [{inheritance}부위 계승 | 엘{elixir_cnt}]", embed_string

    def _get_accessory_info_embed(self):
        acs = self.spec["accessory"]
        part_list_for_order = ["목걸이", "귀걸이", "반지"]
        embed_string = ">>> "

        for part in part_list_for_order:
            ac = acs[part]
            for i in ac:
                embed_string += f"**{part}** [{i['grade']}]\n"
                for effect in i["effects"]:
                    embed_string += (
                        f"-# {effect['grade']} {effect['name']} - {effect['value']}\n"
                    )
        return embed_string

    def _set_profiles(self, profiles, arkpassives):
        arkpassive_list = []
        for arkpassive in arkpassives:
            arkpassive_str = f"{arkpassive['Name']} {arkpassive['Value']}"
            arkpassive_list.append(arkpassive_str)

        profile_dict = {
            "thumbnail": profiles["CharacterImage"],
            "expedition_level": profiles["ExpeditionLevel"],
            "title": profiles["Title"],
            "item_level": profiles["ItemAvgLevel"],
            "battle_level": profiles["CharacterLevel"],
            "server": profiles["ServerName"],
            "class": profiles["CharacterClassName"],
            "arkpassive": arkpassive_list,
        }

        self.spec["profile"] = profile_dict

    def _set_gems(self, gems):
        gem_dict = {
            "10": {"겁화": 0, "작열": 0, "멸화": 0, "홍염": 0},
            "9": {"겁화": 0, "작열": 0, "멸화": 0, "홍염": 0},
            "8": {"겁화": 0, "작열": 0, "멸화": 0, "홍염": 0},
            "7": {"겁화": 0, "작열": 0, "멸화": 0, "홍염": 0},
            "6": {"겁화": 0, "작열": 0, "멸화": 0, "홍염": 0},
            "5": {"겁화": 0, "작열": 0, "멸화": 0, "홍염": 0},
            "4": {"겁화": 0, "작열": 0, "멸화": 0, "홍염": 0},
            "3": {"겁화": 0, "작열": 0, "멸화": 0, "홍염": 0},
            "2": {"겁화": 0, "작열": 0, "멸화": 0, "홍염": 0},
            "1": {"겁화": 0, "작열": 0, "멸화": 0, "홍염": 0},
        }
        for gem in gems:
            gem_full = gem["Name"]
            gem_name = re.sub(r"<[a-zA-z \'=#/0-9]+>", "", gem_full)
            gem_level_str, gem_type_str, *_ = gem_name.split(" ")
            gem_level = re.match(r"[0-9]+", gem_level_str).group()
            gem_type = gem_type_str[:2]
            gem_dict[gem_level][gem_type] += 1

        gem_list = []
        for gem_level in gem_dict:
            for gem_type in gem_dict[gem_level]:
                gem_cnt = gem_dict[gem_level][gem_type]
                if gem_cnt > 0:
                    gem_list.append(f"{gem_level}{gem_type[0]} - {gem_cnt}")

        self.spec["gem"] = gem_list

    def _set_gears(self, gears):
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
                r">[가-힣 +%0-9.,]+",
                json.loads(tooltip)["Element_005"]["value"]["Element_001"],
            )
            effects = []
            for effect in effects_str:
                name, value = effect.split(" +")
                name = name.replace(">", "")
                try:
                    grade = ACCESSORIES_GRADE[name][value]
                except KeyError:
                    grade = "<:NONE:1338580771681603634>"
                effect_dict = {"name": name, "value": value, "grade": grade}
                effects.append(effect_dict)
            accessory_info = {"grade": accessory_grade, "effects": effects}
            if accessory_type in accessory_dict:
                accessory_dict[accessory_type].append(accessory_info)
            else:
                accessory_dict[accessory_type] = [accessory_info]

        self.spec["accessory"] = accessory_dict

    def _set_engravings(self, engravings):
        engraving_list = []
        for engraving in engravings:
            grade = engraving["Grade"]
            level = engraving["Level"]
            name = engraving["Name"]
            stone_level = engraving["AbilityStoneLevel"]
            engraving_info = {
                "grade": grade,
                "level": level,
                "name": name,
                "stone_level": stone_level,
            }
            engraving_list.append(engraving_info)

        self.spec["engraving"] = engraving_list

    def _set_cards(self, card_effects):
        card_list = []
        for card_effect in card_effects:
            card_set = card_effect["Items"][-1]["Name"]
            card_list.append(card_set)

        self.spec["card"] = card_list
