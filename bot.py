import os
import json
import discord
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')
IMAGE_PATH = os.path.join(BASE_DIR, 'images', 'welcome_background.png')

with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    cfg = json.load(f)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)


def save_config():
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def build_welcome_embed(member: discord.Member) -> discord.Embed:
    embed = discord.Embed(
        title='⚔️ BROTHERHOOD',
        description=(
            f'**Seja bem-vindo, {member.mention}!**\n\n'
            'Seu caminho na Brotherhood começa agora.\n\n'
            '❄️ Leia as regras\n'
            '🛡️ Escolha seus cargos\n'
            '⚔️ Prepare-se para as raids'
        ),
        color=0x9ED8FF
    )
    embed.set_image(url='attachment://brotherhood_welcome.png')
    embed.set_footer(text=f'Membro #{member.guild.member_count} • Brotherhood')
    return embed


async def send_welcome(channel: discord.TextChannel, member: discord.Member):
    # A mesma imagem fixa é enviada para todos os membros.
    file = discord.File(IMAGE_PATH, filename='brotherhood_welcome.png')
    embed = build_welcome_embed(member)
    await channel.send(embed=embed, file=file)


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f'Online como {bot.user} | {len(synced)} comandos sincronizados')
    except Exception as exc:
        print(f'Erro ao sincronizar comandos: {exc}')


@bot.event
async def on_member_join(member: discord.Member):
    channel_id = int(cfg.get('welcome_channel_id', 0) or 0)
    if not channel_id:
        return

    channel = member.guild.get_channel(channel_id)
    if not isinstance(channel, discord.TextChannel):
        return

    try:
        await send_welcome(channel, member)
    except Exception as exc:
        print(f'Erro ao enviar boas-vindas: {exc}')


@bot.tree.command(name='configwelcome', description='Define o canal de boas-vindas da Brotherhood')
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(canal='Canal onde as boas-vindas serão enviadas')
async def configwelcome(interaction: discord.Interaction, canal: discord.TextChannel):
    cfg['welcome_channel_id'] = canal.id
    save_config()
    await interaction.response.send_message(
        f'✅ Canal de boas-vindas definido para {canal.mention}.\n'
        'A imagem fixa da Brotherhood será usada para todos os novos membros.',
        ephemeral=True
    )


@bot.tree.command(name='testwelcome', description='Testa a mensagem de boas-vindas neste canal')
@app_commands.checks.has_permissions(administrator=True)
async def testwelcome(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        file = discord.File(IMAGE_PATH, filename='brotherhood_welcome.png')
        embed = build_welcome_embed(interaction.user)
        await interaction.channel.send(embed=embed, file=file)
        await interaction.followup.send('✅ Teste enviado neste canal.', ephemeral=True)
    except Exception as exc:
        await interaction.followup.send(f'❌ Não foi possível enviar o teste: `{exc}`', ephemeral=True)


@bot.tree.command(name='statuswelcome', description='Mostra a configuração atual das boas-vindas')
@app_commands.checks.has_permissions(administrator=True)
async def statuswelcome(interaction: discord.Interaction):
    channel_id = int(cfg.get('welcome_channel_id', 0) or 0)
    channel = interaction.guild.get_channel(channel_id) if channel_id else None
    channel_text = channel.mention if channel else 'Não configurado'
    await interaction.response.send_message(
        f'⚔️ **Brotherhood — Boas-vindas**\n\n'
        f'Canal: {channel_text}\n'
        f'Imagem: `welcome_background.png` (fixa para todos)\n'
        f'Bot: {"online" if bot.is_ready() else "offline"}',
        ephemeral=True
    )


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.MissingPermissions):
        message = '❌ Você precisa ser administrador para usar este comando.'
    else:
        message = '❌ Ocorreu um erro ao executar o comando.'
        print(f'App command error: {error}')

    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


token = os.getenv('DISCORD_TOKEN')
if not token:
    raise RuntimeError('A variável de ambiente DISCORD_TOKEN não foi configurada.')

bot.run(token)
