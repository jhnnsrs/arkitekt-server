from facade.enums import LogLevel, ProvisionStatus
from lok import bounced
from balder.types import BalderSubscription
from facade import models, types
import graphene


class ProvisionLogEvent(graphene.ObjectType):
    message = graphene.String()
    level = graphene.String()


class ProvisionEvent(graphene.ObjectType):
    log = graphene.Field(ProvisionLogEvent)


class ProvisionEventSubscription(BalderSubscription):
    class Arguments:
        reference = graphene.ID(
            description="The reference of the assignation", required=True
        )
        level = graphene.String(description="The log level for alterations")

    @classmethod
    def send_log(cls, groups, message, level=LogLevel.INFO):
        cls.broadcast(
            {"action": "log", "data": {"message": message, "level": level}}, groups
        )

    @bounced(only_jwt=True)
    def subscribe(root, info, *args, reference=None, level=None):
        provision = models.Provision.objects.get(reference=reference)
        return [f"provision_{provision.id}"]

    def publish(payload, info, *args, **kwargs):
        payload = payload["payload"]
        action = payload["action"]
        data = payload["data"]

        print("Publish dubplish", payload)

        if action == "log":
            return {"log": data}

        print("error in payload")

    class Meta:
        type = ProvisionEvent
        operation = "provisionEvent"


class ProvisionsEvent(graphene.ObjectType):
    delete = graphene.ID()
    update = graphene.Field(types.Provision)
    create = graphene.Field(types.Provision)


class MyProvisionsEvent(BalderSubscription):
    class Arguments:
        identifier = graphene.ID(
            description="The reference of this waiter", required=True
        )
        level = graphene.String(description="The log level for alterations")

    @bounced(only_jwt=True)
    def subscribe(root, info, identifier, **kwargs):
        registry, _ = models.Registry.objects.get_or_create(
            user=info.context.bounced.user, app=info.context.bounced.app
        )
        waiter, _ = models.Waiter.objects.get_or_create(
            registry=registry, identifier=identifier
        )
        print(f"Connected Provisions Waiter for {waiter}")
        return [f"provisions_waiter_{waiter.unique}"]

    def publish(payload, info, *args, **kwargs):
        payload = payload["payload"]
        action = payload["action"]
        data = payload["data"]

        if action == "create":
            return {"create": data}
        else:
            return {"update": data}

    class Meta:
        type = ProvisionsEvent
        operation = "provisions"
