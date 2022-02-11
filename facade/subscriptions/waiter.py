from facade.enums import ReservationStatus
from graphene.types.scalars import String
from lok import bounced
from balder.types import BalderSubscription
from facade import models, types
import graphene


class WaiterEvent(graphene.ObjectType):
    update = graphene.Field(types.Reservation)
    delete = graphene.Field(graphene.ID)
    create = graphene.Field(types.Reservation)


class WaiterSubscription(BalderSubscription):
    class Arguments:
        identifier = graphene.ID(
            description="The reference of this waiter", required=True
        )

    @bounced(only_jwt=True)
    def subscribe(root, info, *args, identifier=None):
        registry, _ = models.Registry.objects.get_or_create(
            user=info.context.bounced.user, app=info.context.bounced.app
        )
        waiter, _ = models.Waiter.objects.get_or_create(
            registry=registry, identifier=identifier
        )
        print(f"Connected Waiter for {waiter}")
        return [f"waiter_{waiter.unique}"]

    def publish(payload, info, *args, **kwargs):
        payload = payload["payload"]
        action = payload["action"]
        data = payload["data"]
        print("received Payload", payload)

        if action == "delete":
            return {"delete": data}

        if action == "update":
            return {"update": data}

        if action == "create":
            return {"create": data}

        print("error in payload")

    class Meta:
        type = WaiterEvent
        operation = "waiter"