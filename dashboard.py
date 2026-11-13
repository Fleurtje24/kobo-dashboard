import os, datetime, requests, icalendar, recurring_ical_events
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont

TZ = ZoneInfo("Europe/Amsterdam")
W, H = 758, 1024
LAT, LON = 52.16, 5.39  # Amersfoort

DAGEN = ["maandag","dinsdag","woensdag","donderdag","vrijdag","zaterdag","zondag"]
MAANDEN = ["januari","februari","maart","april","mei","juni","juli",
           "augustus","september","oktober","november","december"]
WEER = {0:"Helder",1:"Overwegend helder",2:"Half bewolkt",3:"Bewolkt",
        45:"Mist",48:"Mist",51:"Motregen",53:"Motregen",55:"Motregen",
        61:"Lichte regen",63:"Regen",65:"Zware regen",71:"Lichte sneeuw",
        73:"Sneeuw",75:"Zware sneeuw",80:"Buien",81:"Buien",82:"Zware buien",
        95:"Onweer",96:"Onweer",99:"Onweer"}

def font(size, bold=False):
    naam = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{naam}", size)

def weer():
    r = requests.get("https://api.open-meteo.com/v1/forecast", params={
        "latitude": LAT, "longitude": LON, "timezone": "Europe/Amsterdam",
        "current": "temperature_2m,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max"
    }, timeout=20).json()
    c, d = r["current"], r["daily"]
    return (round(c["temperature_2m"]), WEER.get(c["weather_code"], ""),
            round(d["temperature_2m_max"][0]), round(d["temperature_2m_min"][0]),
            d["precipitation_probability_max"][0])

def afspraken(vandaag):
    start = datetime.datetime.combine(vandaag, datetime.time.min, TZ)
    eind = start + datetime.timedelta(days=1)
    items = []
    for url in os.environ.get("CALENDAR_URLS", "").split():
        try:
            cal = icalendar.Calendar.from_ical(requests.get(url, timeout=20).content)
            for e in recurring_ical_events.of(cal).between(start, eind):
                s = e["DTSTART"].dt
                titel = str(e.get("SUMMARY", "(geen titel)"))
                if isinstance(s, datetime.datetime):
                    items.append((s.astimezone(TZ).strftime("%H:%M"), titel))
                else:
                    items.append(("Hele dag", titel))
        except Exception as ex:
            print("Agenda mislukt:", ex)
    return sorted(items, key=lambda x: ("0" if x[0] == "Hele dag" else x[0]))

def verjaardagen(vandaag):
    return []  # komt later

def main():
    nu = datetime.datetime.now(TZ)
    v = nu.date()
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)
    y = 40
    d.text((40, y), DAGEN[v.weekday()].capitalize(), font=font(64, True), fill=0); y += 80
    d.text((40, y), f"{v.day} {MAANDEN[v.month-1]} {v.year}", font=font(40), fill=0); y += 70
    d.line((40, y, W-40, y), fill=0, width=3); y += 30

    try:
        t, oms, mx, mn, regen = weer()
        d.text((40, y), f"{t}°", font=font(110, True), fill=0)
        d.text((300, y+10), oms, font=font(40), fill=0)
        d.text((300, y+65), f"{mn}° / {mx}°  ·  regen {regen}%", font=font(30), fill=0)
    except Exception:
        d.text((40, y), "Weer niet beschikbaar", font=font(36), fill=0)
    y += 150
    d.line((40, y, W-40, y), fill=0, width=3); y += 30

    d.text((40, y), "Vandaag", font=font(44, True), fill=0); y += 65
    lijst = afspraken(v)
    if not lijst:
        d.text((40, y), "Geen afspraken", font=font(34), fill=0); y += 50
    for tijd, titel in lijst[:12]:
        d.text((40, y), tijd, font=font(32, True), fill=0)
        d.text((230, y), titel[:28], font=font(32), fill=0)
        y += 50

    jarig = verjaardagen(v)
    if jarig:
        y += 20
        d.text((40, y), "Jarig: " + ", ".join(jarig), font=font(34, True), fill=0)

    d.text((40, H-50), f"Bijgewerkt {nu:%H:%M}", font=font(24), fill=100)
    os.makedirs("site", exist_ok=True)
    img.save(f"site/{os.environ['IMAGE_NAME']}.png")

main()
