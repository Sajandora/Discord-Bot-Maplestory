import discord
from discord.ext import commands  # commands 사용
import requests
import math
from datetime import datetime, timedelta, timezone
import asyncio
import sys

# 디스코드 봇 토큰
# 발급받은 토큰을 입력해주세요
TOKEN = ''

# 환경에 맞는 SelectorEventLoop 설정 (Windows 경우)
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# 인텐트 설정
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # 메시지 내용 확인을 위한 인텐트

# 봇 생성 (command_prefix로 접두사 설정)
bot = commands.Bot(command_prefix='!', intents=intents)

# MapleStory API URL
API_URL = "https://api.meaegi.com/api/maplestory/token-exchange/all"

# KST 타임존 설정
KST = timezone(timedelta(hours=9))

# 서버명 및 티어명 리스트 정의
valid_worlds = ['일반', '리부트']
valid_grades = ['브론즈', '실버', '골드', '다이아']

# 한글을 영어로 변환하는 매핑
grade_map = {
    '브론즈': 'bronze',
    '실버': 'silver',
    '골드': 'gold',
    '다이아': 'diamond'
}

world_map = {
    '일반': 'normal',
    '리부트': 'reboot'
}

# 봇이 준비되었을 때 호출
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# 메소 판매 시 얻는 메포값 계산 함수
def calculate_meso_to_maplepoint(price):
    price_float = float('0.' + str(price))  # price를 소수로 변환
    return math.ceil(1145 / price_float)  # 메포값 계산 후 반올림

# API 최신화 안내 메시지 확인 함수
def check_api_update_time():
    current_time = datetime.now(KST).time()
    if current_time >= datetime(1, 1, 1, 7, 0).time() and current_time <= datetime(1, 1, 1, 10, 9).time():
        return "**⚠️ 안내:** API는 오전 10시 10분에 최신화됩니다. 현재 제공되는 데이터는 전날의 데이터일 수 있습니다.\n\n"
    return ""

# 교환 정보 임베드 생성 함수
def create_embed(info, maplepoint_value, alert_message):
    embed = discord.Embed(
        title=f"{info['world']} 월드 {info['name']} 등급 토큰 교환 정보",
        description=f"{alert_message}**손익 계산값**\n{maplepoint_value:,}\n\n@@손익 계산값보다 메포값이 낮으면 손해@@",
        color=discord.Color.blue()  # 기본 색상
    )
    # 구분선을 추가
    embed.add_field(name="\u200B", value="------------", inline=False)
    embed.add_field(name="날짜", value=info['date'], inline=False)
    embed.add_field(name="가격", value=f"{info['price']:,} 메소", inline=False)
    embed.set_footer(text="Data by 메애기 (https://meaegi.com)")
    return embed

# 이미지 첨부 함수
def add_images(embed, grade, world):
    grade_image = f"./name/{grade}.png"
    world_image = f"./world/{world}.png"
    embed.set_thumbnail(url=f"attachment://{grade}.png")
    embed.set_image(url=f"attachment://{world}.png")
    return [
        discord.File(grade_image, filename=f"{grade}.png"),
        discord.File(world_image, filename=f"{world}.png")
    ]

