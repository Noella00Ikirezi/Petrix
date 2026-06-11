import os
import asyncio
import hmac
from datetime import datetime

import aiohttp
from aiohttp import web
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

# ── Config ─────────────────────────────────────────────────
DISCORD_TOKEN         = os.environ["DISCORD_BOT_TOKEN"]
GITLAB_WEBHOOK_SECRET = os.getenv("GITLAB_WEBHOOK_SECRET", "")
GITLAB_TOKEN          = os.getenv("GITLAB_TOKEN", "")
GITLAB_PROJECT_ID     = os.getenv("GITLAB_PROJECT_ID", "")
CHANNEL_CI_ID         = int(os.getenv("DISCORD_CHANNEL_CI_ID", "0"))
CHANNEL_GIT_ID        = int(os.getenv("DISCORD_CHANNEL_GIT_ID", "0"))
WEBHOOK_PORT          = int(os.getenv("WEBHOOK_PORT", "8001"))
GITLAB_API            = "https://gitlab.com/api/v4"

# ── Bot ────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

STATUS_COLORS = {
    "success":  discord.Color.green(),
    "failed":   discord.Color.red(),
    "running":  discord.Color.yellow(),
    "pending":  discord.Color.light_gray(),
    "canceled": discord.Color.greyple(),
}
STATUS_EMOJI = {
    "success": "✅", "failed": "❌", "running": "🔄",
    "pending": "⏳", "canceled": "⛔",
}


async def send_embed(channel_id: int, embed: discord.Embed):
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send(embed=embed)


# ── Webhook GitLab ──────────────────────────────────────────
async def handle_webhook(request: web.Request) -> web.Response:
    token = request.headers.get("X-Gitlab-Token", "")
    if GITLAB_WEBHOOK_SECRET and not hmac.compare_digest(token, GITLAB_WEBHOOK_SECRET):
        return web.Response(status=403, text="Forbidden")

    try:
        data = await request.json()
    except Exception:
        return web.Response(status=400, text="Invalid JSON")

    event = request.headers.get("X-Gitlab-Event", "")
    if event == "Pipeline Hook":
        await handle_pipeline(data)
    elif event in ("Push Hook", "Tag Push Hook"):
        await handle_push(data)
    elif event == "Merge Request Hook":
        await handle_mr(data)

    return web.Response(text="OK")


async def handle_pipeline(data: dict):
    pipeline = data.get("object_attributes", {})
    status = pipeline.get("status", "unknown")
    if status not in ("success", "failed"):
        return

    embed = discord.Embed(
        title=f"{STATUS_EMOJI.get(status, '🔔')} Pipeline {status.upper()} — {pipeline.get('ref', '?')}",
        color=STATUS_COLORS.get(status, discord.Color.default()),
        url=pipeline.get("web_url", ""),
        timestamp=datetime.utcnow(),
    )
    commit = data.get("commit", {})
    embed.add_field(name="Commit", value=commit.get("message", "?")[:80], inline=False)
    embed.add_field(name="Auteur", value=commit.get("author", {}).get("name", "?"), inline=True)
    embed.add_field(name="Durée", value=f"{pipeline.get('duration', 0)}s", inline=True)
    embed.set_footer(text=data.get("project", {}).get("name", "Petrix"))

    await send_embed(CHANNEL_CI_ID, embed)


async def handle_push(data: dict):
    commits = data.get("commits", [])
    if not commits:
        return

    branch = data.get("ref", "").replace("refs/heads/", "")
    embed = discord.Embed(
        title=f"📦 {len(commits)} commit(s) → `{branch}`",
        color=discord.Color.blurple(),
        url=data.get("project", {}).get("web_url", "") + f"/-/commits/{branch}",
        timestamp=datetime.utcnow(),
    )
    embed.set_author(name=data.get("user_name", "?"))
    desc = ""
    for c in commits[:5]:
        short = c.get("id", "")[:7]
        msg = c.get("message", "").split("\n")[0][:60]
        desc += f"`{short}` {msg}\n"
    embed.description = desc
    embed.set_footer(text=data.get("project", {}).get("name", "Petrix"))

    await send_embed(CHANNEL_GIT_ID, embed)


