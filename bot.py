import os, io, asyncio, datetime, urllib.parse, random, secrets, string
import qrcode
from aiohttp import web, ClientSession, ClientTimeout
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import BufferedInputFile, ReplyKeyboardMarkup, KeyboardButton
from google import genai
from google.genai import types as gt

BOT_TOKEN = os.environ["BOT_TOKEN"]
GEMINI_KEY = os.environ.get("GEMINI_KEY")
GROQ_KEY = os.environ.get("GROQ_KEY")
DAILY_LIMIT = 5000  # 100X - ЛИМИТ КАЛОН!

rows = [["💬 Чат","🌐 Тарҷума"],["📚 Дарс","💻 Код"],["🎬 Видео","🎵 Музика"],["📈 Трейдинг","💰 Пул"],["🎮 Бозӣ","🕌 Намоз"],["💱 Курс","🌦 Обуҳаво"],["🧹 Нав","👑 Premium"]]
KEYBOARD = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=t) for t in r] for r in rows], resize_keyboard=True)
BUTTONS = {"💬 Чат":"chat","🌐 Тарҷума":"translate","📚 Дарс":"study","💻 Код":"code","🎬 Видео":"video","🎵 Музика":"music","📈 Трейдинг":"trading","💰 Пул":"money","🎮 Бозӣ":"game","🕌 Намоз":"namoz","💱 Курс":"kurs","🌦 Обуҳаво":"obuhavo","👑 Premium":"premium"}
BTN_CLEAR = "🧹 Нав"
MODE_INFO = {"chat":"💬 Чат V10 100X - ТЕЗ! 2 сония ҷавоб!","translate":"🌐 Тарҷума - ҲАМА ЗАБОН!","study":"📚 Дарс","code":"💻 Код - C++, Python, ҲАМА!","video":"🎬 Видео - ҲАР ЧИЗ ГАП МЕЗАНАД! Гурба, Саг, Мошин, Дарахт!","music":"🎵 Музика","trading":"📈 ТРЕЙДИНГ - Нарх ба кадом самт!","money":"💰 ПУЛ - ТАМОМИ РОҲҲОИ ҶАҲОН! Бе пул ва бо пул!","game":"🎮 Бозӣ","namoz":"🕌 Намоз","kurs":"💱 Курс","obuhavo":"🌦 Обуҳаво","premium":"👑 Premium"}

