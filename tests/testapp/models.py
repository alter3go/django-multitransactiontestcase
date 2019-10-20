from django.db.models import Model, TextField


class ExampleModel(Model):
    name = TextField(null=True, blank=True)
