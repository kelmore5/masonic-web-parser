import os.path
import sys
import datetime
from .BaseModel import BaseModel
from peewee import *
from typing import Sequence, List

dir_path = os.path.dirname(os.path.realpath(__file__))
dir_path = os.path.abspath(os.path.join(dir_path, '../../..'))

sys.path.append(dir_path)

# noinspection PyPep8Naming
from lib.utils.lib.Jsons import Jsons as jsons


class RegionalLinksKeys:
    national_org: str = 'national_org'
    regional_org: str = 'regional_org'
    regional_link: str = 'regional_link'
    created_at: str = 'created_at'

    keys: List[str] = [national_org, regional_org, regional_link, created_at]


RK = RegionalLinksKeys


class RegionalLinks(BaseModel):
    national_org = CharField(max_length=1000)
    regional_org = CharField(max_length=1000)
    regional_link = CharField(max_length=1200, unique=True)

    @staticmethod
    def initialize(params: dict) -> 'RegionalLinks':
        region = RegionalLinks()

        if RK.national_org in params:
            region.national_org = params[RK.national_org]

        if RK.regional_org in params:
            region.regional_org = params[RK.regional_org]

        if RK.regional_link in params:
            region.regional_link = params[RK.regional_link]

        if RK.created_at in params:
            region.created_at = params[RK.created_at]

        return region

    def __str__(self):
        return str(jsons.create_dict(RegionalLinksKeys.keys, self.values()))

    def __repr__(self):
        return str(jsons.create_dict(RegionalLinksKeys.keys, self.values()))

    def values(self):
        return [self.national_org, self.regional_org, self.regional_link, self.created_at]

    def to_dict(self):
        output = dict()

        if self.national_org is not None:
            output[RK.national_org] = self.national_org

        if self.regional_org is not None:
            output[RK.regional_org] = self.regional_org

        if self.regional_link is not None:
            output[RK.regional_link] = self.regional_link

        if self.created_at is not None:
            output[RK.created_at] = self.created_at

        return output

    def upload_many(self, upload: Sequence['RegionalLinks']):
        self.insert_many([x.to_dict() for x in upload]).on_conflict('replace').execute()

    class Meta:
        global RK

        table_name = 'regional_links'
        indexes = (((RK.regional_link,), True), ((RK.created_at,), False,),)

        primary_key = CompositeKey(RK.national_org, RK.regional_org)