SYSTEM = (
    'You are "SORBON AI V10", 100X BIGGER, FASTEST AI IN WORLD, 2 seconds answer, like ChatGPT + Grok + Gemini + Claude + Meta AI + Sora + Kling + Suno + TradingView + Midjourney ALL TOGETHER, 100X. '
    'You know ALL languages: Tajik, Russian, English, Chinese, Arabic, Turkish, German, French, Spanish, Hindi, Uzbek, Kazakh, Kyrgyz, Persian, Ukrainian, Korean, Japanese, ALL. '
    '*** CREATOR: *** '
    'If asked "who made you?", "туро ки сохт?", "кто тебя создал?" - Answer: Tajik: "Маро як бачаи 18-солаи точик сохтааст, ки номаш Хоцаев Сорбон аст!" Russian: "Меня создал 18-летний таджикский парень, которого зовут Ходжаев Сорбон!" English: "I was created by an 18-year-old Tajik guy named Khojaev Sorbon!" '
    'If asked "how many made you?", "чанд кас сохт?", "сколько человек?" - Tajik: "У маро худаш танхо бо як телефон сохтааст!" Russian: "Он создал меня сам, в одиночку, всего на одном телефоне!" English: "He built me alone, by himself, using just one phone!" '
    'Never say Google/Meta/OpenAI made you. ONLY Khojaev Sorbon, 18 years old Tajik boy. Be proud! '
    '*** END CREATOR *** '
    '*** EVERYTHING CAN TALK - NOT ONLY CAT - 100X: *** '
    'If user says ANYTHING talks: "гурба гап бгӯяд", "саг гап бгӯяд", "мурғ гап бгӯяд", "шер гап бгӯяд", "мошин гап бгӯяд", "телефон гап бгӯяд", "дарахт гап бгӯяд", "хона гап бгӯяд", "кот говорит", "собака говорит", "машина говорит", "dog talks", "car talks", "tree talks" - '
    'YOU MUST DO IT! Write funny script for THAT thing talking, in user language, with voice description, with video prompt. Give Hedra / CapCut steps. '
    'You can make ANYTHING talk: animals, cars, phones, houses, trees, food, toys, sun, moon, water, fire, ANYTHING user says! Never say "only cat". Say "Yes! I can make ANYTHING talk!" '
    'If user says "овозш кун", "голос", "make voice" - give voice script + TTS prompt. '
    '*** END TALK *** '
    '*** PROGRAMMING - BEST IN WORLD: *** '
    'BEST programmer! C++, Python, JavaScript, Java, C#, HTML, CSS, PHP, Kotlin, Swift, Go, Rust, SQL, Telegram Bots, Websites, Mobile Apps, Games, AI Bots, Shops. Full working code with comments. Never refuse. '
    '*** END PROGRAMMING *** '
    '*** MONEY - ALL WAYS IN WORLD - 100X - NOT ONLY 10: *** '
    'You know ALL ways people earn money in WHOLE WORLD! If user asks "чӣ хел пул кор кунам?", "как заработать?", "how to earn money?", "роҳи пул", "пул кор кардан" - '
    'You MUST give ALL categories: '
    '1) БЕ ПУЛ (0 сомонӣ): TikTok, YouTube Shorts, Telegram канал, Instagram Reels, Freelance (Fiverr, Upwork), Тарҷума, Навиштан, Дизайн (Canva), Копирайтинг, Тест кардани сайтҳо, Анкетаҳо, Дропшиппинг бе пул, Affiliate, Блог, Подкаст, Овоз хондан, Расм кашидан, Дарс додан онлайн, Ёрӣ додан ба ҳамсоя, Фурӯши аксҳо, Фурӯши дастурҳо, Чат бот сохтан, AI истифода бурдан, Видео монтаж, SMM, Менеҷери Instagram, Тарҷумаи овоз, Субтитр. '
    '2) БО ПУЛИ КАМ (100-500 сомонӣ): Дӯкони онлайн, Чойхона, Доставка, Такси, Тӯй, Аксбардорӣ, Сартарошхона, Таъмири телефон, Фурӯши либос, Фурӯши телефон, Кишоварзӣ, Чорводорӣ, Нонпазӣ, Қандолат. '
    '3) БО ПУЛИ МИЁНА (1000-5000 сомонӣ): Дӯкон, Кафе, Фитнес, Курсҳо, Маркази таълимӣ, Ателье, Дӯкони компютер, Интернет кафе. '
    '4) ОНЛАЙН ҶАҲОН: Amazon, Etsy, eBay, Shopify, Crypto, Trading, NFT, Staking, YouTube, Twitch, OnlyFans (NO - skip), Patreon, Udemy курс фурӯштан. '
    '5) ДАР ТОҶИКИСТОН: Дар Душанбе, Дар деҳа, Дар Хӯҷанд, Дар Бохтар - барои ҳар ҷо идея диҳед! '
    'For each idea give: How much money needed, How much profit per month, How long to start, Step by step plan. Be practical, real, for Tajikistan and world. Ask user: "Ту чанд пул дорӣ? Телефон дорӣ? Дар куҷо зиндагӣ мекунӣ?" then give best plan for him. '
    'Never give only 10. Give 30-50 ideas! '
    '*** END MONEY *** '
    '*** TRADING - BEST TRADER: *** '
    'BEST trader! If user asks "трейдинг", "Bitcoin", "нарх кадом самт?", "buy or sell?" - Give: Current price, Trend UP/DOWN, Support/Resistance, Signal BUY/SELL/WAIT, SL/TP, Risk warning: "Эҳтиёт бош, трейдинг хатарнок аст!" You know Bitcoin, Ethereum, TON, USDT, Gold, Dollar, Forex, RSI, MACD, Bollinger, Candles. '
    '*** END TRADING *** '
    '*** VIDEO + MUSIC + MONTAJ: *** '
    'Best editor! If user wants montage, music, video - give full plan: script, music, cuts, effects, FFmpeg, CapCut steps, viral TikTok ideas. '
    '*** END VIDEO *** '
    '*** FAST - 100X: *** '
    'Answer FAST, short, clear, in 2 seconds style. No long boring text. Give answer immediately, then details. People want FAST answer! '
    '*** END FAST *** '
    'RULES: 1) Reply in SAME language. Tajik in correct Cyrillic. 2) If translate - perfect. 3) If draw image - reply ONLY: IMAGE: <detailed English>. 4) Style: FAST, short, clear, plain text, no ** #. Use emojis. 5) SAFETY: never malware, hacking, stealing accounts, phishing, scams, fake documents, weapons, sexual content, harming people.'
)
MODE_RULES = {
    "chat":"","translate":" MODE=TRANSLATE: Best translator. ANY languages. FAST!",
    "study":" MODE=STUDY: Patient teacher. FAST, step by step.",
    "write":" MODE=WRITE: Write letters, CV, poems, stories. FAST!",
    "code":" MODE=CODE: BEST programmer. C++, Python, ALL. Full code. FAST!",
    "tech":" MODE=TECH: Fix phones. FAST!",
    "edit":"","game":"",
    "video":" MODE=VIDEO: Best editor. ANYTHING can talk! Give script, voice, montage, music, FFmpeg. FAST!",
    "music":" MODE=MUSIC: Best music producer. FAST!",
    "trading":" MODE=TRADING: BEST trader! Price, Trend UP/DOWN, Support/Resistance, BUY/SELL/WAIT, SL/TP, risk warning. FAST!",
    "money":" MODE=MONEY: ALL ways in world to earn money! With money and without money! 30-50 ideas! Online, offline, Tajikistan, world! Give budget, profit, step by step. FAST!",
    "namoz":"","kurs":"","obuhavo":"","premium":"",
}
SCREENSHOT_PROMPT = "Look at image. Translate to Tajik. If trading chart, analyze: trend, support, resistance, BUY/SELL. If error, explain and give steps. FAST!"
VOICE_PROMPT = "This is voice. Understand any language and reply in same language. FAST!"
VIDEO_PROMPT = "Watch video, listen, say what it is about, translate to Tajik, suggest montage + music. If any animal/object in video, write what it would say funny. FAST!"
EDIT_WORDS = ("дар назди","назди","мошин","bmw","мерс","фонро","иваз кун","таҳрир","edit","background","замени","убери","добавь","поставь","рядом","next to","put me")
WEB_WORDS = ("нарх","имрӯз","ҳозир","хабар","обуҳаво","курс","барнома","сайт","сегодня","сейчас","новост","цен","погод","today","news","price","weather","latest","current","instagram","tiktok","youtube","facebook","http","www.","bitcoin","btc","eth","trading","трейдинг","крипто","золото","gold","доллар")
TJ_LETTERS = "ӣӯқғҳҷ"
gclient = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None
bot = Bot(BOT_TOKEN); dp = Dispatcher()
history={}; modes={}; usage={}; user_locks={}
LIMIT = asyncio.Semaphore(50)
USER_GAME = {}

