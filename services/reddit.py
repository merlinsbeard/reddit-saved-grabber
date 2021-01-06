from datetime import datetime
import requests
import logging
from .exceptions import APIError
from typing import Optional

logger = logging.getLogger(__name__)

class Reddit():
    
    def __init__(
        self,
        client_secret: str,
        client_id: str,
        username: str,
        password: str,
        user_agent: str = 'Reddit Saved Grabber by merlinsbeardv0.1',
        filtered_fields: list = [
            "id", "title", "subreddit", "permalink", "url", "description", "media", "score",
            "domain", "created", "over_18", "author", "post_hint", "thumbnail", "preview"
        ]
        ):
        self.client_secret = client_secret
        self.client_id = client_id
        self.headers = {
            "User-Agent": user_agent
        }
        self.access_token = None
        self.username = username
        self.password = password
        self.authenticate(self.username, self.password)
        self.filtered_fields = filtered_fields


    def authenticate(self, username:str, password: str) -> None:
        url = "https://www.reddit.com/api/v1/access_token"
        client_auth = requests.auth.HTTPBasicAuth(self.client_id, self.client_secret)
        data = {
            "grant_type": "password",
            "username": username,
            "password": password
        }
        r = requests.post(url, data=data, auth=client_auth, headers=self.headers)
        if r.status_code != 200:
            raise APIError(r.text)
        data = r.json()
        if data.get('error'):
            raise APIError(data['error'])
        access_token = data['access_token']
        self.headers = {
            **self.headers,
            "Authorization": f"bearer {access_token}"
        }

    def get_list_saved(self, params: Optional[dict] = {}):
        url = f"https://oauth.reddit.com/user/{self.username}/saved"
        r = requests.get(url, headers=self.headers, params=params)
        self.list_saved = r.json()

    @property
    def list_saved_data(self) -> list :
        if self.list_saved.get('data'):
            return self.list_saved['data']['children']
        return []

    @property
    def list_saved_before(self) -> str or None:
        return self.list_saved['data']['before'] or None

    @property
    def list_saved_after(self) -> str or None:
        return self.list_saved['data']['after'] or None

    def list_saved_parsed(self) -> list:
        fields = self.filtered_fields
        new_list = []
        for x in self.list_saved_data:
            data = x.get('data')
            if data:
                _ = {}
                for k,v in data.items():
                    if k in fields:
                        if k == "created":
                            v = datetime.fromtimestamp(v)
                        if k == "preview":
                            v = v.get('images')
                            if v:
                                v = v[0]['source']['url'].replace('amp;', '')
                        _[k] = v
                new_list.append(_)
        return new_list

    def next_page(self) -> None:
        """Get next page if it exists"""
        if self.list_saved_after:
            params = {"after": self.list_saved_after}
            self.get_list_saved(params=params)

    def prev_page(self) -> None:
        """ Get Previous page if it exists"""
        if self.list_saved_before:
            params = {"before": self.list_saved_before}
            self.get_list_saved(params=params)

    def get_all_list_parsed(self) -> list:
        """Get all pages then show the parsed value"""
        self.get_list_saved()
        new_list = []
        new_list.extend(self.list_saved_parsed())
        while self.list_saved_after:
            self.next_page()
            new_list.extend(self.list_saved_parsed())
        return new_list