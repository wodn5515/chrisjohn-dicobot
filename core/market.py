from core.client import LostarkAPIClient
from requests.models import Response
from discord import Embed


class MarketClient(LostarkAPIClient):
    item: str
    quality: int

    def __init__(self, item=None, quality=None):
        self.item = item
        self.quality = quality

    def get_유각(self, name: str):
        path = "/markets/items"
        body = {
            "Sort": "CURRENT_MIN_PRICE",
            "CategoryCode": 40000,
            "ItemGrade": "유물",
            "ItemName": "각인",
            "PageNo": 1,
            "SortCondition": "DESC",
        }
        if name:
            body["ItemName"] = name
        response = self._get_response(path=path, method="POST", body=body)
        self._set_data_for_유각(response=response)

    def _set_data_for_유각(self, response: Response):
        data = []
        results = response.json()["Items"]

        for result in results:
            datum = {"name": result["Name"], "price": result["CurrentMinPrice"]}
            data.append(datum)

        self.data = data

    def get_embed_for_유각(self):
        embed = Embed(title="유물 각인서 시세랭킹", color=0xFF8C00)
        embed_string = ""

        for datum in self.data:
            embed_string += f"- {datum['name']} : {int(datum['price']):,}\n"

        embed.add_field(name="", value=embed_string)

        embed.set_thumbnail(
            url="https://cdn-lostark.game.onstove.com/efui_iconatlas/use/use_9_25.png"
        )

        return embed