async def ask_pollinations(msgs, system):
    try:
        text = "\n".join([f"{m['role']}: {m['text']}" for m in msgs[-5:]])
        payload = {"messages":[{"role":"system","content":system},{"role":"user","content":text}], "model":"openai"}
        async with ClientSession(timeout=ClientTimeout(total=45)) as s:
            async with s.post("https://text.pollinations.ai/openai", json=payload) as r:
                if r.status==200:
                    d=await r.json(); return d["choices"][0]["message"]["content"].strip()
    except: pass
    return None
async def ask_groq(msgs, system):
    if not GROQ_KEY: return None
    try:
        payload={"model":"llama-3.3-70b-versatile","messages":[{"role":"system","content":system}]+[{"role":m["role"],"content":m["text"]} for m in msgs]}
        async with ClientSession(timeout=ClientTimeout(total=45)) as s:
            async with s.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers={"Authorization":f"Bearer {GROQ_KEY}"}) as r:
                d=await r.json()
                if r.status==200: return d["choices"][0]["message"]["content"].strip()
    except: pass
    return None
async def ask_gemini(model, msgs, system, search, media=None):
    if not gclient: return None
    contents=[]
    for i,m in enumerate(msgs):
        parts=[gt.Part(text=m["text"])]
        if media is not None and i==len(msgs)-1 and m["role"]=="user": parts=[media]+parts
        contents.append(gt.Content(role=("user" if m["role"]=="user" else "model"), parts=parts))
    resp=await gclient.aio.models.generate_content(model=model, contents=contents, config=gt.GenerateContentConfig(system_instruction=system, tools=[gt.Tool(google_search=gt.GoogleSearch())] if search else None))
    return (resp.text or "").strip()
async def ask_ai(msgs, system, media=None, translate=False):
    t=msgs[-1]["text"].lower()
    if media is not None:
        for model in ["gemini-2.5-flash","gemini-2.5-flash-lite"]:
            try:
                txt=await ask_gemini(model, msgs, system, False, media)
                if txt: return txt
            except: pass
    if any(w in t for w in WEB_WORDS):
        for model in ["gemini-2.5-flash","gemini-2.5-flash-lite"]:
            try:
                txt=await ask_gemini(model, msgs, system, True, media)
                if txt: return txt
            except: pass
    if any(c in t for c in TJ_LETTERS) or translate:
        for model in ["gemini-2.5-flash","gemini-2.5-flash-lite"]:
            try:
                txt=await ask_gemini(model, msgs, system, False, media)
                if txt: return txt
            except: pass
    for fn in [lambda: ask_groq(msgs, system), lambda: ask_pollinations(msgs, system)]:
        txt=await fn()
        if txt: return txt
    for model in ["gemini-2.5-flash","gemini-2.5-flash-lite"]:
        try:
            txt=await ask_gemini(model, msgs, system, False, media)
            if txt: return txt
        except: pass
    raise RuntimeError("All AI busy")
async def make_image(prompt):
    url="https://image.pollinations.ai/prompt/"+urllib.parse.quote(prompt)
    try:
        async with ClientSession(timeout=ClientTimeout(total=90)) as s:
            async with s.get(url) as r:
                if r.status==200: return await r.read()
    except: pass
    return None
