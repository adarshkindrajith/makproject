# chat/consumers.py

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
import json
from .models import CustomUser, Message

from django.contrib.auth import get_user_model

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_group_name = "chat_group"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        history = await self.get_last_messages()
        await self.send(text_data=json.dumps({"type": "chat_history", "messages": history}))


    @database_sync_to_async
    def get_user_by_username(self, username):
        try:
            user = User.objects.get(username=username)
            return {
                "username": user.username,
                "profile_pic": user.profile_picture.url if user.profile_picture else "",
                "badge": user.badge.url if user.badge else "",
                "is_superuser": user.is_superuser,
            }
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def get_message_details(self, message_id):
        try:
            # Use select_related to preload the user to avoid a separate query later
            message = Message.objects.select_related('user').get(id=message_id)
            return {
                "id": message.id,
                "username": message.user.username,
                "content": message.content,
            }
        except Message.DoesNotExist:
            return None


    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        # pin and unpin action
        if data.get("type") == "pin":
            msg_id  = data.get("id")
            pin_it  = data.get("value", True)

            if self.scope["user"].is_superuser:
                await database_sync_to_async(
                    Message.objects.filter(id=msg_id).update
                )(pinned=pin_it)

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type":   "chat_message",
                        "action": "pin",
                        "id":     msg_id,
                        "value":  pin_it,
                    }
                )
            return

        # delete action
        if data.get('type') == 'delete':
            msg_id = data.get('id')

            deleted = await database_sync_to_async(Message.objects.filter(id=msg_id).exists)()
            if not deleted:
                return

            await database_sync_to_async(Message.objects.filter(id=msg_id).delete)()

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'action': 'delete',
                    'id': msg_id,
                }
            )
            return
        
        # report / un-report toggle action
        if data.get("type") == "report":
            msg_id = data.get("id")
            
            # Retrieve the message using database_sync_to_async
            # Use select_related here to ensure user is loaded
            message_obj = await database_sync_to_async(
                lambda: Message.objects.select_related('user').get(id=msg_id)
            )()

            message_obj.reported = not message_obj.reported
            await database_sync_to_async(message_obj.save)()

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message", 
                    "action": "report",
                    "id": msg_id,
                    "reported": message_obj.reported,
                    # Accessing message_obj.user.username is now safe because 'user' was preloaded
                    "username": message_obj.user.username,
                    "profile_pic": message_obj.user.profile_picture.url if message_obj.user.profile_picture else "",
                    "message": message_obj.content,
                    "timestamp": message_obj.timestamp.isoformat(),
                }
            )
            return

        
        # Default: a new chat message action
        username = data["username"]
        message_content = data["message"]
        replied_to_id = data.get("replied_to") 

        user_data = await self.get_user_by_username(username)
        if user_data is None:
            return

        message_obj = await self.store_message(username, message_content, replied_to_id)

        replied_to_data_for_frontend = None
        if message_obj.replied_to: 
            replied_to_data_for_frontend = await self.get_message_details(message_obj.replied_to.id)


        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "id": message_obj.id,
                "username": user_data["username"],
                "message": message_content,
                "profile_pic": user_data["profile_pic"],
                "badge": user_data["badge"],
                'timestamp': message_obj.timestamp.isoformat(),
                "reported": message_obj.reported,
                "action": "message",
                "pinned": message_obj.pinned,
                "replied_to": replied_to_data_for_frontend,
                "is_sender_superuser": user_data.get("is_superuser", False),
            },
        )


    async def chat_message(self, event):
        action = event.get("action", "message")

        if action == "report":
            await self.send(text_data=json.dumps({
                "action": "report",
                "id": event["id"],
                "reported": event["reported"],
                "username": event.get("username"),
                "profile_pic": event.get("profile_pic"),
                "message": event.get("message"),
                "timestamp": event.get("timestamp"),
            }))

        elif action == "pin":
            await self.send(text_data=json.dumps({
                "action": "pin",
                "id": event["id"],
                "value": event["value"],
            }))
        elif action == "delete":
            await self.send(text_data=json.dumps({
                "action": "delete",
                "id": event["id"],
            }))
        else:
            await self.send(text_data=json.dumps({
                "action": "message",
                "id": event["id"],
                "username": event["username"],
                "message": event["message"],
                "profile_pic": event.get("profile_pic", ""),
                "badge": event.get("badge", ""),
                "timestamp": event["timestamp"],
                "pinned": event.get("pinned", False),
                "reported": event.get("reported", False),
                "replied_to": event.get("replied_to", None),
                "is_sender_superuser": event.get("is_sender_superuser", False),
            }))


    @database_sync_to_async         
    def store_message(self, username, content, replied_to_id=None):
        user = User.objects.get(username=username)
        replied_to_message = None
        if replied_to_id:
            try:
                replied_to_message = Message.objects.get(id=replied_to_id)
            except Message.DoesNotExist:
                pass 

        return Message.objects.create(user=user, content=content, replied_to=replied_to_message)

    @database_sync_to_async
    def get_last_messages(self, n=50):
        # Ensure user and replied_to__user are selected related for direct access
        qs = (
            Message.objects.select_related("user", "replied_to__user")
            .order_by("-pinned", "-timestamp")[:n]
        )
        qs = list(reversed(qs))

        messages_data = []
        for m in qs:
            replied_to_info = None
            if m.replied_to:
                replied_to_info = {
                    "id": m.replied_to.id,
                    "username": m.replied_to.user.username, # Safe due to select_related
                    "content": m.replied_to.content,
                }
            messages_data.append({
                "id": m.id,
                "username": m.user.username, # Safe due to select_related
                "profile_pic": m.user.profile_picture.url if m.user.profile_picture else "",
                "badge": m.user.badge.url if m.user.badge else "",
                "message": m.content,
                "timestamp": m.timestamp.isoformat(),
                "pinned": m.pinned,
                "reported": m.reported,
                "replied_to": replied_to_info,
                "is_sender_superuser": m.user.is_superuser, # Safe due to select_related
            })
        return messages_data