# API 요청 함수
def fetch_api_data():
    headers = {'Cache-Control': 'no-cache'}
    response = requests.get(API_URL, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

# 모든 서버, 모든 티어 출력 함수
async def send_all_data(ctx, data):
    embed = discord.Embed(title="모든 서버의 토큰 교환 정보", color=discord.Color.green())
    for item in data:
        maplepoint_value = calculate_meso_to_maplepoint(item['price'])
        embed.add_field(
            name=f"{item['world']} 월드 {item['name']} 등급",
            value=f"**손익 계산값**\n{maplepoint_value:,}",
            inline=False
        )
        # 구분선을 추가
        embed.add_field(name="\u200B", value="-----", inline=False)
        embed.add_field(name="날짜", value=item['date'], inline=False)
        embed.add_field(name="가격", value=f"{item['price']:,} 메소", inline=False)
    embed.set_footer(text="**손익 계산보다 메포값이 낮으면 손해\n\nData by 메애기 (https://meaegi.com)**")
    await ctx.send(embed=embed)

# 특정 서버의 모든 티어 출력 함수
async def send_server_data(ctx, data, world):
    embed = discord.Embed(title=f"{world} 서버의 토큰 교환 정보", color=discord.Color.green())
    for item in data:
        if item['world'].lower() == world.lower():
            maplepoint_value = calculate_meso_to_maplepoint(item['price'])
            embed.add_field(
                name=f"{item['name']} 등급",
                value=f"**손익 계산값**\n{maplepoint_value:,}",
                inline=False
            )
            # 구분선을 추가
            embed.add_field(name="\u200B", value="-----", inline=False)
            embed.add_field(name="날짜", value=item['date'], inline=False)
            embed.add_field(name="가격", value=f"{item['price']:,} 메소", inline=False)
    embed.set_footer(text="**손익 계산보다 메포값이 낮으면 손해\n\nData by 메애기 (https://meaegi.com)**")
    await ctx.send(embed=embed)

# !maple 일반 골드 처리 함수
async def maple_general_gold(ctx):
    try:
        alert_message = check_api_update_time()
        data = fetch_api_data()
        if data:
            matching_data = [item for item in data if item['world'].lower() == '일반' and item['name'].lower() == '골드']
            if matching_data:
                info = matching_data[0]
                maplepoint_value = calculate_meso_to_maplepoint(info['price'])
                embed = create_embed(info, maplepoint_value, alert_message)
                files = add_images(embed, 'gold', 'normal')
                await ctx.send(embed=embed, files=files)
            else:
                await ctx.send("일반 월드의 골드 등급 토큰 정보를 찾을 수 없습니다.")
        else:
            await ctx.send("API 요청에 실패했습니다.")
    except Exception as e:
        await ctx.send(f"오류 발생: {str(e)}")
        print(f"오류 발생: {e}")

# !가격 명령어 처리
@bot.command()
async def 가격(ctx):
    await maple_general_gold(ctx)

# !주화 명령어 처리
@bot.command()
async def 주화(ctx):
    await maple_general_gold(ctx)

# !손익 명령어 처리
@bot.command()
async def 손익(ctx):
    await maple_general_gold(ctx)

# !maple 명령어 처리
@bot.command()
async def maple(ctx, world: str = None, grade: str = None):
    if world and world not in valid_worlds:
        await ctx.send(f"오류: '{world}'는 유효한 서버명이 아닙니다.")
        return
    if grade and grade not in valid_grades:
        await ctx.send(f"오류: '{grade}'는 유효한 티어명이 아닙니다.")
        return

    try:
        alert_message = check_api_update_time()
        data = fetch_api_data()

        if data:
            if not world and not grade:
                await send_all_data(ctx, data)
            elif world and not grade:
                await send_server_data(ctx, data, world)
            else:
                matching_data = [item for item in data if item['world'].lower() == world.lower() and item['name'].lower() == grade.lower()]
                if matching_data:
                    info = matching_data[0]
                    maplepoint_value = calculate_meso_to_maplepoint(info['price'])
                    embed = create_embed(info, maplepoint_value, alert_message)
                    files = add_images(embed, grade_map[grade], world_map[world])
                    await ctx.send(embed=embed, files=files)
                else:
                    await ctx.send(f"{world} 월드의 {grade} 등급 토큰 정보를 찾을 수 없습니다.")
        else:
            await ctx.send("API 요청에 실패했습니다.")
    except Exception as e:
        await ctx.send(f"오류 발생: {str(e)}")
        print(f"오류 발생: {e}")

# 봇 실행
bot.run(TOKEN)