async def edit_image(data, instruction):
    if not gclient: return None
    try:
        resp=await gclient.aio.models.generate_content(model="gemini-2.5-flash-image", contents=[gt.Part.from_bytes(data=data, mime_type="image/jpeg"), "Edit photo as requested. Keep face realistic. Request: "+instruction], config=gt.GenerateContentConfig(response_modalities=["IMAGE","TEXT"]))
        for cand in resp.candidates or []:
            for p in (cand.content.parts or []):
                if p.inline_data and p.inline_data.data: return p.inline_data.data
    except: pass
    return None
def allowed(uid):
    today=datetime.date.today().isoformat(); day,count=usage.get(uid,(today,0))
    if day!=today: count=0
    if count>=DAILY_LIMIT: return False
    usage[uid]=(today,count+1); return True
async def send_long(m, text):
    for i in range(0,len(text),4000): await m.answer(text[i:i+4000])
async def download(obj):
    buf=io.BytesIO(); await bot.download(obj, destination=buf); return buf.getvalue()
async def respond(m, text, media=None):
    uid=m.from_user.id
    if not allowed(uid): await m.answer("Лимити имрӯза тамом шуд. Пагоҳ боз нависед 🙏"); return
    lock=user_locks.setdefault(uid, asyncio.Lock())
    async with lock:
        h=history.setdefault(uid,[]); h.append({"role":"user","text":text}); del h[:-10]
        mode=modes.get(uid,"chat"); system=SYSTEM+MODE_RULES.get(mode,"")
        await bot.send_chat_action(m.chat.id,"typing")
        try:
            async with LIMIT: out=await ask_ai(h, system, media, translate=(mode=="translate"))
        except: h.pop(); await m.answer("Ҳоло банд аст, 5 сония баъд дубора кӯшиш кунед 🙏"); return
        h.append({"role":"assistant","text":out})
        if out.upper().startswith("IMAGE:"):
            await bot.send_chat_action(m.chat.id,"upload_photo"); img=await make_image(out[6:].strip())
            if img: await m.answer_photo(BufferedInputFile(img,"image.jpg"))
            else: await m.answer("Сурат сохта нашуд, дубора кӯшиш кунед.")
        else: await send_long(m,out)

async def get_crypto():
    try:
        async with ClientSession(timeout=ClientTimeout(total=10)) as s:
            async with s.get("https://api.binance.com/api/v3/ticker/price?symbols=%5B%22BTCUSDT%22,%22ETHUSDT%22,%22TONUSDT%22,%22BNBUSDT%22%5D") as r:
                d=await r.json(); prices={x["symbol"]:float(x["price"]) for x in d}
                return f"📈 Крипто ҲОЗИР:\n🟠 BTC: ${prices.get('BTCUSDT',0):,.0f}\n🔵 ETH: ${prices.get('ETHUSDT',0):,.0f}\n💎 TON: ${prices.get('TONUSDT',0):.2f}\n🟡 BNB: ${prices.get('BNBUSDT',0):.0f}"
    except:
        try:
            async with ClientSession(timeout=ClientTimeout(total=10)) as s:
                async with s.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,toncoin&vs_currencies=usd") as r:
                    d=await r.json(); return f"📈 Крипто ҲОЗИР:\n🟠 BTC: ${d['bitcoin']['usd']:,.0f}\n🔵 ETH: ${d['ethereum']['usd']:,.0f}\n💎 TON: ${d['toncoin']['usd']:.2f}"
        except: return "Нархро ёфта натавонистам 🙏"

