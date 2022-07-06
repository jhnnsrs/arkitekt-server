import graphene
from graphene.types.generic import GenericScalar


class ChoiceInput(graphene.InputObjectType):
    value = GenericScalar(required=True)
    label = graphene.String(required=True)


class WidgetInput(graphene.InputObjectType):
    typename = graphene.String(description="type", required=True)
    query = graphene.String(description="Do we have a possible")
    dependencies = graphene.List(
        graphene.String, description="The dependencies of this port"
    )
    max = graphene.Int(description="Max value for int widget")
    min = graphene.Int(description="Max value for int widget")
    placeholder = graphene.String(description="Placeholder for any widget")
    choices = graphene.List(ChoiceInput, description="A list of choices")
