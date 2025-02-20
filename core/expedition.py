from core.client import LostarkAPIClient
from core.utils import CLEAR_GOLDS, CLASS_EMOJIS
import discord


class ExpeditionClient(LostarkAPIClient):
    def __init__(self, name: str):
        self.name = name
        self.expedition = {}

    def set_expedition(self):
        url = f"/characters/{self.name}/siblings"
        response = self._get_response(url, "GET").json()
        siblings = {}

        for sibling in response:
            server = sibling["ServerName"]
            try:
                sibling_info = {
                    "name": sibling["CharacterName"],
                    "level": sibling["CharacterLevel"],
                    "class": sibling["CharacterClassName"],
                    "item_level": float(sibling["ItemMaxLevel"].replace(",", "")),
                    "class_emoji": CLASS_EMOJIS[sibling["CharacterClassName"]],
                }
            except KeyError:
                continue
            if server in siblings:
                siblings[server].append(sibling_info)
            else:
                siblings[server] = [sibling_info]

        for server in siblings:
            siblings[server].sort(key=lambda x: x["item_level"], reverse=True)
        self.expedition = siblings

    def _get_weekly_gold_info(self):
        servers = []
        for server, siblings in self.expedition.items():
            gold_description = ""
            total = 0
            even_weeks_total = 0
            main_siblings = siblings[:6]
            for sibling in main_siblings:
                for level, gold_data in CLEAR_GOLDS.items():
                    if sibling["item_level"] >= level:
                        gold = gold_data["gold"]
                        even_weeks_gold = gold_data["2week_add"]
                        total += gold
                        if even_weeks_gold is not None:
                            even_weeks_total += even_weeks_gold
                            gold_description += f"<:gold:1342060913230086151> {gold} {sibling['name']} (격주 +{even_weeks_gold})\n"
                        else:
                            gold_description += f"<:gold:1342060913230086151> {gold} {sibling['name']}\n"
                        break

            gold_title = (
                f"합계: <:gold:1342060913230086151> {total} (격주 +{even_weeks_total})"
            )
            servers.append(
                {
                    "server": server,
                    "gold_total": total,
                    "gold_description": gold_description,
                    "gold_title": gold_title,
                }
            )
        servers = sorted(servers, key=lambda x: x["gold_total"], reverse=True)
        return servers[0]

    def _get_expedition_info(self, server: str):
        siblings = self.expedition[server]
        info = ">>> "
        for sibling in siblings:
            info += f"{sibling['class_emoji']}{sibling['name']} [{sibling['class']}]\n"
            info += f"-# Lv.{sibling['level']} | {sibling['item_level']}\n"
        return info

    def get_embed(self):
        gold_info = self._get_weekly_gold_info()
        server = gold_info["server"]
        siblings = self.expedition[server]

        embed = discord.Embed(title=f"원정대 : {self.name}", color=0x00F44C)
        embed.add_field(
            name=gold_info["gold_title"],
            value=gold_info["gold_description"],
            inline=False,
        )
        value = ">>> "
        name = ""
        for i, sibling in enumerate(siblings):
            value += (
                f"{sibling['class_emoji']}{sibling['name']} [{sibling['class']}]\n"
                f"-# Lv.{sibling['level']} | {sibling['item_level']}\n"
            )
            if i == len(siblings) - 1 or i % 3 == 2:
                embed.add_field(
                    name=name,
                    value=value,
                    inline=True,
                )
                if i == len(siblings) - 1:
                    break
                else:
                    value = ">>> "
            if i % 6 == 5:
                embed.add_field(
                    name="",
                    value="",
                    inline=False,
                )
        return embed
