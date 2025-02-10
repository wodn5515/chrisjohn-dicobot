import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
from core.market import MarketClient
from core.spec import SpecClient
import time

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
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))

    async def on_ready(self):
        print("ready!")
        # await send_message_in_loop.start()

        activity = discord.activity.CustomActivity("문의는 크리스존에게")
        await self.change_presence(status=discord.Status.online, activity=activity)


bot = MyBot()


@bot.tree.command(
    name="거래소", description="거래소 검색", guild=discord.Object(id=GUILD_ID)
)
async def market(interaction: discord.Interaction) -> None:
    # market_categories = []
    pass


# @tasks.loop(seconds=10)  # your timer
# async def send_message_in_loop():
#     print("PING")
#     time.sleep(5)
#     print("PONG")


@bot.tree.command(
    name="군장검사", description="군장검사하기", guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(캐릭터명="필수")
async def spec_check(interaction: discord.Interaction, 캐릭터명: str) -> None:
    # client = SpecClient(name=캐릭터명)
    await interaction.response.send_message(content="준비중입니다.", ephemeral=True)


@bot.tree.command(
    name="유각", description="유각 가격보기", guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(각인명="미입력시 가격순10개")
async def test(interaction: discord.Interaction, 각인명: str = None) -> None:
    client = MarketClient()
    client.get_유각(name=각인명)
    embed = client.get_embed()
    await interaction.response.send_message(embed=embed)


bot.run(BOT_TOKEN)
