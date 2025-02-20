import asyncio
import discord
import yt_dlp as youtube_dl
import re
from discord.ext import commands
from discord import app_commands


# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ""

# YouTube DL 설정 옵션
ytdl_format_options = {
    "format": "bestaudio/best",  # 최상의 오디오 품질 선택
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",  # 출력 파일 이름 형식
    "restrictfilenames": True,  # 파일 이름 제한
    "noplaylist": True,  # 플레이리스트 다운로드 방지
    "nocheckcertificate": True,  # 인증서 확인 건너뛰기
    "ignoreerrors": False,  # 오류 무시하지 않음
    "logtostderr": False,  # 표준 오류로 로그 출력하지 않음
    "quiet": True,  # 자세한 출력 억제
    "no_warnings": True,  # 경고 메시지 숨김
    "default_search": "auto",  # 자동 검색 모드
    "source_address": "0.0.0.0",  # IPv4 주소 바인딩
}

# FFmpeg 설정 옵션
ffmpeg_options = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",  # 연결 끊김 시 재연결 설정
    "options": "-vn",  # 비디오 스트림 비활성화
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    """YouTube 다운로더 소스 클래스"""

    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get("title")  # 영상 제목
        self.url = data.get("url")  # 스트리밍 URL
        self.youtube_url = data.get("youtube_url")  # 원본 YouTube URL

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        """URL로부터 오디오 소스 생성"""
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream)
        )
        data["youtube_url"] = url

        if "entries" in data:  # 플레이리스트인 경우 첫 번째 항목 선택
            data = data["entries"][0]

        filename = data["url"] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Music(commands.Cog):
    """음악 재생 명령어 Cog"""

    def __init__(self, bot):
        self.bot = bot
        self.queue = asyncio.Queue()  # 재생 대기열
        self.current = None  # 현재 재생 중인 곡
        self.is_playing = False  # 재생 상태

    @app_commands.command(name="입장", description="크리스존봇 입장")
    async def join(self, interaction: discord.Interaction):
        """음성 채널 입장 (= !입장)"""

        if interaction.user.voice and interaction.user.voice.channel:
            channel = interaction.user.voice.channel
            await interaction.response.send_message(
                "봇이 {0.user.voice.channel} 채널에 입장합니다.".format(interaction)
            )
            await channel.connect()
            print("음성 채널 정보: {0.user.voice}".format(interaction))
            print("음성 채널 이름: {0.user.voice.channel}".format(interaction))
        else:
            await interaction.response.send_message(
                "음성 채널에 유저가 존재하지 않습니다. 1명 이상 입장해 주세요."
            )

    @app_commands.command(name="재생", description="노래재생")
    @app_commands.describe(url="재생할 유튜브 URL 입력")
    async def play(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()
        if interaction.guild.voice_client is None:
            if interaction.user.voice and interaction.user.voice.channel:
                channel = interaction.user.voice.channel
                await channel.connect()
            else:
                await interaction.response.send_message(
                    "음성 채널에 유저가 존재하지 않습니다. 1명 이상 입장해 주세요."
                )

        """대기열(큐)에 노래 추가 & 노래가 없으면 최근 노래 재생 (= !재생)"""
        discord.opus.load_opus("libopus.dylib")
        player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
        if player is None:
            await interaction.response.send_message(
                "노래를 가져오는데 문제 발생. URL을 확인해주세요."
            )
            return

        await self.queue.put(player)
        position = self.queue.qsize()
        if self.is_playing:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title=f"{player.title}, #{position}번째로 대기열에 추가.",
                    color=0x00F44C,
                )
            )

        # 현재 노래가 재생 중이 아니면 다음 곡 재생
        if not self.is_playing and not interaction.guild.voice_client.is_paused():
            await self.play_next(interaction)

    async def play_next(self, interaction: discord.Interaction):
        """다음 곡 재생 처리"""
        if not self.queue.empty():
            self.current = await self.queue.get()
            self.is_playing = True
            interaction.guild.voice_client.play(
                self.current,
                after=lambda e: self.bot.loop.create_task(
                    self.play_next_after(interaction, e)
                ),
            )
            interaction.guild.voice_client.source.volume = (
                10 / 100
            )  # 기본 볼륨 10%로 설정
            youtube_id = await self.get_youtube_id(self.current.youtube_url)
            thumbnail = (
                f"https://img.youtube.com/vi/{youtube_id}/0.jpg"  # 썸네일 URL 생성
            )
            embed = discord.Embed(
                title=f"🎧 노래재생 - {self.current.title}", color=0x00F44C
            )
            embed.set_image(url=thumbnail)
            await interaction.followup.send(embed=embed)
        else:
            self.current = None
            self.is_playing = False
            embed = discord.Embed(
                title="🎧 재생목록이 비어있어서 퇴장합니다.", color=0x00F44C
            )
            await interaction.guild.voice_client.disconnect(force=True)

    async def get_youtube_id(self, url):
        """YouTube URL에서 영상 ID 추출"""
        id_regex = r"(?:youtu\.be\/|youtube\.com\/(?:watch\?v=|embed\/|v\/|shorts\/))([^#&?]{11})"
        return re.search(id_regex, url).group()[-11:]

    async def play_next_after(self, interaction, error):
        if error:
            print(f"에러: {error}")
        self.is_playing = False
        await self.play_next(interaction)

    @app_commands.command(name="스킵", description="현재 재생중인 노래 스킵")
    async def skip(self, interaction: discord.Interaction):
        """현재 재생중인 노래 스킵 (= !스킵)"""
        if (
            interaction.guild.voice_client
            and interaction.guild.voice_client.is_playing()
        ):
            interaction.guild.voice_client.stop()
            embed = discord.Embed(title="🎧 현재 노래를 건너뜁니다.", color=0x00F44C)
            await interaction.response.send_message(embed=embed)
            await self.play_next(interaction)
        else:
            embed = discord.Embed(
                title="🎧 현재 재생 중인 노래가 없습니다.", color=0x00F44C
            )
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="볼륨", description="볼륨 크기 조절")
    @app_commands.describe(크기="원하는 볼륨 크기")
    async def volume(self, interaction: discord.Interaction, 크기: int):
        """볼륨 조정 (불완전함) 사용법: !volume 50 (= !볼륨 50)"""
        if interaction.user.voice and interaction.user.voice.channel:
            if interaction.guild.voice_client and interaction.guild.voice_client.source:
                interaction.guild.voice_client.source.volume = 크기 / 100
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title=f"🔊 스피커 음량을 {크기}%로 변경", color=0x00F44C
                    )
                )
            else:
                await interaction.response.send_message(
                    "No audio is currently playing."
                )
        else:
            return await interaction.response.send_message("음성 채널과 연결 불가능")

    @app_commands.command(name="퇴장", description="크리스존봇 퇴장")
    async def stop(
        self,
        interaction: discord.Interaction,
    ):
        """음성 채널 퇴장 (= !퇴장)"""

        self.queue = asyncio.Queue()
        if (
            interaction.guild.voice_client
            and interaction.guild.voice_client.is_playing()
        ):
            interaction.guild.voice_client.stop()

        await interaction.response.send_message(
            embed=discord.Embed(title="크리스존봇이 퇴장합니다... 떼잉", color=0x00F44C)
        )
        await interaction.guild.voice_client.disconnect(force=True)

    @app_commands.command(name="일시정지", description="노래 일시정지")
    async def pause(
        self,
        interaction: discord.Interaction,
    ):
        """음악을 일시정지 (= !일시정지)"""
        if (
            interaction.guild.voice_client.is_paused()
            or not interaction.guild.voice_client.is_playing()
        ):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="음악이 이미 일시 정지 중이거나 재생 중이지 않습니다.",
                    color=0x00F44C,
                )
            )
        else:
            interaction.guild.voice_client.pause()
            await interaction.response.send_message(
                embed=discord.Embed(title="음악이 일시 정지되었습니다.", color=0x00F44C)
            )

    @app_commands.command(name="다시재생", description="노래 다시 재생")
    async def resume(
        self,
        interaction: discord.Interaction,
    ):
        """일시정지된 음악을 다시 재생 (= !다시재생)"""
        if (
            interaction.guild.voice_client.is_playing()
            or not interaction.guild.voice_client.is_paused()
        ):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="음악이 이미 재생 중이거나 재생할 음악이 존재하지 않습니다.",
                    color=0x00F44C,
                )
            )
        else:
            interaction.guild.voice_client.resume()
            await interaction.response.send_message(
                embed=discord.Embed(title="음악이 다시 재생됩니다.", color=0x00F44C)
            )

    @app_commands.command(name="플리", description="노래 플레이리스트")
    async def playlist(
        self,
        interaction: discord.Interaction,
    ):
        """대기열(큐) 목록 출력 (= !플리)"""
        if not self.queue.empty():
            embed = discord.Embed(title="플레이리스트", color=0x00F44C)
            temp_queue = list(self.queue._queue)
            embed_string = ""
            for idx, player in enumerate(temp_queue, start=1):
                embed_string += f"{idx}. {player.title}\n"
            embed.add_field(name="", value=embed_string)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(
                embed=discord.Embed(title="대기열이 비어 있습니다.", color=0x00F44C)
            )

    @app_commands.command(name="삭제", description="노래 대기열 삭제")
    @app_commands.describe(n번째="몇번째 노래를 삭제할지")
    async def remove(self, interaction: discord.Interaction, n번째: int):
        """대기열(큐)에 있는 곡 삭제. 사용법: !remove 1 (= !삭제 1)"""
        if not self.queue.empty():
            temp_queue = list(
                self.queue._queue
            )  # Convert the queue to a list to access it
            if 0 < n번째 <= len(temp_queue):
                removed = temp_queue.pop(n번째 - 1)
                await interaction.response.send_message(f"삭제: {removed.title}")
                # Rebuild the queue
                self.queue = asyncio.Queue()
                for item in temp_queue:
                    await self.queue.put(item)
            else:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="유효한 번호를 입력하세요.", color=0x00F44C
                    )
                )
        else:
            await interaction.response.send_message(
                embed=discord.Embed(title="대기열이 비어 있습니다.", color=0x00F44C)
            )
