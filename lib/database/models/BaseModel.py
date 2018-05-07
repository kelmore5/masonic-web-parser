from peewee import *
import os
import datetime

dir_path = os.path.dirname(os.path.realpath(__file__))
dir_path = os.path.abspath(os.path.join(dir_path, '..'))

db = SqliteDatabase(dir_path + '/masonic.db', pragmas=(('foreign_keys', 'on'),))


class BaseModel(Model):
    db = db
    created_at = DateTimeField(default=datetime.datetime.now)

    def to_dict(self):
        output = dict()
        keys = BaseModel._meta.get_sorted_fields()

        values = self.values()

        if len(keys) != len(values):
            raise IndexError('The length of keys and values were not equal for Organizations class. '
                             'This needs to be fixed internally')

        for idx in range(len(values)):
            value = values[idx]
            if value is not None:
                output[keys[idx]] = value

        return output

    def values(self):
        return [self.created_at]

    class Meta:
        database = db
