import json
import aiormq
from hare.carrots import (
    HareMessage,
    HareMessageTypes,
    ProvideHareMessage,
    ReserveHareMessage,
    UnassignHareMessage,
    UnreserveHareMessage,
)
from hare.connection import rmq
from hare.consumers.agent.protocols.agent_json import *
import ujson
from arkitekt.console import console
from hare.consumers.agent.base import AgentConsumer
from .helpers import *


class HareAgentConsumer(AgentConsumer):
    """Hare Postman

    Hare is the default Resolver for the Message Layer using rabbitmq
    it inherits the default

    Args:
        PostmanConsumer (_type_): _description_
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.res_queues = {}
        self.res_consumers = {}

    async def connect(self):
        await super().connect()
        self.channel = await rmq.open_channel()

        self.callback_queue = await self.channel.queue_declare(
            self.agent.queue, auto_delete=True
        )

        print(f"Liustenting Agent on '{self.agent.queue}'")
        # Start listening the queue with name 'hello'
        await self.channel.basic_consume(
            self.callback_queue.queue, self.on_rmq_message_in
        )

    async def forward(self, f: HareMessage):
        print(f"Publishing this to {f.queue}")
        await self.channel.basic_publish(
            f.to_message(),
            exchange=f.queue,  # Lets take the first best one
        )

    async def on_rmq_message_in(self, rmq_message: aiormq.abc.DeliveredMessage):
        try:
            json_dict = ujson.loads(rmq_message.body)
            type = json_dict["type"]

            if type == HareMessageTypes.RESERVE:
                await self.on_reserve(ReserveHareMessage(**json_dict))

            if type == HareMessageTypes.UNRESERVE:
                await self.on_unreserve(UnreserveHareMessage(**json_dict))

            if type == HareMessageTypes.PROVIDE:
                await self.on_provide(ProvideHareMessage(**json_dict))

        except Exception as e:
            console.print_exception()

        self.channel.basic_ack(rmq_message.delivery.delivery_tag)

    async def on_list_provisions(self, message: ProvisionList):

        replies, forwards = await list_provisions(message, agent=self.agent)

        for r in replies:
            await self.reply(r)

    async def on_list_assignations(self, message: AssignationsList):

        replies, forwards = await list_assignations(message, agent=self.agent)

        for r in replies:
            await self.reply(r)

    async def on_assignment_in(self, provid, rmq_message):
        replies = []
        forwards = []
        try:
            json_dict = ujson.loads(rmq_message.body)
            type = json_dict["type"]
            if type == HareMessageTypes.ASSIGN:
                m = AssignHareMessage(**json_dict)
                replies, forwards = await bind_assignation(m, provid)

            if type == HareMessageTypes.UNASSIGN:
                m = UnassignHareMessage(**json_dict)
                replies = [UnassignSubMessage(**json_dict)]

        except Exception as e:
            console.print_exception()
        print(f"Received Assignment for {provid} {rmq_message}")

        for r in replies:
            await self.reply(r)

        for r in forwards:
            await self.forward(r)

    async def on_provision_changed(self, message: ProvisionChangedMessage):

        if message.status == ProvisionStatus.ACTIVE:
            replies, forwards, queues = await activate_provision(
                message, agent=self.agent
            )

            for res, queue in queues:
                print(f"Lisenting for queue of Reservation {res}")
                self.res_queues[res] = await self.channel.queue_declare(
                    queue,
                    auto_delete=True,
                )
                print(self.res_queues[res].queue)

                self.res_consumers[res] = await self.channel.basic_consume(
                    self.res_queues[res].queue,
                    lambda aio: self.on_assignment_in(message.provision, aio),
                    consumer_tag=f"{res}-{message.provision}",
                )

        else:
            replies, forwards = await change_provision(message, agent=self.agent)

        for r in forwards:
            await self.forward(r)

        for r in replies:
            await self.reply(r)

    async def on_assignation_changed(self, message: AssignationChangedMessage):

        replies, forwards = await change_assignation(message, agent=self.agent)

        for r in forwards:
            await self.forward(r)

        for r in replies:
            await self.reply(r)

    async def on_reserve(self, message: ReserveHareMessage):

        replies, forwards, reservation_queues = await accept_reservation(
            message, agent=self.agent
        )

        for res, queue in reservation_queues:
            print(f"Lisenting for queue of Reservation {res}")
            self.res_queues[res] = await self.channel.queue_declare(
                queue, auto_delete=True
            )
            print(self.res_queues[res].queue)

            await self.channel.basic_consume(
                self.res_queues[res].queue,
                lambda aio: self.on_assignment_in(message.provision, aio),
                consumer_tag=f"{res}-{message.provision}",
            )

        for r in forwards:
            await self.forward(r)

        for r in replies:
            await self.reply(r)

    async def on_unreserve(self, message: UnreserveHareMessage):

        print("Received Unreserve", message)

        replies, forwards, delete_queue_id = await loose_reservation(
            message, agent=self.agent
        )

        for id in delete_queue_id:
            await self.channel.basic_cancel(f"{id}-{message.provision}")
            print(f"Deleteing for queue {id} of Reservation {message.provision}")

        for r in forwards:
            await self.forward(r)

        for r in replies:
            await self.reply(r)

    async def on_provide(self, message: ProvideHareMessage):
        logger.warning(f"Agent received PROVIDE {message}")

        replies = [
            ProvideSubMessage(
                provision=message.provision,
                template=message.template,
                status=message.status,
            )
        ]

        for r in replies:
            await self.reply(r)

    async def disconnect(self, close_code):
        try:
            logger.warning(f"Disconnecting Postman with close_code {close_code}")
            # We are deleting all associated Provisions for this Agent
            forwards = await disconnect_agent(self.agent, close_code)

            for r in forwards:
                print(r)
                await self.forward(r)

            await self.channel.close()
        except Exception as e:
            logger.error(f"Something weird happened in disconnection! {e}")