async def handle_mr(data: dict):
    mr = data.get("object_attributes", {})
    action = mr.get("action", "")
    labels = {
        "open":   ("🔀 MR ouvert",          discord.Color.blue()),
        "merge":  ("✅ MR mergé",            discord.Color.green()),
        "close":  ("🔒 MR fermé",            discord.Color.red()),
        "update": ("✏️ MR mis à jour",       discord.Color.yellow()),
    }
    if action not in labels:
        return

    title, color = labels[action]
    embed = discord.Embed(title=title, color=color, url=mr.get("url", ""), timestamp=datetime.utcnow())
    embed.add_field(name="Titre",  value=mr.get("title", "?"),         inline=False)
    embed.add_field(name="Source", value=mr.get("source_branch", "?"), inline=True)
    embed.add_field(name="Cible",  value=mr.get("target_branch", "?"), inline=True)
    embed.set_author(name=data.get("user", {}).get("name", "?"))
    embed.set_footer(text=data.get("project", {}).get("name", "Petrix"))

    await send_embed(CHANNEL_GIT_ID, embed)


# ── Slash commands ──────────────────────────────────────────
@bot.tree.command(name="status", description="Statut du dernier pipeline GitLab")
async def cmd_status(interaction: discord.Interaction):
    await interaction.response.defer()
    if not GITLAB_TOKEN or not GITLAB_PROJECT_ID:
        await interaction.followup.send("⚠️ GITLAB_TOKEN ou GITLAB_PROJECT_ID non configuré.")
        return

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{GITLAB_API}/projects/{GITLAB_PROJECT_ID}/pipelines?per_page=1",
            headers={"PRIVATE-TOKEN": GITLAB_TOKEN},
        ) as resp:
            if resp.status != 200:
                await interaction.followup.send("❌ Impossible de contacter GitLab.")
                return
            pipelines = await resp.json()

    if not pipelines:
        await interaction.followup.send("Aucun pipeline trouvé.")
        return

    p = pipelines[0]
    status = p.get("status", "unknown")
    embed = discord.Embed(
        title=f"{STATUS_EMOJI.get(status, '🔔')} Pipeline #{p['id']} — {status.upper()}",
        color=STATUS_COLORS.get(status, discord.Color.default()),
        url=p.get("web_url", ""),
    )
    embed.add_field(name="Branche", value=p.get("ref", "?"), inline=True)
    embed.add_field(name="SHA",     value=p.get("sha", "?")[:7],  inline=True)
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="deploy", description="Déclenche le pipeline de déploiement sur main")
@app_commands.checks.has_permissions(administrator=True)
async def cmd_deploy(interaction: discord.Interaction):
    await interaction.response.defer()
    if not GITLAB_TOKEN or not GITLAB_PROJECT_ID:
        await interaction.followup.send("⚠️ GITLAB_TOKEN ou GITLAB_PROJECT_ID non configuré.")
        return

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{GITLAB_API}/projects/{GITLAB_PROJECT_ID}/pipeline",
            json={"ref": "main"},
            headers={"PRIVATE-TOKEN": GITLAB_TOKEN},
        ) as resp:
            if resp.status not in (200, 201):
                await interaction.followup.send(f"❌ Erreur GitLab : {resp.status}")
                return
            data = await resp.json()

    embed = discord.Embed(
        title="🚀 Pipeline déclenché",
        color=discord.Color.blurple(),
        url=data.get("web_url", ""),
    )
    embed.add_field(name="ID",      value=f"#{data['id']}",       inline=True)
    embed.add_field(name="Branche", value=data.get("ref", "main"), inline=True)
    embed.set_footer(text=f"Déclenché par {interaction.user.display_name}")
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="pin", description="Épingle le dernier message du salon")
@app_commands.checks.has_permissions(manage_messages=True)
async def cmd_pin(interaction: discord.Interaction):
    messages = [m async for m in interaction.channel.history(limit=5)]
    target = next((m for m in messages if not m.author.bot), None)
    if not target:
        await interaction.response.send_message("Aucun message à épingler.", ephemeral=True)
        return
    await target.pin()
    await interaction.response.send_message("📌 Message épinglé !", ephemeral=True)


# ── Démarrage ───────────────────────────────────────────────
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot connecté : {bot.user}")
    print(f"   Webhook server : http://0.0.0.0:{WEBHOOK_PORT}/webhook/gitlab")


async def main():
    app = web.Application()
    app.router.add_post("/webhook/gitlab", handle_webhook)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", WEBHOOK_PORT).start()

    async with bot:
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