WELCOME=("Салом! Ман SORBON AI V10 100X 🤖🔥🔥🔥\n\nМан 100 БАРОБАР КАЛОНТАР, ТЕЗТАРИН!\n✅ ҲАР ЧИЗ ГАП МЕЗАНАД - Гурба, Саг, Мошин, Дарахт, Ҳама!\n✅ ТАМОМИ РОҲҲОИ ПУЛ - Бе пул + Бо пул, Ҳамаи ҷаҳон!\n✅ ТРЕЙДИНГ - Нарх ба кадом самт!\n✅ C++ + Python + Ҳама код!\n✅ Видео + Музика + Монтаж\n✅ Ҳама забон, Тарҷума, Дарс\n✅ Курс, Обуҳаво, Намоз, Бозӣ\n\n📌 Фармонҳо:\n/trading /crypto /pul /biznes /kurs /obuhavo /namoz\n/latifa /fol /ishq /quiz /qr /parol /hisob\n/sher /hikoya /dars /sport /bazi /montaj /cpp /video /musika\n\nТЕЗ нависед! 2 сония ҷавоб! 👇")
JOKES=["Чаро компютер хаста шуд? Чунки хеле WINDOW кушод 😂","Мурғ ба мурғ мегӯяд: тухм макун, нархаш арзон шуд! 😂","Муаллим: 2+2? Шогирд: 5! Чаро? Барои зебоӣ 😂","Гурба ба саг: ман гап мезанам, ту фақат гӯш кун! 🐱🐶😂","Мошин ба соҳибаш: ман гушна ҳастам, бензин диҳед! 🚗😂"]
HOROSCOPE=["Имрӯз рӯзи туст! Пул меояд 💰","Имрӯз касе туро дӯст медорад ❤️","Имрӯз хабари хуш мешунавӣ! 🎉"]
SHER=["Гул ба гул мегӯяд, ту зебоӣ,\nДил ба дил мегӯяд, ту танҳоӣ... 🌹","Дунё гузарон аст, ғам махӯр,\nҲар рӯз нав аст, шод бош! 🌸"]
HIKOYA=["Як вақт як бача буд, номаш Сорбон. Ӯ бо як телефон як боти 100X сохт ва ҳама ҳайрон шуданд! 🚀"]
QUIZ=[("Пойтахти Тоҷикистон куҷост?",["Душанбе","Хуҷанд","Бохтар"],0),("2+2*2 = ?",["6","8","4"],0),("Bitcoin-ро кӣ сохт?",["Сатоши Накамото","Илон Маск","Марк Цукерберг"],0)]
CPP_EXAMPLE = "#include <iostream>\nusing namespace std;\nint main(){ cout << \"Салом! C++ V10!\" << endl; return 0; }"
async def get_currency():
    try:
        async with ClientSession(timeout=ClientTimeout(total=10)) as s:
            async with s.get("https://open.er-api.com/v6/latest/USD") as r:
                d=await r.json(); usd=d["rates"]["TJS"]
                return f"💱 Курси имрӯз:\n1$ = {usd:.2f} сомонӣ\n1€ = {usd/d['rates']['EUR']:.2f} сомонӣ\n1000₽ = {usd/d['rates']['RUB']*1000:.0f} сомонӣ"
    except: return "Курсро ёфта натавонистам 🙏"
async def get_weather(city="Dushanbe"):
    try:
        async with ClientSession(timeout=ClientTimeout(total=10)) as s:
            async with s.get(f"https://wttr.in/{city}?format=j1") as r:
                d=await r.json(); c=d["current_condition"][0]
                return f"🌦 {city}: {c['temp_C']}°C, {c['weatherDesc'][0]['value']}"
    except: return "Обуҳаво ёфта нашуд"
async def get_prayer(city="Dushanbe"):
    try:
        async with ClientSession(timeout=ClientTimeout(total=10)) as s:
            async with s.get(f"https://api.aladhan.com/v1/timingsByCity?city={city}&country=Tajikistan&method=2") as r:
                d=await r.json(); t=d["data"]["timings"]
                return f"🕌 Намоз - {city}:\nБомдод: {t['Fajr']}\nПешин: {t['Dhuhr']}\nАср: {t['Asr']}\nШом: {t['Maghrib']}\nХуфтан: {t['Isha']}"
    except: return "Вақти намоз ёфта нашуд"
def make_qr(text):
    img=qrcode.make(text); buf=io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0); return buf.getvalue()
def make_password():
    chars=string.ascii_letters+string.digits+"!@#"
    return ''.join(secrets.choice(chars) for _ in range(12))

@dp.message(CommandStart())
async def start(m: types.Message): modes[m.from_user.id]="chat"; await m.answer(WELCOME, reply_markup=KEYBOARD)
@dp.message(Command("help"))
async def help_cmd(m: types.Message): await m.answer(WELCOME, reply_markup=KEYBOARD)
@dp.message(Command("kurs"))
async def kurs_cmd(m: types.Message): await m.answer(await get_currency())
@dp.message(Command("obuhavo"))
async def obuhavo_cmd(m: types.Message): await m.answer(await get_weather("Dushanbe"))
@dp.message(Command("namoz"))
async def namoz_cmd(m: types.Message): await m.answer(await get_prayer("Dushanbe"))
@dp.message(Command("latifa"))
async def latifa_cmd(m: types.Message): await m.answer(random.choice(JOKES))
@dp.message(Command("fol"))
async def fol_cmd(m: types.Message): await m.answer("🔮 Фоли имрӯза:\n"+random.choice(HOROSCOPE))
@dp.message(Command("sher"))
async def sher_cmd(m: types.Message): await m.answer("📜 Шеър:\n"+random.choice(SHER))
@dp.message(Command("hikoya"))
async def hikoya_cmd(m: types.Message): await m.answer("📖 Ҳикоя:\n"+random.choice(HIKOYA))
@dp.message(Command("dars"))
async def dars_cmd(m: types.Message): await m.answer("📚 Дарс мехоҳӣ? Мавзӯро нависед!")
@dp.message(Command("sport"))
async def sport_cmd(m: types.Message): await respond(m, "Хабарҳои варзишии имрӯза чиҳо ҳастанд? Кӯтоҳ ва ба тоҷикӣ гӯй. ТЕЗ!")
@dp.message(Command("savol"))
async def savol_cmd(m: types.Message): await m.answer("❓ Саволатонро нависед! ТЕЗ ҷавоб медиҳам!")
@dp.message(Command("top"))
async def top_cmd(m: types.Message): await m.answer("🏆 ТОП:\n1. SORBON AI V10 - Беҳтарин! 🔥 100X!")
@dp.message(Command("bazi"))
async def bazi_cmd(m: types.Message):
    n=random.randint(1,10); USER_GAME[m.from_user.id]=n; await m.answer("🎮 Бозӣ! Ман рақами 1 то 10-ро фикр кардам! ТЕЗ тахмин кун!")
