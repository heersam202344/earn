"""
PAGAL Escrow Bot - Telethon Manager
Handles auto group creation, name changes, photo changes via MTProto
"""
import asyncio
import logging
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import (
    CreateChatRequest, EditChatTitleRequest, ExportChatInviteRequest
)
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import InputChatUploadedPhoto, InputPeerUser
from config import API_ID, API_HASH, STRING_SESSION, BOT_USERNAME

logger = logging.getLogger(__name__)

class TelethonManager:
    def __init__(self):
        self.client = None
        self.connected = False

    async def connect(self):
        """Initialize Telethon client with string session"""
        try:
            self.client = TelegramClient(
                StringSession(STRING_SESSION),
                API_ID,
                API_HASH
            )
            await self.client.connect()
            if not await self.client.is_user_authorized():
                logger.error("Telethon session not authorized!")
                return False
            self.connected = True
            me = await self.client.get_me()
            logger.info(f"Telethon connected as {{me.first_name}} (ID: {{me.id}})")
            return True
        except Exception as e:
            logger.error(f"Telethon connection failed: {{e}}")
            return False

    async def create_escrow_group(self, creator_id, escrow_id):
        """
        Creates a new basic group for escrow.
        Returns: (group_id, invite_link) or (None, None)
        """
        if not self.connected:
            logger.error("Telethon not connected")
            return None, None

        try:
            group_title = f"P2P Escrow By PAGAL Bot ({{escrow_id}})"

            # Create basic group with bot
            bot_username_clean = BOT_USERNAME.replace("@", "")
            result = await self.client(CreateChatRequest(
                users=[bot_username_clean],
                title=group_title
            ))

            group = result.chats[0]
            group_id = group.id

            # Add creator to group
            try:
                from telethon.tl.functions.messages import AddChatUserRequest
                await self.client(AddChatUserRequest(
                    chat_id=group_id,
                    user_id=creator_id,
                    fwd_limit=0
                ))
            except Exception as e:
                logger.warning(f"Could not add creator to group: {{e}}")

            # Generate invite link with 2 member limit
            try:
                invite = await self.client(ExportChatInviteRequest(
                    peer=group_id,
                    usage_limit=2
                ))
                invite_link = invite.link
            except Exception as e:
                logger.warning(f"Could not generate invite: {{e}}")
                invite_link = None

            logger.info(f"Created group {{group_id}} for escrow {{escrow_id}}")
            return group_id, invite_link

        except Exception as e:
            logger.error(f"Group creation failed: {{e}}")
            return None, None

    async def change_group_name(self, group_id, new_name):
        """Change group title"""
        if not self.connected:
            return False
        try:
            await self.client(EditChatTitleRequest(
                chat_id=group_id,
                title=new_name
            ))
            return True
        except Exception as e:
            logger.error(f"Name change failed: {{e}}")
            return False

    async def change_group_photo(self, group_id, photo_path):
        """Change group photo"""
        if not self.connected:
            return False
        try:
            from telethon.tl.functions.messages import EditChatPhotoRequest

            uploaded = await self.client.upload_file(photo_path)
            await self.client(EditChatPhotoRequest(
                chat_id=group_id,
                photo=InputChatUploadedPhoto(uploaded)
            ))
            return True
        except Exception as e:
            logger.error(f"Photo change failed: {{e}}")
            return False

    async def pin_message(self, group_id, message_id):
        """Pin a message in the group"""
        if not self.connected:
            return False
        try:
            await self.client.pin_message(group_id, message_id)
            return True
        except Exception as e:
            logger.error(f"Pin failed: {{e}}")
            return False

    async def disconnect(self):
        if self.client:
            await self.client.disconnect()
            self.connected = False

# Singleton instance
telethon_mgr = TelethonManager()
