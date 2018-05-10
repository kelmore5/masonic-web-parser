from peewee import *

from .BaseModel import BaseModel
from .RegionalLinks import RegionalLinks


class OrganizationsKeys:
    created_at: str = 'created_at'

    national_org: str = 'national_org'
    regional_org: str = 'regional_org'
    regional_link: str = 'regional_link'
    page_link: str = 'page_link'
    name: str = 'name'
    number: str = 'number'
    address: str = 'address'
    founded_date: str = 'founded_date'
    meeting_schedule: str = 'meeting_schedule'
    contact: str = 'contact'
    phone: str = 'phone'
    website: str = 'website'
    email: str = 'email'
    latitude: str = 'latitude'
    longitude: str = 'longitude'


Keys = OrganizationsKeys


class Organizations(BaseModel):
    global Keys

    national_org = CharField(max_length=1000)
    regional_org = CharField(max_length=1000)

    # TODO: Figure out how to do foreign key with multiple fields
    # Seems like the only way to do it in Peewee is through ManyToMany through table
    # which is jank - will probably have to change ORMs...
    #
    # national_org = ForeignKeyField(RegionalLinks, to_field=OK.national_org)
    # regional_org = ForeignKeyField(RegionalLinks, to_field=OK.regional_org)
    regional_link = ForeignKeyField(RegionalLinks, to_field=Keys.regional_link)

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
        model = Organizations()

        if Keys.created_at in params:
            model.created_at = params[Keys.created_at]

        if Keys.national_org in params:
            model.national_org = params[Keys.national_org]

        if Keys.regional_org in params:
            model.regional_org = params[Keys.regional_org]

        if Keys.regional_link in params:
            model.regional_link = params[Keys.regional_link]

        if Keys.page_link in params:
            model.page_link = params[Keys.page_link]

        if Keys.name in params:
            model.name = params[Keys.name]

        if Keys.number in params:
            model.number = params[Keys.number]

        if Keys.address in params:
            model.address = params[Keys.address]

        if Keys.founded_date in params:
            model.founded_date = params[Keys.founded_date]

        if Keys.meeting_schedule in params:
            model.meeting_schedule = params[Keys.meeting_schedule]

        if Keys.contact in params:
            model.contact = params[Keys.contact]

        if Keys.phone in params:
            model.phone = params[Keys.phone]

        if Keys.website in params:
            model.website = params[Keys.website]

        if Keys.email in params:
            model.email = params[Keys.email]

        if Keys.latitude in params:
            model.latitude = params[Keys.latitude]

        if Keys.longitude in params:
            model.longitude = params[Keys.longitude]

        return model

    def values(self):
        try:
            regional_link = self.regional_link.regional_link
        except DoesNotExist:
            regional_link = None

        return [self.created_at, self.national_org, self.regional_org, regional_link, self.page_link,
                self.name, self.number, self.address, self.founded_date, self.meeting_schedule, self.contact,
                self.phone, self.website, self.email, self.latitude, self.longitude]

    class Meta:
        indexes = (((Keys.created_at,), False),)

        primary_key = CompositeKey(Keys.national_org, Keys.regional_org, Keys.name, Keys.number)
