from facade.enums import PodStatus
from facade.models import AppProvider, Provider, Template, Pod, Provision
from facade import types
from balder.types import BalderMutation
import graphene
from herre import bounced

class Accept(BalderMutation):
    """ Accepting is a way for a provider to create a pod, this can be instatiated through a provision or simply
    through providing a template"""

    class Arguments:
        template = graphene.ID(required=True, description="The Template you are giving an implementation for!")
        provision = graphene.String(required=True, description="The Provision we need")

    @bounced(only_jwt=True)
    def mutate(root, info, template=None, provision=None):
        provider, created = AppProvider.objects.update_or_create(client_id=info.context.bounced.client_id, user=info.context.bounced.user , defaults = {
            "name": info.context.bounced.app_name + " " + info.context.bounced.user.username
        })

        provision = Provision.objects.get(reference=provision)

        pod = Pod.objects.create(**{
                "template_id": template,
                "status": PodStatus.PENDING,
                "created_by": provision
            }
        )
        pod.save()

        print(pod)

        return pod


    class Meta:
        type = types.Pod