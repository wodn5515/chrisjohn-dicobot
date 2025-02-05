import os
import requests


LOSTARK_API_JWT = os.getenv("LOSTARK_API_JWT")


class LostarkAPIClient:
    base_url = "https://developer-lostark.game.onstove.com"

    def _get_header(self):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"bearer {LOSTARK_API_JWT}",
        }
        return headers

    def _get_url(self, path):
        return f"{self.base_url}{path}"

    def _get_response(
        self,
        path: str,
        method: str,
        params: dict = None,
        body: dict = None,
        additional_headers: dict = {},
    ):
        url = self._get_url(path)
        headers = self._get_header()
        headers.update(additional_headers)

        if method == "GET":
            response = requests.get(url=url, params=params, headers=headers)
        elif method == "POST":
            response = requests.post(url=url, json=body, headers=headers)

        return response
