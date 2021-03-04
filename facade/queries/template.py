from facade.filters import PodFilter
from typing_extensions import Annotated
from balder.types import BalderQuery
from facade import types
from facade.enums import PodStatus
from facade.models import Template
import graphene
from herre import bounced
from balder.enum import InputEnum

class TemplateDetailQuery(BalderQuery):

    class Arguments:
        id = graphene.ID(description="The query pod")

    @bounced(anonymous=True)
    def resolve(root, info, id=None):
        return Template.objects.get(id=id)

    class Meta:
        type = types.Template
        operation = "template"



class Templates(BalderQuery):

    class Arguments:
        active = graphene.Boolean(description="Does the template have active pods?")
        provider = graphene.String(description="The Name of the provider")


    @bounced(anonymous=True)
    def resolve(root, info, active = None, provider=None):
        qs = Template.objects
        qs = qs.filter(pods__status=PodStatus.ACTIVE) if active else qs
        qs = qs.filter(provider__name=provider) if provider else qs
        return qs.all()


    class Meta:
        type = types.Template
        list = True