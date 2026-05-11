import discord
from discord.ext import commands
import os

# ====================== AYARLAR (ID'LERİ DOLDUR) ======================
# Tokeni ortam değişkeninden (Variable) çekiyoruz
TOKEN = os.environ.get("TOKEN") 

DEGER_YETKILI_ROL_ID = 1503341767049740369  # Yetkili rolün ID'si
LOG_KANAL_ID = 123456789012345678          # İşlem log kanalı ID'si
# =======================================================================

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

# --- MATEMATİKSEL FONKSİYONLAR ---

def parse_deger(metin):
    """'1.5M' gibi metinleri sayıya çevirir."""
    metin = metin.upper().replace(",", ".").replace(" ", "")
    multi = 1
    if metin.endswith("B"): multi = 1_000_000_000; metin = metin[:-1]
    elif metin.endswith("M"): multi = 1_000_000; metin = metin[:-1]
    elif metin.endswith("K"): multi = 1_000; metin = metin[:-1]
    try:
        return float(metin) * multi
    except:
        return None

def format_deger(sayi):
    """Sayıyı '1.5M' formatına çevirir."""
    if sayi >= 1_000_000_000: return f"{sayi/1_000_000_000:.1f}B".replace(".0", "")
    if sayi >= 1_000_000: return f"{sayi/1_000_000:.1f}M".replace(".0", "")
    if sayi >= 1_000: return f"{sayi/1_000:.1f}K".replace(".0", "")
    return str(int(sayi))

def nick_guncelle(mevcut_nick, miktar_str, islem):
    """İsim formatı: İsim | Değer | Takım"""
    parcalar = [p.strip() for p in mevcut_nick.split("|")]
    if len(parcalar) < 2:
        return None, "İsim formatı yanlış! (Format: İsim | 1M | Takım)"
    
    mevcut_sayi = parse_deger(parcalar[1])
    eklenecek_sayi = parse_deger(miktar_str)
    
    if mevcut_sayi is None or eklenecek_sayi is None:
        return None, "Geçersiz değer formatı!"
    
    yeni_sayi = mevcut_sayi + eklenecek_sayi if islem == "ekle" else mevcut_sayi - eklenecek_sayi
    parcalar[1] = format_deger(max(0, yeni_sayi))
    
    return " | ".join(parcalar), parcalar[1]

# --- BOT OLAYLARI VE KOMUTLAR ---

@bot.event
async def on_ready():
    print(f"✅ {bot.user.name} Değer Botu Aktif!")

@bot.command()
@commands.has_any_role(DEGER_YETKILI_ROL_ID)
async def dver(ctx, uye: discord.Member, miktar: str):
    """Değer ekleme komutu: .dver @üye 5M"""
    eski_nick = uye.display_name
    yeni_nick, yeni_deger_str = nick_guncelle(eski_nick, miktar, "ekle")
    
    if yeni_nick is None:
        return await ctx.send(f"❌ **Hata:** {yeni_deger_str}")

    try:
        await uye.edit(nick=yeni_nick)
        embed = discord.Embed(title="💰 Değer Artışı", color=0x2ecc71)
        embed.add_field(name="👤 Oyuncu", value=uye.mention, inline=True)
        embed.add_field(name="📈 Değişim", value=f"+{miktar.upper()}", inline=True)
        embed.add_field(name="💵 Yeni Değer", value=yeni_deger_str, inline=True)
        
        await ctx.send(embed=embed)
        
        log_kanali = bot.get_channel(LOG_KANAL_ID)
        if log_kanali: await log_kanali.send(embed=embed)
    except discord.Forbidden:
        await ctx.send("❌ **Yetki Hatası:** Botun rolü bu üyenin üstünde olmalı!")

@bot.command()
@commands.has_any_role(DEGER_YETKILI_ROL_ID)
async def dsil(ctx, uye: discord.Member, miktar: str):
    """Değer silme komutu: .dsil @üye 2M"""
    eski_nick = uye.display_name
    yeni_nick, yeni_deger_str = nick_guncelle(eski_nick, miktar, "cikar")
    
    if yeni_nick is None:
        return await ctx.send(f"❌ **Hata:** {yeni_deger_str}")

    try:
        await uye.edit(nick=yeni_nick)
        embed = discord.Embed(title="📉 Değer Düşüşü", color=0xe74c3c)
        embed.add_field(name="👤 Oyuncu", value=uye.mention, inline=True)
        embed.add_field(name="📉 Değişim", value=f"-{miktar.upper()}", inline=True)
        embed.add_field(name="💵 Yeni Değer", value=yeni_deger_str, inline=True)
        
        await ctx.send(embed=embed)
        
        log_kanali = bot.get_channel(LOG_KANAL_ID)
        if log_kanali: await log_kanali.send(embed=embed)
    except:
        await ctx.send("❌ **Hata:** İsim güncellenemedi.")

@bot.command()
async def dtop(ctx):
    """En değerli 10 oyuncuyu sıralar."""
    oyuncular = []
    for member in ctx.guild.members:
        if "|" in member.display_name:
            parcalar = member.display_name.split("|")
            val = parse_deger(parcalar[1])
            if val is not None:
                oyuncular.append((member, val))
    
    sirali = sorted(oyuncular, key=lambda x: x[1], reverse=True)[:10]
    
    if not sirali:
        return await ctx.send("❌ Listelenecek oyuncu bulunamadı.")
    
    text = ""
    for i, (uye, val) in enumerate(sirali, 1):
        text += f"**{i}.** {uye.mention} ➔ `{format_deger(val)}` \n"
        
    embed = discord.Embed(title="🏆 Sunucu Değer Sıralaması", description=text, color=0xf1c40f)
    await ctx.send(embed=embed)

@bot.command()
async def dyardim(ctx):
    """Yardım menüsü."""
    embed = discord.Embed(title="📖 Değer Botu Komutları", color=0x3498db)
    embed.add_field(name=".dver @uye [miktar]", value="Değer ekler (Örn: .dver @Messi 5M)", inline=False)
    embed.add_field(name=".dsil @uye [miktar]", value="Değer siler (Örn: .dsil @Messi 2.5M)", inline=False)
    embed.add_field(name=".dtop", value="Zenginlik sıralamasını gösterir.", inline=False)
    embed.set_footer(text="İsim formatı: İsim | Değer | Takım")
    await ctx.send(embed=embed)

# Hata Yönetimi (Yetki yoksa)
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("❌ Bu komutu sadece **Değer Yetkilileri** kullanabilir!")

# Botu çalıştır
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ HATA: 'TOKEN' environment variable bulunamadı!")
