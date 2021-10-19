from facade.structures.widgets.types import Widget
from balder.registry import register_type
import graphene
from graphene.types.generic import GenericScalar

get_port_types = lambda: {
            "IntArgPort": IntArgPort,
            "StringArgPort": StringArgPort,
            "StructureArgPort": StructureArgPort,
            "ListArgPort": ListArgPort,
            "BoolArgPort": BoolArgPort,
            "EnumArgPort": EnumArgPort,
}


@register_type
class ArgPort(graphene.Interface):
    key = graphene.String()
    type = graphene.String()
    label = graphene.String()
    description = graphene.String(required=False)
    required = graphene.Boolean()
    widget = graphene.Field(Widget,description="Description of the Widget")

    @classmethod
    def resolve_type(cls, instance, info):
        typemap = get_port_types()
        _type = instance.get("type", instance.get("typename"))
        return typemap.get(_type, ArgPort)

@register_type
class IntArgPort(graphene.ObjectType):
    """Integer Port"""

    class Meta:
        interfaces = (ArgPort,)

@register_type
class BoolArgPort(graphene.ObjectType):
    """Integer Port"""

    class Meta:
        interfaces = (ArgPort,)

@register_type
class EnumArgPort(graphene.ObjectType):
    """Integer Port"""
    options = GenericScalar(description="A dict of options")

    class Meta:
        interfaces = (ArgPort,)



@register_type
class StringArgPort(graphene.ObjectType):
    """String Port"""
    default = graphene.String(description="Default value")

    class Meta:
        interfaces = (ArgPort,)


@register_type
class StructureArgPort(graphene.ObjectType):
    """Model Port"""
    identifier = graphene.String(description="The identifier of this Structure")

    class Meta:
        interfaces = (ArgPort,)


@register_type
class ListArgPort(graphene.ObjectType):
    """Model Port"""
    child = graphene.Field(lambda: ArgPort, description="The child")

    class Meta:
        interfaces = (ArgPort,)


    