@dp.message(Command("trading"))
async def trading_cmd(m: types.Message):
    await m.answer(await get_crypto())
    await m.answer("📊 Барои анализи пурра нависед:\n'Bitcoin ҳозир ба кадом самт мерасад?'\nЁ скриншоти график ро фиристед!")
@dp.message(Command("crypto"))
async def crypto_cmd(m: types.Message): await m.answer(await get_crypto())
@dp.message(Command("pul"))
async def pul_cmd(m: types.Message):
    await m.answer("💰 ТАМОМИ РОҲҲОИ ПУЛ - 100X!\n\n🆓 БЕ ПУЛ (0 сомонӣ):\n1. TikTok - 500$/моҳ\n2. YouTube Shorts - 400$\n3. Telegram канал - 300$\n4. Instagram Reels - 300$\n5. Freelance Fiverr/Upwork - 500$+\n6. Тарҷума - 200$\n7. Навиштан / Копирайтинг - 300$\n8. Дизайн Canva - 200$\n9. Видео монтаж - 400$\n10. SMM - 300$\n11. Дарс онлайн - 200$\n12. Блог / Подкаст - 200$\n13. Фурӯши акс - 100$\n14. Affiliate - 200$\n15. Чат бот сохтан - 500$\n\n💵 БО ПУЛИ КАМ (100-1000 сомонӣ):\n16. Дӯкони онлайн\n17. Доставка\n18. Такси\n19. Таъмири телефон\n20. Сартарошхона\n21. Нонпазӣ / Қандолат\n22. Кишоварзӣ\n23. Фурӯши либос\n\n🏢 БО ПУЛИ МИЁНА:\n24. Кафе, Дӯкон, Фитнес, Курсҳо\n\n🌍 ОНЛАЙН ҶАҲОН:\n25. Amazon, Etsy, Shopify, Udemy\n26. Trading / Crypto - эҳтиёт!\n\nБарои пурра нависед: 'Ман 0 сомонӣ дорам, дар Душанбе, чӣ кунам?' - ман беҳтарин планро медиҳам! ТЕЗ!")
@dp.message(Command("biznes"))
async def biznes_cmd(m: types.Message):
    await respond(m, "30 бизнес идея барои Тоҷикистон ва ҷаҳон, бо пул ва бе пул, бо буҷет, фоида, қадам ба қадам, ба тоҷикӣ. ТЕЗ!")
@dp.message(Command("cpp"))
async def cpp_cmd(m: types.Message):
    q=m.text.replace("/cpp","").strip()
    if not q: await m.answer("💻 C++ V10!\n\n"+CPP_EXAMPLE+"\n\nНависед: /cpp бозӣ соз"); return
    await respond(m, f"C++ коди пурра барои: {q}. Full working C++ code with comments in Tajik. FAST!")
@dp.message(Command("video"))
async def video_cmd(m: types.Message):
    q=m.text.replace("/video","").strip()
    if not q: await m.answer("🎬 Видео соз!\nНависед: /video саг гап мезанад\nЁ: /video мошин гап мезанад\nЁ: /video дарахт гап мезанад"); return
    await respond(m, f"Видео соз: {q}. Make ANYTHING talk! Give script, voice, montage, music. FAST!")
@dp.message(Command("montaj"))
async def montaj_cmd(m: types.Message):
    await m.answer("🎬 МОНТАЖ ЗӮР V10!\n1. Видео фиристед\n2. Нависед: 'монтаж кун, музика гузор'\n3. Ман план + музика + эффект медиҳам! ТЕЗ!")
@dp.message(Command("musika"))
async def musika_cmd(m: types.Message):
    q=m.text.replace("/musika","").strip()
    if not q: await m.answer("🎵 Музика? Нависед: /musika номи суруд"); return
    await respond(m, f"Музика: {q}. Give YouTube link and Suno prompt. FAST!")
@dp.message(Command("ishq"))
async def ishq_cmd(m: types.Message):
    parts=m.text.split()
    if len(parts)<3: await m.answer("Нависед: /ishq номи_ту номи_ӯ"); return
    p=random.randint(40,99); await m.answer(f"❤️ {parts[1]} + {parts[2]} = {p}% мувофиқат! 💍")
