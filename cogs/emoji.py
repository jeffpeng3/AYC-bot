from discord import ApplicationContext, HTTPException, Message, Bot
from discord.ext.commands import Cog
from discord.commands import SlashCommandGroup
from json import dump,load

class emoji(Cog):
    emoji_command_group = SlashCommandGroup('emoji',"設定自動反應的表情")
    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        with open('data/emoji.json','r',encoding='utf-8') as f:
            self.emoji_map:dict = load(f)


    @Cog.listener("on_message")
    async def on_message(self, message: Message) -> None:
        react=self.emoji_map.get(f'{message.author.id}',None)
        if react:
            try:
                await message.add_reaction(react)
            except HTTPException as e:
                print(message.author.id,message.author.display_name,e)

    @emoji_command_group.command(name='query',description='查詢現在使用的表情')
    async def query(self,ctx:ApplicationContext) -> None:
        react=self.emoji_map.get(str(ctx.author.id),None)
        if react:
            await ctx.respond(f'你現在使用的表情是 : {react}',ephemeral=True)
        else:
            await ctx.respond('你現在沒有正在使用的表情',ephemeral=True)

    @emoji_command_group.command(name='set',description='設定要自動反應的表情')
    async def set(self,ctx:ApplicationContext,react:str) -> None:
        self.emoji_map[str(ctx.author.id)] = react
        await ctx.respond(f'你使用的表情已設定為 : {react}',ephemeral=True)
        with open('data/emoji.json','w',encoding='utf-8') as f:
            dump(self.emoji_map,f,ensure_ascii=False,indent=4)

    @emoji_command_group.command(name='unset',description='取消要自動反應的表情')
    async def un_set(self,ctx:ApplicationContext) -> None:
        if str(ctx.author.id) not in self.emoji_map:
            await ctx.respond('你現在沒有正在使用的表情',ephemeral=True)
            return
        del self.emoji_map[str(ctx.author.id)]
        await ctx.respond('已刪除你使用的表情',ephemeral=True)
        with open('data/emoji.json','w',encoding='utf-8') as f:
            dump(self.emoji_map,f,ensure_ascii=False,indent=4)

def setup(bot: Bot):
    bot.add_cog(emoji(bot))
