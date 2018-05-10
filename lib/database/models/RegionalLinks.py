from peewee import *

from .BaseModel import BaseModel


class RegionalLinksKeys:
    created_at: str = 'created_at'

    national_org: str = 'national_org'
    regional_org: str = 'regional_org'
    regional_link: str = 'regional_link'


Keys = RegionalLinksKeys


class RegionalLinks(BaseModel):
    global Keys

    national_org = CharField(max_length=1000)
    regional_org = CharField(max_length=1000)
    regional_link = CharField(max_length=1200, unique=True)

    @staticmethod
    def initialize(params: dict) -> 'RegionalLinks':
        model = RegionalLinks()

        if Keys.created_at in params:
            model.created_at = params[Keys.created_at]

        if Keys.national_org in params:
            model.national_org = params[Keys.national_org]

        if Keys.regional_org in params:
            model.regional_org = params[Keys.regional_org]

        if Keys.regional_link in params:
            model.regional_link = params[Keys.regional_link]

        return model

    def values(self):
        return [self.created_at, self.national_org, self.regional_org, self.regional_link]

    class Meta:
        global Keys

        table_name = 'regional_links'
        indexes = (((Keys.regional_link,), True), ((Keys.created_at,), False,),)

        primary_key = CompositeKey(Keys.national_org, Keys.regional_org)
