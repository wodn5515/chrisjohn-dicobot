import asyncio
import discord
import yt_dlp as youtube_dl
import re
from discord.ext import commands


# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ""

ytdl_format_options = {
    "format": "bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get("title")
        self.url = data.get("url")
        self.youtube_url = data.get("youtube_url")

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream)
        )
        data["youtube_url"] = url

        if "entries" in data:
            data = data["entries"][0]

        filename = data["url"] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = asyncio.Queue()
        self.current = None
        self.is_playing = False

    @commands.command(aliases=["입장"])
    async def join(self, ctx):
        """음성 채널 입장 (= !입장)"""

        if ctx.author.voice and ctx.author.voice.channel:
            channel = ctx.author.voice.channel
            await ctx.send(
                "봇이 {0.author.voice.channel} 채널에 입장합니다.".format(ctx)
            )
            await channel.connect()
            print("음성 채널 정보: {0.author.voice}".format(ctx))
            print("음성 채널 이름: {0.author.voice.channel}".format(ctx))
        else:
            await ctx.send(
                "음성 채널에 유저가 존재하지 않습니다. 1명 이상 입장해 주세요."
            )

    @commands.command(aliases=["재생"])
    async def play(self, ctx, *, url):
        """대기열(큐)에 노래 추가 & 노래가 없으면 최근 노래 재생 (= !재생)"""
        discord.opus.load_opus("libopus.dylib")
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            if player is None:
                await ctx.send("노래를 가져오는데 문제 발생. URL을 확인해주세요.")
                return

            await self.queue.put(player)
            position = self.queue.qsize()
            if self.is_playing:
                await ctx.message.delete()
                await ctx.send(
                    embed=discord.Embed(
                        title=f"{player.title}, #{position}번째로 대기열에 추가.",
                        color=0x00F44C,
                    )
                )

            # 현재 노래가 재생 중이 아니면 다음 곡 재생
            if not self.is_playing and not ctx.voice_client.is_paused():
                await self.play_next(ctx)

    async def play_next(self, ctx):
        if not self.queue.empty():
            self.current = await self.queue.get()
            print(self.current.youtube_url)
            self.is_playing = True
            ctx.voice_client.play(
                self.current,
                after=lambda e: self.bot.loop.create_task(self.play_next_after(ctx, e)),
            )
            ctx.voice_client.source.volume = 10 / 100
            youtube_id = await self.get_youtube_id(self.current.youtube_url)
            thumbnail = f"https://img.youtube.com/vi/{youtube_id}/0.jpg"
            await ctx.message.delete()
            embed = discord.Embed(
                title=f"🎧 노래재생 - {self.current.title}", color=0x00F44C
            )
            embed.set_image(url=thumbnail)
            await ctx.send(embed=embed)
        else:
            self.current = None
            self.is_playing = False
            embed = discord.Embed(
                title="🎧 재생목록이 비어있어서 퇴장합니다.", color=0x00F44C
            )
            ctx.send(embed=embed)
            await ctx.voice_client.disconnect()

    async def get_youtube_id(self, url):
        id_regex = r"(?:youtu\.be\/|youtube\.com\/(?:watch\?v=|embed\/|v\/|shorts\/))([^#&?]{11})"
        return re.search(id_regex, url).group()[-11:]

    async def play_next_after(self, ctx, error):
        if error:
            print(f"에러: {error}")
        self.is_playing = False
        await self.play_next(ctx)

    @commands.command(aliases=["스킵"])
    async def skip(self, ctx):
        """현재 재생중인 노래 스킵 (= !스킵)"""
        await ctx.message.delete()
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            embed = discord.Embed(
                title="🎧 현재 노래를 건너뜁니다.", color=0x00F44C
            )
            await ctx.send(embed=embed)
            await self.play_next(ctx)
        else:
            embed = discord.Embed(
                title="🎧 현재 재생 중인 노래가 없습니다.", color=0x00F44C
            )
            await ctx.send(embed=embed)

    @commands.command(aliases=["볼륨"])
    async def volume(self, ctx, volume: int):
        """볼륨 조정 (불완전함) 사용법: !volume 50 (= !볼륨 50)"""
        await ctx.message.delete()
        if ctx.author.voice and ctx.author.voice.channel:
            if ctx.voice_client and ctx.voice_client.source:
                ctx.voice_client.source.volume = volume / 100
                await ctx.send(
                    embed=discord.Embed(title=f"🔊 스피커 음량을 {volume}%로 변경", color=0x00F44C)
                )
            else:
                await ctx.send("No audio is currently playing.")
        else:
            return await ctx.send("음성 채널과 연결 불가능")

    @commands.command(aliases=["퇴장"])
    async def stop(self, ctx):
        """음성 채널 퇴장 (= !퇴장)"""

        self.queue = asyncio.Queue()
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()

        await ctx.message.delete()
        await ctx.send(
            embed=discord.Embed(title="크리스존봇이 퇴장합니다... 떼잉", color=0x00F44C)
        )
        await ctx.voice_client.disconnect()

    @commands.command(aliases=["일시정지"])
    async def pause(self, ctx):
        """음악을 일시정지 (= !일시정지)"""
        if ctx.voice_client.is_paused() or not ctx.voice_client.is_playing():
            await ctx.send("음악이 이미 일시 정지 중이거나 재생 중이지 않습니다.")
        else:
            ctx.voice_client.pause()
            await ctx.send("음악이 일시 정지되었습니다.")

    @commands.command(aliases=["다시재생"])
    async def resume(self, ctx):
        """일시정지된 음악을 다시 재생 (= !다시재생)"""
        if ctx.voice_client.is_playing() or not ctx.voice_client.is_paused():
            await ctx.send("음악이 이미 재생 중이거나 재생할 음악이 존재하지 않습니다.")
        else:
            ctx.voice_client.resume()
            await ctx.send("음악이 다시 재생됩니다.")

    @commands.command(aliases=["플리"])
    async def playlist(self, ctx):
        """대기열(큐) 목록 출력 (= !플리)"""
        if not self.queue.empty():
            embed = discord.Embed(title="플레이리스트", color=0x00F44C)
            temp_queue = list(self.queue._queue)
            embed_string = ""
            for idx, player in enumerate(temp_queue, start=1):
                embed_string += f"{idx}. {player.title}\n"
            embed.add_field(name="", value=embed_string)
            await ctx.message.delete()
            await ctx.send(embed=embed)
        else:
            await ctx.message.delete()
            await ctx.send(
                embed=discord.Embed(title="대기열이 비어 있습니다.", color=0x00F44C)
            )

    @commands.command(aliases=["삭제"])
    async def remove(self, ctx, index: int):
        """대기열(큐)에 있는 곡 삭제. 사용법: !remove 1 (= !삭제 1)"""
        if not self.queue.empty():
            temp_queue = list(
                self.queue._queue
            )  # Convert the queue to a list to access it
            if 0 < index <= len(temp_queue):
                removed = temp_queue.pop(index - 1)
                await ctx.send(f"삭제: {removed.title}")
                # Rebuild the queue
                self.queue = asyncio.Queue()
                for item in temp_queue:
                    await self.queue.put(item)
            else:
                await ctx.send("유효한 번호를 입력하세요.")
        else:
            await ctx.send("대기열이 비어 있습니다.")

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if not (ctx.author.voice and ctx.author.voice.channel):
            await ctx.send("You are not connected to a voice channel.")
            raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
