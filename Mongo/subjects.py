import os
import typing
from dataclasses import dataclass

import discord.utils
from discord import Role, Guild
from discord import TextChannel
from discord.ext.commands import Bot

from Mongo.mongocollection import MongoCollection, MongoDocument


@dataclass(frozen=True)
class Subject(MongoDocument):
    _id: int
    chat: TextChannel
    role: Role

    @property
    def role_name(self):
        return self.role.name

    @property
    def role_id(self):
        return self.role.id

    @property
    def channel_id(self):
        return self.chat.id

    @property
    def document(self) -> dict[str: typing.Any]:
        return {
            "_id": self._id,
            "channelID": self.chat.id,
            "roleID": self.role.id
        }


class Subjects(MongoCollection):
    def __init__(self, bot: Bot):
        super().__init__(os.environ["DB_NAME"], self.__class__.__name__)
        self.bot = bot

    def __contains__(self, item):
        raise NotImplementedError("Use await contains() instead!")

    async def contains(self, subject: Subject) -> bool:
        return True if await self.find_one(subject.document) else False

    async def _create_subject(self, result):
        guild: Guild = self.bot.guilds[0]
        _id = result["_id"]
        chat = await self.bot.fetch_channel(int(result["channelID"]))
        role: Role = discord.utils.get(guild.roles, id=result["roleID"])
        subject = Subject(_id, chat, role)
        return subject

    async def insert_one(self, entry: tuple[TextChannel, Role]) -> Subject:
        chat, role = entry
        document = {
            "channelID": chat.id,
            "roleID": role.id
        }
        await self.collection.insert_one(document)
        return await self.find_one(document)

    async def find_one(self, find_params: dict) -> Subject:
        result = await self.collection.find_one(find_params)
        return await self._create_subject(result)

    async def find(self, find_params: dict, sort: dict = None, limit: int = None) -> list[Subject]:
        if sort:
            cursor = self.collection.find(find_params).sort(self)
        else:
            cursor = self.collection.find(find_params)

        return [await self._create_subject(entry) for entry in await cursor.to_list(limit)]

    async def update_one(self, find_params: dict, replace: dict) -> Subject:
        await self.collection.update_one(find_params, {"$set": replace})
        document = find_params.copy()
        document.update(replace)
        return await self.find_one(document)
