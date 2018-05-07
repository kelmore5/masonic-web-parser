import os.path
import sys
from .RegionalLinks import RegionalLinks, RegionalLinksKeys
from .BaseModel import BaseModel
from peewee import *
from typing import Sequence

dir_path = os.path.dirname(os.path.realpath(__file__))
dir_path = os.path.abspath(os.path.join(dir_path, '../../..'))

sys.path.append(dir_path)

# noinspection PyPep8Naming
from lib.utils.lib.Jsons import Jsons as jsons


class OrganizationsKeys(RegionalLinksKeys):
    page_link = 'page_link'
    name = 'name'
    number = 'number'
    address = 'address'
    founded_date = 'founded_date'
    meeting_schedule = 'meeting_schedule'
    contact = 'contact'
    phone = 'phone'
    website = 'website'
    email = 'email'
    latitude = 'latitude'
    longitude = 'longitude'

    keys = [RegionalLinksKeys.national_org, RegionalLinksKeys.regional_org, RegionalLinksKeys.regional_link, page_link,
            name, number, address, founded_date, meeting_schedule, contact, phone, website, email, latitude, longitude,
            RegionalLinksKeys.created_at]


OK = OrganizationsKeys()


class Organizations(BaseModel):
    global OK

    national_org = CharField(max_length=1000)
    regional_org = CharField(max_length=1000)

    # TODO: Figure out how to do foreign key with multiple fields
    # Seems like the only way to do it in Peewee is through ManyToMany through table
    # which is jank - will probably have to change ORMs...
    #
    # national_org = ForeignKeyField(RegionalLinks, to_field=OK.national_org)
    # regional_org = ForeignKeyField(RegionalLinks, to_field=OK.regional_org)
    regional_link = ForeignKeyField(RegionalLinks, to_field=OK.regional_link)

    page_link = CharField(max_length=1000, unique=True)
    name = CharField(max_length=1000)
    number = IntegerField()
    address = TextField(null=True)
    founded_date = CharField(max_length=1000, null=True)
    meeting_schedule = TextField(null=True)
    contact = TextField(null=True)
    phone = CharField(max_length=1000, null=True)
    website = TextField(null=True)
    email = CharField(max_length=1000, null=True)
    latitude = DoubleField(null=True)
    longitude = DoubleField(null=True)

    @staticmethod
    def initialize(params: dict) -> 'Organizations':
        org = Organizations()

        if OK.national_org in params:
            org.national_org = params[OK.national_org]

        if OK.regional_org in params:
            org.regional_org = params[OK.regional_org]

        if OK.regional_link in params:
            org.regional_link = params[OK.regional_link]

        if OK.name in params:
            org.name = params[OK.name]

        if OK.number in params:
            org.number = params[OK.number]

        if OK.address in params:
            org.address = params[OK.address]

        if OK.founded_date in params:
            org.founded_date = params[OK.founded_date]

        if OK.meeting_schedule in params:
            org.meeting_schedule = params[OK.meeting_schedule]

        if OK.contact in params:
            org.contact = params[OK.contact]

        if OK.phone in params:
            org.phone = params[OK.phone]

        if OK.website in params:
            org.website = params[OK.website]

        if OK.email in params:
            org.email = params[OK.email]

        if OK.latitude in params:
            org.latitude = params[OK.latitude]

        if OK.longitude in params:
            org.longitude = params[OK.longitude]

        if OK.created_at in params:
            org.created_at = params[OK.created_at]

        return org

    def __str__(self):
        return str(jsons.create_dict(OrganizationsKeys.keys, self.values()))

    def __repr__(self):
        return str(jsons.create_dict(OrganizationsKeys.keys, self.values()))

    def values(self):
        # Test ForeignKeyFields first

        try:
            national_org = self.national_org
        except DoesNotExist:
            national_org = None

        try:
            regional_org = self.regional_org
        except DoesNotExist:
            regional_org = None

        try:
            regional_link = self.regional_link.regional_link
        except DoesNotExist:
            regional_link = None

        return [national_org, regional_org, regional_link, self.page_link, self.name, self.number, self.address,
                self.founded_date, self.meeting_schedule, self.contact, self.phone, self.website, self.email,
                self.latitude, self.longitude, self.created_at]

    def to_dict(self):
        output = dict()

        keys = OK.keys
        values = self.values()

        if len(keys) != len(values):
            raise IndexError('The length of keys and values were not equal for Organizations class. '
                             'This needs to be fixed internally')

        for idx in range(len(values)):
            value = values[idx]
            if value is not None:
                output[keys[idx]] = value

        return output

    def upload_many(self, upload: Sequence['Organizations']):
        if len(upload) > 0:
            self.insert_many([x.to_dict() for x in upload]).on_conflict('replace').execute()

    class Meta:
        indexes = (((OK.created_at,), False),)

        primary_key = CompositeKey(OK.national_org, OK.regional_org, OK.name, OK.number)
