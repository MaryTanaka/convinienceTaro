import discord
import random
from discord.ext import commands
from discord.ext import tasks
from datetime import datetime, timedelta, timezone
import asyncio
import os
import subprocess
import ffmpeg
from voice_generator import creat_WAV

bot = commands.Bot(command_prefix='/')
ID_BOT = 708836631519690784 #BotのID
TOKEN = 'NzA4ODM2NjMxNTE5NjkwNzg0.XrdJ4w.sbJfGgx8IgDCajHshP5qnGlrrls' #TOKEN

GUILD_ID = 602886213686395044 #鯖のID
ID_CHANNEL_VC = 721590762147414116 #VCのチャンネル

ID_CHANNEL = 710122109711417385 #マルチ募集時の投稿チャンネルID
REACTION_PART = '<:dappou:613239014304251921>' #狩る側で参加したい人のリアクション
REACTION_MUST = '✅'

OFFER_TIME = '22:50' #募集時刻
JST = timezone(timedelta(hours=+9), 'JST')
participation = []
must_participation = []

bot.remove_command('help')
voice_client = None
#callChannelID = None

@bot.event
async def on_ready():
    """
    Bot起動処理
    """
    print("便利太郎 起動")

@bot.command()
async def help(ctx):
    if ctx.message.channel.id != ID_CHANNEL:
        return

    embed = discord.Embed(title="便利太郎の使い方", description="便利太郎の使い方は以下の通りです.", color=0xeee657)

    embed.add_field(name="/join", value="VCに便利太郎を召喚するコマンド．\nテキストチャンネルへの投稿を読み上げますが、現状絵文字は読み上げません．", inline=False)
    embed.add_field(name="/bye", value="VCから便利太郎を帰らせるコマンド.", inline=False)   
    embed.add_field(name="/ult", value="任意のタイミングでアルバハ募集をかけるコマンド.\nアルバハは22:50に定期募集されます.", inline=False)
    embed.add_field(name="/pick N", value="自動でN人組を選出し、待機組を別途表示します.\n2組以上作成可能な場合は可能な限り作成します.", inline=False)
    embed.add_field(name="/ls", value="現在参加表明している人のリストをDiscord上に表示します.", inline=False)
    embed.add_field(name="/clear", value="現在参加表明している人のリストを強制的に削除します.")
    embed.add_field(name="その他機能", value="・VCへの接続、移動、退室を通話用チャットへ投稿してくれます")

    await ctx.send(embed=embed)

@tasks.loop(seconds=60)
async def loop():
    """
    60秒毎に呼び出される.
    現在時刻を取得し、設定時刻になるとアルバハ募集メッセージを自動で送信する.

    メッセージ送信前にList: participationおよびmust_participationをclearする.
    (メッセージ送信後のリアクションだけでリストを作るため)

    メッセージ送信後リアクションを自動で2つ付ける(REACTION_PART, REACTION_MUST).
    """

    now = datetime.now(JST).strftime('%H:%M')

    print("TIME: " + now)

    if now == OFFER_TIME:
        today = datetime.now(JST).strftime('%m月%d日分 ')

        channel = bot.get_channel(ID_CHANNEL)
        participation.clear()
        must_participation.clear()
        msg = await channel.send(today + 'アルバハ参加表明 (' + REACTION_PART + ' : 参加, ' + REACTION_MUST + ': 絶対狩る側で参加したい)')

        await msg.add_reaction(REACTION_PART)
        await msg.add_reaction(REACTION_MUST)
       
@bot.command()
async def pick(ctx, arg):
    """
    : 「/pick 人数」で自動選出を行う. リストの人数で作れるだけ組を作ります.
    @input arg: 人数(int)

    @param group_num: 作れる組数
    @param lack_num: must_participationで賄えなかった人数

    @param picked: 狩る人に選出された人
    @param substitute: 待機組リスト

    """
    if ctx.message.channel.id != ID_CHANNEL:
        return

    #補欠リストの作成
    substitute = []
    substitute.clear()
    picked = []
    picked.clear()

    pickup_str = ""
    sub_str = ""

    #SETへ変換して両方リアクションつけた人はREACTION_PARTから除く
    must_participation_set = set(must_participation)
    participation_set = set(participation) - set(must_participation)
    #リストへ戻す
    participation_list = list(participation_set)
    must_participation_list = list(must_participation_set)

    #人数の組が何組作れるかを算出
    group_num = int((len(must_participation_list) + len(participation_list)) / int(arg))

    if (group_num == 0) :
        await ctx.send("人数が足りません")
        return

    #狩る側で必ず参加したい人がグループ数×選出人数を超えた場合
    if len(must_participation_list) > (group_num*int(arg)):
        #participation_listの人は絶対に待機組なのでsubstituteに格納
        substitute.extend(participation_list)

        picked = random.sample(must_participation_list, group_num*int(arg))

        #must_participationで選出されなかった人をsubstituteに格納
        picked_set = set(picked)
        substitute.extend(list(must_participation_set - picked_set))
    else :
        #不足人数の算出
        lack_member = (group_num * int(arg)) - len(must_participation_list)

        #must_participation_listの人は全員参加なのでpickedに追加
        picked.extend(must_participation_list)

        #不足人数分をparticipation_listからランダム選出->pickedに追加, 差分をsubstituteに格納
        rand_pick = random.sample(participation_list, lack_member)
        picked.extend(rand_pick)
        substitute.extend(list(participation_set - set(rand_pick)))

    #狩る人出力部分
    for i in range (0, group_num):
        pickup_str += ("===== " + str(i+1) + "組目 =====" + "\n")
        for j in range (int(arg)):
            pickup_str += (str(j+1) + " : " + str(picked[i*int(arg) + j].name) + "\n")

    #待機組出力部分
    for i in range (len(substitute)):
        if i == 0 :
            sub_str += ("===== 待機組 =====" + "\n")
        sub_str += (str(i+1) + " : " + str(substitute[i].name) + "\n")

    pickup_str += sub_str

    await ctx.send(pickup_str)