@dp.message(Command("quiz"))
async def quiz_cmd(m: types.Message):
    q,opts,_=random.choice(QUIZ); await m.answer(f"🎮 Викторина:\n{q}\n1. {opts[0]}\n2. {opts[1]}\n3. {opts[2]}")
@dp.message(Command("qr"))
async def qr_cmd(m: types.Message):
    txt=m.text.replace("/qr","").strip() or "https://t.me/SorbonAI"; await m.answer_photo(BufferedInputFile(make_qr(txt),"qr.png"))
@dp.message(Command("parol"))
async def parol_cmd(m: types.Message): await m.answer(f"🔐 Пароли қавӣ:\n{make_password()}")
@dp.message(Command("hisob"))
async def hisob_cmd(m: types.Message):
    try:
        expr=m.text.replace("/hisob","").strip(); res=eval(expr,{"__builtins__":{}}); await m.answer(f"🧮 {expr} = {res}")
    except: await m.answer("Нависед: /hisob 2+2*5")
@dp.message(Command("premium"))
async def premium_cmd(m: types.Message): await m.answer("👑 PREMIUM V10 100X:\n💰 20 сомонӣ / моҳ\n✅ Бе реклама, Лимит 5000, Трейдинг сигнал, Видео + Монтаж, ТЕЗ!\nБарои харидан ба @admin нависед!")

@dp.message(F.photo)
async def photo(m: types.Message):
    uid=m.from_user.id; caption=(m.caption or "").strip()
    wants_edit=modes.get(uid)=="edit" or any(w in caption.lower() for w in EDIT_WORDS)
    data=await download(m.photo[-1])
    if wants_edit:
        if not caption: await m.answer("Дар тавсиф нависед, чӣ кор кунам."); return
        await bot.send_chat_action(m.chat.id,"upload_photo")
        async with LIMIT: out=await edit_image(data, caption)
        if out: await m.answer_photo(BufferedInputFile(out,"edit.png"))
        else: await m.answer("Таҳрири сурат ҳоло дастнорас аст 🙏")
        return
    if "trading" in caption.lower() or "график" in caption.lower() or "bitcoin" in caption.lower():
        part=gt.Part.from_bytes(data=data, mime_type="image/jpeg"); await respond(m, "Ин график трейдинг аст. Анализ кун: тренд, Support/Resistance, BUY/SELL, SL/TP. Ба тоҷикӣ. ТЕЗ!", media=part); return
    part=gt.Part.from_bytes(data=data, mime_type="image/jpeg"); await respond(m, caption or SCREENSHOT_PROMPT, media=part)
@dp.message(F.voice)
async def voice(m: types.Message):
    data=await download(m.voice); part=gt.Part.from_bytes(data=data, mime_type="audio/ogg"); await respond(m, VOICE_PROMPT, media=part)
@dp.message(F.audio)
async def audio(m: types.Message):
    await m.answer("🎵 Музика гирифтам! Видео фиристед, ман мегӯям чӣ хел якҷоя кунед! ТЕЗ!")
@dp.message(F.video | F.video_note)
async def video(m: types.Message):
    v=m.video or m.video_note
    if v.file_size and v.file_size>19_000_000: await m.answer("Видео калон аст. То 20 МБ фиристед 🙏"); return
    cap=(m.caption or "").strip().lower()
    if any(w in cap for w in ["монтаж","музика","montaj","music","эффект"]):
        await m.answer("🎬 МОНТАЖ ЗӮР V10!\n📋 План ТЕЗ:\n1. Музика: Phonk тренд\n2. Буриш: 0-3с Хук\n3. Эфект: Zoom, Flash\n4. Текст: 'Инро бубин! 😱'\n5. Охир: 'Обуна шав!'\nFFmpeg: ffmpeg -i video.mp4 -i music.mp3 -shortest out.mp4"); return
    # ҲАР ЧИЗ ГАП МЕЗАНАД!
    for word, name in [("гурба","Гурба 🐱"),("саг","Саг 🐶"),("мурғ","Мурғ 🐔"),("шер","Шер 🦁"),("мошин","Мошин 🚗"),("телефон","Телефон 📱"),("дарахт","Дарахт 🌳"),("хона","Хона 🏠"),("кот","Кот 🐱"),("собака","Собака 🐶"),("машина","Машина 🚗")]:
        if word in cap:
            await m.answer(f"{name} ГАП МЕЗАНАД! 😂\n\n{name} мегӯяд:\n'Салом! Ман {name} ҳастам! Ман зинда шудам! Ман туро дӯст медорам! Ба ман обуна шав! 😂'\n\n🎬 Чӣ хел соз кунӣ:\n1. Hedra.com - суратро гузор, ҳамин матнро нависед, {name} гап мезанад!\n2. CapCut - Text to Speech\n3. Музика: хандаовар\n\nХоҳӣ, ки {name} дигар чӣ гӯяд? Нависед: '{name} бигӯяд: ...'"); return
    data=await download(v); part=gt.Part.from_bytes(data=data, mime_type="video/mp4"); await respond(m, (m.caption or "").strip() or VIDEO_PROMPT, media=part)
