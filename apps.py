import discord
from discord import app_commands
from discord.ext import commands
import os
from core.market import MarketClient

APPLICATION_ID = os.getenv("APPLICATION_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

# 테스트용
# GUILD_ID = int(os.getenv("TEST_GUILD_ID"))

intents = discord.Intents.default()
intents.message_content = True


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents.all(),
            sync_command=True,
            application_id=APPLICATION_ID,  # 디스코드 봇의 application id를 입력한다.
        )

    async def setup_hook(self):
        await bot.tree.sync()

    async def on_ready(self):
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print("ready!")

        activity = discord.activity.CustomActivity("문의는 크리스존에게")
        await self.change_presence(status=discord.Status.online, activity=activity)


bot = MyBot()


@bot.tree.command(
    name="유각", description="유각 가격보기", guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(각인명="미입력시 가격순10개")
async def test(interaction: discord.Interaction, 각인명: str = None) -> None:
    client = MarketClient()
    client.get_유각(name=각인명)
    embed = client.get_embed_for_유각()
    await interaction.response.send_message(embed=embed)


bot.run(BOT_TOKEN)