@bot.command()
async def join(ctx):
    await ctx.send('おはよう')
    vc = ctx.author.voice.channel
    #callChannelID = ctx.message.channel.id
    await vc.connect()

@bot.command()
async def bye(ctx):
    await ctx.send('おやすみ')
    await ctx.voice_client.disconnect()

@bot.command()
async def ult(ctx):
    """
    : 任意のタイミングでアルバハ募集をかけるコマンド.
    """
    if ctx.message.channel.id != ID_CHANNEL:
        return

    #リストをクリア
    must_participation.clear()
    participation.clear()

    msg = await ctx.send('アルバハ参加表明 (' + REACTION_PART + ' : 参加, ' + REACTION_MUST + ': 絶対狩る側で参加したい)')

    await msg.add_reaction(REACTION_PART)
    await msg.add_reaction(REACTION_MUST)

    print(ctx)

@bot.command()
async def clear(ctx):
    """
    : 現在のリストを強制的に初期化するコマンド.
    """
    if ctx.message.channel.id != ID_CHANNEL:
        return

    must_participation.clear()
    participation.clear()
    await ctx.send('リスト初期化完了')

    print(ctx)

@bot.command()
async def ls(ctx):
    """
    : 現在リストに格納されている人の名前をDiscord上で列挙するコマンド.
    """

    must_list = ""
    part_list = ""

    if ctx.message.channel.id != ID_CHANNEL:
        return

    if must_participation == []:
        await ctx.send('絶対狩るマンのリストは空です')
    else :
        must_list += ("===== 絶対狩るマンのリスト =====\n")
        for i in range(len(must_participation)):
            must_list += (str(i+1) + " : " + must_participation[i].name + "\n")
        await ctx.send(must_list)

    if participation == []:
        await ctx.send('参加はする側のリストは空です')
    else :
        part_list += ('===== 自発するマンのリスト =====\n')
        for i in range(len(participation)):
            part_list += (str(i+1) + " : " + participation[i].name + "\n")
        await ctx.send(part_list)

@bot.event
async def on_reaction_add(reaction, user):
    """
    リアクションがついた際に、そのリアクションをつけた人のuser情報をリストに格納する.
    本当はMessage.idを比較して特定のメッセージについたリアクションだけを判定したいが,
    コンソール上でidが同じでもif文では何故かfalseになってしまったので泣く泣く断念
    """
    if user.bot == True:
        #print("point1")
        return

    #チャンネルIDが規定のIDと異なる場合は拾わない
    channel = bot.get_channel(reaction.message.channel.id)
    if channel.id != ID_CHANNEL:
        #print("point2")
        return


    if str(reaction.emoji) == REACTION_PART:
        #BOTが投稿したメッセージについたリアクションだけ拾う
        if reaction.message.author.id == ID_BOT:
            participation.append(user)
            print('Participation.append!')
    
    if str(reaction.emoji) == REACTION_MUST:
        #BOTが投稿したメッセージについたリアクションだけ拾う
        if reaction.message.author.id == ID_BOT:
            must_participation.append(user)
            print('Must_Participation.append!')

    print('\nParticipation: ')
    print(participation)

    print('\nMust_Participation: ')
    print(must_participation)

@bot.event
async def on_reaction_remove(reaction, user):
    """
    リアクションが外れた際に、そのリアクションを外した人のuser情報をリストから削除する.
    """
    if user.bot == True:
        return

    #チャンネルIDが規定のIDと異なる場合は拾わない
    channel = bot.get_channel(reaction.message.channel.id)
    if channel.id != ID_CHANNEL:
        return

    if str(reaction.emoji) == REACTION_PART:
        #BOTが投稿したメッセージについたリアクションだけ拾う
        if (user in participation) and (reaction.message.author.id == ID_BOT):
            participation.remove(user)
            print('Participation.Removed!')
    
    if str(reaction.emoji) == REACTION_MUST:
        #BOTが投稿したメッセージについたリアクションだけ拾う
        if (user in must_participation) and (reaction.message.author.id == ID_BOT):
            must_participation.remove(user)
            print('Must_Participation.Removed!')

    print('\nParticipation: ')
    print(participation)

    print('\nMust_Participation: ')
    print(must_participation)


@bot.event
async def on_message(message):
    msgclient = message.guild.voice_client
    if message.content.startswith('/'):
        pass
    else:
        if message.guild.voice_client:
            print(message.content)
            creat_WAV(message.content)
            source = discord.FFmpegPCMAudio("open_jtalk.wav")
            message.guild.voice_client.play(source)
        else:
            pass
    await bot.process_commands(message)

@bot.event
async def on_voice_state_update(member, before, after):
    channel = bot.get_channel(ID_CHANNEL_VC)
    if member.guild.id == GUILD_ID and (before.channel != after.channel):
        if before.channel is None:
            msg = await channel.send(member.name + "が [ " + after.channel.name + " ]に参加しました.")
        elif after.channel is None:
            msg = await channel.send(member.name + "が退室しました.")     
        else:
            msg = await channel.send(member.name + "が [ " + before.channel.name + " ] から [ " + after.channel.name + " ]に移動しました.")  


loop.start()
bot.run(TOKEN)