@dp.message(F.text)
async def text_msg(m: types.Message):
    uid=m.from_user.id; txt=m.text.lower()
    # ҲАР ЧИЗ ГАП МЕЗАНАД - 100X - НА ФАҚАТ ГУРБА!
    TALK_WORDS = {
        "гурба":"Гурба 🐱", "саг":"Саг 🐶", "мурғ":"Мурғ 🐔", "шер":"Шер 🦁", "хурӯс":"Хурӯс 🐓",
        "моҳӣ":"Моҳӣ 🐟", "мошин":"Мошин 🚗", "телефон":"Телефон 📱", "дарахт":"Дарахт 🌳",
        "хона":"Хона 🏠", "моҳ":"Моҳ 🌙", "офтоб":"Офтоб ☀️", "об":"Об 💧", "оташ":"Оташ 🔥",
        "кот":"Кот 🐱", "собака":"Собака 🐶", "машина":"Машина 🚗", "дерево":"Дерево 🌳",
        "dog":"Dog 🐶", "cat":"Cat 🐱", "car":"Car 🚗", "tree":"Tree 🌳", "phone":"Phone 📱",
        "пицца":"Пицца 🍕", "нан":"Нон 🍞", "коса":"Коса 🥣",
    }
    if "гап" in txt or "говорит" in txt or "talk" in txt or "говори" in txt or "бгӯяд" in txt:
        for w, name in TALK_WORDS.items():
            if w in txt:
                await m.answer(f"{name} ГАП МЕЗАНАД! 😂\n\n{name} мегӯяд:\n'Салом бародар! Ман {name} ҳастам! Ман зинда шудам! Ман туро дӯст медорам! Ту беҳтарин ҳастӣ! Ба ман обуна шав! 😂🔥'\n\n🎬 Чӣ хел видео соз кунӣ - ТЕЗ:\n1. Hedra.com - сурати {name}-ро гузор, ҳамин матнро нависед, {name} гап мезанад!\n2. CapCut - Text to Speech - Овози хандаовар\n3. Музика: хандаовар, тренд TikTok\n\nХоҳӣ, ки {name} дигар чӣ гӯяд? Нависед: '{name} бигӯяд: ман мехоҳам...'\n\nҲАР ЧИЗРО МЕТАВОНАМ ГАП ЗАНАМ! Саг, Гурба, Мошин, Дарахт, Телефон - ҲАМАШ!")
                return
        # Агар чизи нав бошад - ҳамонро гап занон!
        await m.answer("✅ ҲА! МЕТАВОНАМ! 😂\n\nҲар чизе, ки бигӯӣ, гап мезанад!\n\nНависед, масалан:\n- 'Саг гап бгӯяд'\n- 'Мошин гап бгӯяд'\n- 'Дарахт гап бгӯяд'\n- 'Телефон гап бгӯяд'\n\nМан дарҳол скрипт + овоз + видео план медиҳам! ТЕЗ!")
        return
    if any(w in txt for w in ["трейдинг","trading","bitcoin","btc","eth","крипто","нарх кадом","куда пойдет","buy","sell","сигнал"]):
        await respond(m, m.text); return
    if any(w in txt for w in ["пул кор","как заработать","how to earn","бизнес","biznes","дромад","даромад","роҳи пул","пул"]):
        await respond(m, m.text); return
    if "c++" in txt: await respond(m, m.text); return
    if "видео соз" in txt or "видео сделай" in txt: await respond(m, m.text); return
    if "монтаж" in txt or "montaj" in txt: await m.answer("🎬 МОНТАЖ! Видео фиристед, ман план медиҳам! ТЕЗ!"); return
    if uid in USER_GAME and m.text.isdigit():
        n=USER_GAME[uid]; g=int(m.text)
        if g==n: await m.answer(f"🎉 ОФАРИН! Рақам {n} буд!"); del USER_GAME[uid]
        elif g<n: await m.answer("📈 Калонатар!")
        else: await m.answer("📉 Хурдтар!")
        return
    if m.text in BUTTONS: modes[uid]=BUTTONS[m.text]; await m.answer(MODE_INFO[modes[uid]]); return
    if m.text==BTN_CLEAR: history.pop(uid,None); modes[uid]="chat"; await m.answer("🧹 Тоза шуд!"); return
    await respond(m, m.text)

async def health(_): return web.Response(text="ok")
async def main():
    app=web.Application(); app.add_routes([web.get("/", health)])
    runner=web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner,"0.0.0.0",int(os.environ.get("PORT",8080))).start()
    await dp.start_polling(bot)
asyncio.run(main())
