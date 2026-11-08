#!/usr/bin/env python3
"""Generate the guide's SVG diagrams in one consistent style."""
import json, math, os, sys
from xml.sax.saxutils import escape as esc

OUT = sys.argv[1]
META = sys.argv[2]
os.makedirs(OUT, exist_ok=True)

W, H = 640, 400
BG, INK, MUTED, ACC, WATER, STONE, STONE2, LINE = "#f7f1e6", "#2b2622", "#7d7266", "#b5532f", "#3d7aa8", "#e3d6c0", "#cdb898", "#d9ccb6"
FONT = "-apple-system, 'Helvetica Neue', Arial, sans-serif"


def svg(name, title, body, h=H):
    s = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" role="img" font-family="{FONT}">'
         f'<title>{esc(title)}</title>'
         f'<rect width="{W}" height="{h}" fill="{BG}"/>'
         f'{body}</svg>\n')
    with open(os.path.join(OUT, name), "w") as f:
        f.write(s)


def t(x, y, s, size=15, fill=INK, anchor="start", weight="normal", italic=False):
    st = ' font-style="italic"' if italic else ""
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}"{st}>{esc(str(s))}</text>'


def head(s, sub=""):
    out = t(24, 34, s, 19, INK, weight="700")
    if sub:
        out += t(24, 56, sub, 13.5, MUTED)
    return out


def arrow_defs():
    return (f'<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{ACC}"/></marker>'
            f'<marker id="ahi" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{INK}"/></marker>'
            f'<marker id="ahw" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{WATER}"/></marker></defs>')


def line(x1, y1, x2, y2, color=INK, w=1.5, dash=None, arrow=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    a = f' marker-end="url(#{arrow})"' if arrow else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{w}"{d}{a}/>'


# 1. Aqueduct profile ------------------------------------------------------
b = arrow_defs() + head("How water reached the palace", "Aqua Claudia, side profile. Not to scale.")
b += f'<path d="M0,120 C60,110 90,130 140,150 L140,400 L0,400 z" fill="{STONE2}"/>'
b += f'<path d="M140,300 C260,300 300,280 360,285 L360,400 L140,400 z" fill="{STONE}"/>'
b += f'<path d="M360,285 C390,280 395,250 420,250 L450,250 C460,300 480,330 520,330 C540,300 545,230 580,225 L640,225 L640,400 L360,400 z" fill="{STONE2}"/>'
b += f'<path d="M60,138 L140,175 L360,212 L600,226" fill="none" stroke="{WATER}" stroke-width="5" stroke-linecap="round"/>'
b += f'<path d="M60,138 L140,175" fill="none" stroke="{BG}" stroke-width="2" stroke-dasharray="4 5"/>'
for x in range(160, 360, 22):
    y_top = 175 + (x - 140) * (212 - 175) / 220
    b += f'<path d="M{x},{y_top+4} L{x},300 M{x+22},{y_top+4} L{x+22},300" stroke="{ACC}" stroke-width="3"/>'
    b += f'<path d="M{x},{y_top+26} Q{x+11},{y_top+10} {x+22},{y_top+26}" fill="none" stroke="{ACC}" stroke-width="3"/>'
for x in range(470, 560, 18):
    y_top = 212 + (x - 360) * (226 - 212) / 240
    b += f'<path d="M{x},{y_top+4} L{x},330 M{x+18},{y_top+4} L{x+18},330" stroke="{ACC}" stroke-width="3"/>'
    b += f'<path d="M{x},{y_top+22} Q{x+9},{y_top+9} {x+18},{y_top+22}" fill="none" stroke="{ACC}" stroke-width="3"/>'
b += f'<rect x="590" y="200" width="34" height="24" fill="{WATER}" opacity="0.8"/>'
b += t(24, 100, "Springs in the hills,", 13.5) + t(24, 116, "about 70 km east", 13.5)
b += t(14, 200, "underground channel", 12, "#5a4e42", italic=True)
b += t(200, 150, "Gentle, steady fall all the way", 13.5, WATER, weight="600")
b += t(170, 330, "Arches carry the channel", 13.5) + t(170, 346, "over low ground near Rome", 13.5)
b += t(440, 365, "Valley between Caelian", 13) + t(440, 381, "and Palatine: still on arches", 13)
b += t(632, 176, "Palatine: cisterns,", 13, anchor="end") + t(632, 192, "then lead pipes", 13, anchor="end")
b += t(400, 242, "Caelian", 12, MUTED) + t(610, 245, "Palatine", 12, MUTED, anchor="middle")
svg("aqueduct-profile.svg", "Aqueduct profile: the water falls gently from the springs and crosses low ground on arches to arrive high on the Palatine.", b)

# chorobates-free: keep set focused

# 2. Circus track ----------------------------------------------------------
b = arrow_defs() + head("Circus Maximus, seen from above", "About 600 m long. Seven laps, anticlockwise.")
b += f'<path d="M60,110 L520,110 A90,90 0 0 1 520,290 L60,290 Q48,200 60,110 z" fill="{STONE}" stroke="{STONE2}" stroke-width="10"/>'
b += f'<rect x="150" y="194" width="330" height="12" rx="6" fill="{STONE2}" stroke="{INK}" stroke-width="1"/>'
for cx in (140, 490):
    b += f'<circle cx="{cx}" cy="200" r="11" fill="{ACC}"/>'
for i in range(12):
    y = 122 + i * 13.5
    b += f'<rect x="56" y="{y}" width="14" height="10" fill="{INK}" opacity="0.7"/>'
b += f'<path d="M455,150 C530,150 545,250 455,250" fill="none" stroke="{ACC}" stroke-width="2.5" marker-end="url(#ah)"/>'
b += f'<path d="M455,250 L190,250" fill="none" stroke="{ACC}" stroke-width="2.5" marker-end="url(#ah)"/>'
b += f'<path d="M185,250 C110,250 110,150 185,150" fill="none" stroke="{ACC}" stroke-width="2.5" marker-end="url(#ah)"/>'
b += f'<path d="M190,150 L450,150" fill="none" stroke="{ACC}" stroke-width="2.5" marker-end="url(#ah)"/>'
b += t(315, 186, "spina (central barrier)", 13, INK, "middle")
b += t(120, 205, "meta", 13, ACC, "end", "600") + t(560, 205, "meta", 13, ACC, "start", "600")
b += t(80, 316, "starting gates", 13) + t(80, 332, "(carceres)", 12, MUTED)
b += t(340, 96, "Palatine side: the emperor's box looked down here", 13, INK, "middle")
b += t(340, 362, "Aventine side", 13, MUTED, "middle")
b += t(560, 340, "Crashes at the turns:", 12.5, INK, "middle") + t(560, 356, "naufragia, “shipwrecks”", 12.5, MUTED, "middle")
svg("circus-track.svg", "Circus Maximus from above: starting gates, the central spina with a turning post at each end, and the anticlockwise race.", b)

# 4. Hypocaust ---------------------------------------------------------------
b = arrow_defs() + head("How a heated floor worked (hypocaust)", "Cross-section of the palace dining hall floor.")
b += f'<rect x="120" y="180" width="460" height="22" fill="{STONE2}" stroke="{INK}"/>'
b += f'<rect x="120" y="170" width="460" height="10" fill="#e9e0f0" stroke="{INK}" stroke-width="0.8"/>'
for x in range(140, 570, 40):
    for k in range(6):
        b += f'<rect x="{x}" y="{204 + k*12}" width="22" height="11" fill="{ACC}" opacity="0.85"/>'
b += f'<rect x="120" y="276" width="460" height="10" fill="{STONE2}"/>'
b += f'<rect x="580" y="90" width="26" height="196" fill="{STONE}" stroke="{INK}"/>'
for y in range(100, 270, 22):
    b += f'<rect x="586" y="{y}" width="14" height="18" fill="none" stroke="{INK}" stroke-width="0.8"/>'
b += f'<path d="M30,240 L110,240 L110,276 L30,276 z" fill="{STONE2}" stroke="{INK}"/>'
b += f'<path d="M50,270 q8,-22 14,-4 q6,-20 14,0 q6,-14 12,4" fill="{ACC}"/>'
b += f'<path d="M110,250 C220,250 330,230 440,242 C520,248 560,250 590,250" fill="none" stroke="#d4572a" stroke-width="2.5" stroke-dasharray="6 5" marker-end="url(#ah)"/>'
b += f'<path d="M593,240 L593,92" stroke="#d4572a" stroke-width="2.5" stroke-dasharray="6 5" marker-end="url(#ah)"/>'
b += t(30, 300, "Furnace, stoked", 13) + t(30, 316, "by slaves outside", 13)
b += t(250, 330, "Hot air flows under the floor between", 13.5) + t(250, 346, "stacks of small bricks (pilae)", 13.5)
b += t(120, 160, "Marble floor on a thick mortar slab, warm underfoot", 13.5)
b += t(568, 80, "Hollow wall tiles let the air rise and escape", 13, anchor="end")
b += t(250, 375, "Look for: the brick stacks where the floor has gone.", 13.5, ACC, weight="600")
svg("hypocaust.svg", "Hypocaust: a furnace sends hot air under a floor raised on brick stacks, and out through hollow wall tiles.", b)

# 5. Iron Age hut -------------------------------------------------------------
b = arrow_defs() + head("An Iron Age hut on the Palatine", "Reconstructed from post holes cut in the rock, 8th century BC.")
b += f'<path d="M80,300 L120,200 L330,200 L370,300 z" fill="#d8c3a0" stroke="{INK}"/>'
b += f'<path d="M100,205 L225,90 L350,205 z" fill="#b99a62" stroke="{INK}"/>'
for x in range(120, 340, 14):
    b += f'<line x1="{x}" y1="205" x2="{225 + (x-225)*0.15}" y2="100" stroke="#8a7044" stroke-width="0.8"/>'
b += f'<rect x="205" y="235" width="40" height="65" fill="#5b4632"/>'
b += f'<line x1="60" y1="300" x2="390" y2="300" stroke="{INK}" stroke-width="2"/>'
b += t(120, 330, "Walls: woven branches plastered with clay", 13)
b += t(150, 80, "Thatched roof", 13)
cx, cy = 510, 220
b += f'<ellipse cx="{cx}" cy="{cy}" rx="90" ry="68" fill="none" stroke="{MUTED}" stroke-dasharray="4 4"/>'
for i in range(14):
    a = 2 * math.pi * i / 14
    b += f'<circle cx="{cx + 90*math.cos(a):.1f}" cy="{cy + 68*math.sin(a):.1f}" r="6" fill="{INK}"/>'
b += f'<circle cx="{cx}" cy="{cy}" r="7" fill="{ACC}"/>'
b += t(cx, 130, "Plan: what survives", 14, INK, "middle", "600")
b += t(cx, 312, "Ring of post holes in the bedrock,", 13, anchor="middle") + t(cx, 328, "central post for the roof", 13, anchor="middle")
svg("iron-age-hut.svg", "Iron Age hut: a thatched oval hut, and the ring of post holes in the rock that is all that survives of it.", b)

# 6. Forum plan from coordinates ------------------------------------------
meta = json.load(open(META))
st = meta["stops"]
forum_ids = {"7": "Arch of Titus", "8": "Basilica of Maxentius", "9": "Vesta & Vestals", "10": "Temple of Caesar",
             "11": "Basilica Julia", "12": "Temple of Saturn", "13": "Rostra", "14": "Arch of Severus",
             "16": "Senate House", "17": "Basilica Aemilia", "18": "Antoninus & Faustina", "6": "Farnese terrace (you)"}
lats = [st[k]["lat"] for k in forum_ids]; lons = [st[k]["lon"] for k in forum_ids]
la0, la1, lo0, lo1 = min(lats), max(lats), min(lons), max(lons)
kx = 82650; ky = 111000
sc = min(400 / ((lo1 - lo0) * kx), 270 / ((la1 - la0) * ky))
def P(lat, lon):
    return 150 + (lon - lo0) * kx * sc, 92 + (la1 - lat) * ky * sc
b = arrow_defs() + head("The Forum from the Farnese terrace", "Plan view, north up. You walk from the Arch of Titus (right) to the exit (top).")
order = ["7", "8", "9", "10", "11", "12", "13", "14", "16", "17", "18"]
pts = " ".join(f"{P(st[k]['lat'], st[k]['lon'])[0]:.0f},{P(st[k]['lat'], st[k]['lon'])[1]:.0f}" for k in order)
b += f'<polyline points="{pts}" fill="none" stroke="{ACC}" stroke-width="3" stroke-dasharray="8 6" stroke-linejoin="round"/>'
offs = {"7": (-12, 4), "8": (10, -10), "9": (-6, 22), "10": (10, -10), "11": (-8, 22), "12": (-10, 18), "13": (-12, 4),
        "14": (-12, -12), "16": (10, -12), "17": (10, -10), "18": (12, 4), "6": (12, -6)}
anch = {"7": "end", "12": "end", "13": "end", "14": "end", "11": "end", "9": "end"}
for k, name in forum_ids.items():
    x, y = P(st[k]["lat"], st[k]["lon"])
    col = WATER if k == "6" else INK
    b += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="7" fill="{col}"/>'
    dx, dy = offs[k]
    b += t(f"{x+dx:.0f}", f"{y+dy:.0f}", f"{k}  {name}", 12.5, col, anch.get(k, "start"), "600")
b += t(24, 392, "← west: Capitoline Hill", 13, MUTED)
b += t(616, 392, "east: Colosseum →", 13, MUTED, "end")
svg("forum-plan.svg", "Forum plan, north up: the numbered stops from the Arch of Titus west to the Temple of Antoninus and Faustina by the exit.", b)

# 7. Arch of Titus restoration ---------------------------------------------
b = arrow_defs() + head("Arch of Titus: old and new", "In 1821 Valadier rebuilt the sides in plain travertine.")
X0, X1 = 140, 500
b += f'<rect x="{X0}" y="80" width="{X1-X0}" height="290" fill="#e8dcc6" stroke="{INK}"/>'
b += f'<rect x="250" y="80" width="140" height="290" fill="#fbf8f2" stroke="{INK}"/>'
b += f'<rect x="{X0}" y="80" width="{X1-X0}" height="62" fill="none" stroke="{INK}"/>'
b += t(320, 106, "SENATVS", 11, INK, "middle", "700") + t(320, 122, "POPVLVSQVE", 11, INK, "middle", "700") + t(320, 138, "ROMANVS", 11, INK, "middle", "700")
b += f'<path d="M270,370 L270,230 A50,50 0 0 1 370,230 L370,370 z" fill="{BG}" stroke="{INK}"/>'
for x in (180, 230, 410, 460):
    b += f'<rect x="{x-6}" y="160" width="12" height="200" fill="none" stroke="{INK}" stroke-width="0.8"/>'
b += f'<rect x="30" y="110" width="16" height="16" fill="#fbf8f2" stroke="{INK}"/>' + t(52, 123, "Original", 13) + t(52, 139, "marble", 13)
b += f'<rect x="30" y="160" width="16" height="16" fill="#e8dcc6" stroke="{INK}"/>' + t(52, 173, "1821", 13) + t(52, 189, "travertine", 13)
b += t(320, 395, "Simpler new parts so anyone can tell old from new", 13, ACC, "middle", "600")
b += t(512, 214, "Inside the", 13) + t(512, 230, "passage: the", 13) + t(512, 246, "menorah relief", 13)
b += line(508, 240, 372, 280, ACC, 1.5, arrow="ah")
svg("arch-titus-restoration.svg", "Arch of Titus: the original marble centre and the plainer travertine sides added in the 1821 restoration.", b)

# 8. Vault loads -------------------------------------------------------------
b = arrow_defs() + head("How the Basilica of Maxentius stood", "Cross-section. Everything works in compression.")
g = 340
b += f'<line x1="40" y1="{g}" x2="600" y2="{g}" stroke="{INK}" stroke-width="2"/>'
b += f'<path d="M190,{g} L190,170 Q320,60 450,170 L450,{g} L420,{g} L420,180 Q320,95 220,180 L220,{g} z" fill="{STONE2}" stroke="{INK}"/>'
b += f'<path d="M70,{g} L70,240 Q130,180 190,230 L190,{g} L175,{g} L175,245 Q130,205 85,250 L85,{g} z" fill="{STONE}" stroke="{INK}"/>'
b += f'<path d="M570,{g} L570,240 Q510,180 450,230 L450,{g} L465,{g} L465,245 Q510,205 555,250 L555,{g} z" fill="{STONE}" stroke="{INK}"/>'
b += line(320, 110, 320, 150, ACC, 2.5, arrow="ah")
b += line(240, 160, 205, 220, ACC, 2.5, arrow="ah") + line(400, 160, 435, 220, ACC, 2.5, arrow="ah")
b += line(205, 260, 205, 330, ACC, 2.5, arrow="ah") + line(435, 260, 435, 330, ACC, 2.5, arrow="ah")
b += line(150, 280, 185, 280, INK, 2, arrow="ahi") + line(490, 280, 455, 280, INK, 2, arrow="ahi")
b += t(320, 205, "Central hall", 13.5, INK, "middle", "600") + t(320, 222, "cross vaults, ~35 m high", 12.5, MUTED, "middle")
b += t(110, 370, "Side bays (what you see today)", 12.5, INK, "start")
b += t(30, 150, "Weight flows down", 13, ACC, weight="600") + t(30, 166, "into massive piers", 13, ACC)
b += t(470, 120, "Vaults push outward;", 13, INK) + t(470, 136, "side bays push back", 13, INK)
b += t(320, 392, "Concrete is strong when squeezed, weak when stretched", 13, MUTED, "middle", italic=True)
svg("vault-loads.svg", "Basilica of Maxentius in section: the central vaults send weight down into the piers, and the side bays brace them against spreading.", b)

# 9. Vestal career -----------------------------------------------------------
b = head("A Vestal's 30 years", "Chosen as a girl aged 6 to 10.")
segs = [("Learning", "years 1–10", "#e3c9a8"), ("Performing the rites", "years 11–20", ACC), ("Teaching new Vestals", "years 21–30", "#7a4a35")]
for i, (a_, bb, c) in enumerate(segs):
    x = 40 + i * 170
    b += f'<rect x="{x}" y="100" width="168" height="54" fill="{c}"/>'
    col = INK if i == 0 else "#fff"
    b += t(x + 84, 126, a_, 13.5, col, "middle", "600") + t(x + 84, 144, bb, 12, col, "middle")
b += f'<rect x="550" y="100" width="60" height="54" fill="none" stroke="{INK}" stroke-dasharray="4 3"/>'
b += t(580, 126, "Free", 13, INK, "middle", "600") + t(580, 142, "to leave", 12, INK, "middle")
b += t(40, 200, "Privileges: own property, make a will, official escort, front-row seats.", 13.5)
b += t(40, 222, "Price: strict chastity. Breaking it was punished by burial alive.", 13.5)
b += t(40, 258, "After 30 years a Vestal could leave and even marry. Few did.", 13.5, MUTED)
svg("vestal-career.svg", "A Vestal's 30-year service: ten years learning, ten performing the rites, ten teaching, then free to leave.", b, 290)

# 10. Republic timeline ------------------------------------------------------
b = head("How the Republic ended", "From the Rubicon to Augustus in 22 years.")
ev = [(49, "Caesar crosses", "the Rubicon"), (44, "Caesar killed;", "cremated here"), (43, "Triumvirs' death", "lists; Cicero killed"),
      (42, "Philippi: Brutus", "& Cassius lose"), (31, "Actium: Antony", "& Cleopatra lose"), (29, "Temple of the", "Divine Julius"), (27, "Octavian becomes", "Augustus")]
b += line(120, 82, 120, 92 + 6*40, INK, 2)
for i, (yr, a_, bb) in enumerate(ev):
    y = 92 + i * 40
    hi = yr in (44, 27)
    b += f'<circle cx="120" cy="{y}" r="7" fill="{ACC if hi else INK}"/>'
    b += t(100, y + 5, f"{yr} BC", 14, ACC, "end", "700")
    b += t(140, y + 5, a_ + " " + bb, 14, INK, weight="600" if hi else "normal")
b += t(140, 380, "A killing meant to save the Republic ended in monarchy.", 13.5, MUTED, italic=True)
svg("republic-timeline.svg", "Timeline 49 to 27 BC: Rubicon, Caesar's murder, Cicero's death, Philippi, Actium, the Temple of Caesar, Augustus.", b, 400)

# 14. Severus inscription ------------------------------------------------------
b = head("Erasing Geta: line 4 of the inscription", "The bronze letters sat in sockets. New words, old holes.")
b += f'<rect x="30" y="80" width="580" height="200" fill="{STONE}" stroke="{INK}"/>'
for i, y in enumerate((110, 140, 170)):
    b += f'<rect x="60" y="{y-14}" width="520" height="16" fill="{STONE2}" opacity="0.7"/>'
b += t(320, 120, "line 1 · Septimius Severus", 12, MUTED, "middle", italic=True)
b += t(320, 150, "line 2 · his titles", 12, MUTED, "middle", italic=True)
b += t(320, 180, "line 3 · Caracalla", 12, MUTED, "middle", italic=True)
b += f'<rect x="50" y="198" width="540" height="56" fill="#f3e2d9" stroke="{ACC}" stroke-width="2"/>'
b += t(320, 220, "Original (from the socket holes): P·SEPTIMIO·L·FIL·GETAE·NOBILISS·CAESARI", 12.5, MUTED, "middle")
b += t(320, 243, "Recut: OPTIMIS·FORTISSIMISQVE·PRINCIPIBVS", 14, INK, "middle", "700")
b += t(30, 310, "Original: “to Publius Septimius Geta, son of Lucius, most noble Caesar”", 13.5)
b += t(30, 332, "Replacement: “to the best and bravest emperors”", 13.5)
b += t(30, 362, "Look for: holes on line 4 that do not fit the letters.", 13.5, ACC, weight="600")
svg("severus-inscription.svg", "Arch of Septimius Severus: line 4 originally named Geta and was recut to praise the best and bravest emperors.", b, 380)

# 15. Boustrophedon ------------------------------------------------------------
b = arrow_defs() + head("Writing like an ox ploughs", "The Lapis Niger pillar, 6th century BC: lines change direction.")
b += f'<path d="M230,80 L410,80 L400,380 L240,380 z" fill="{STONE}" stroke="{INK}"/>'
for i in range(6):
    y = 110 + i * 46
    if i % 2 == 0:
        b += f'<path d="M262,{y} L376,{y}" stroke="{ACC}" stroke-width="2.5" marker-end="url(#ah)"/>'
    else:
        b += f'<path d="M376,{y} L262,{y}" stroke="{ACC}" stroke-width="2.5" marker-end="url(#ah)"/>'
    if i < 5:
        side = 382 if i % 2 == 0 else 256
        b += f'<path d="M{side},{y} q{14 if i%2==0 else -14},23 0,46" fill="none" stroke="{MUTED}" stroke-dasharray="3 3"/>'
b += t(430, 140, "Left to right,", 13.5) + t(430, 158, "then right to left,", 13.5) + t(430, 176, "then back again", 13.5)
b += t(430, 230, "Contains the word", 13.5) + t(430, 248, "for king", 13.5, ACC, weight="600")
b += t(40, 200, "Oldest known", 13.5) + t(40, 218, "Latin public", 13.5) + t(40, 236, "inscription", 13.5)
svg("boustrophedon.svg", "The Lapis Niger inscription runs boustrophedon: each line reverses direction, like an ox ploughing a field.", b)

# 18. Ground levels -------------------------------------------------------------
b = arrow_defs() + head("How deep the Forum was buried", "Temple of Antoninus and Faustina, front view.")
b += f'<rect x="120" y="270" width="400" height="80" fill="{STONE2}" stroke="{INK}"/>'
for x in range(150, 500, 60):
    b += f'<rect x="{x}" y="110" width="22" height="160" fill="#e8e2d6" stroke="{INK}"/>'
b += f'<rect x="130" y="88" width="380" height="22" fill="{STONE}" stroke="{INK}"/>'
b += f'<rect x="295" y="160" width="50" height="80" fill="#6b4f36"/>'
b += line(40, 350, 600, 350, INK, 2) + t(600, 372, "Ancient ground level", 13, INK, "end", "600")
b += line(40, 240, 600, 240, ACC, 2, dash="8 6") + t(600, 232, "Medieval ground level", 13, ACC, "end", "600")
b += f'<rect x="40" y="240" width="80" height="110" fill="{ACC}" opacity="0.12"/>' + f'<rect x="520" y="240" width="80" height="110" fill="{ACC}" opacity="0.12"/>'
b += line(80, 340, 80, 252, INK, 1.5, arrow="ahi") + t(90, 300, "metres of", 12.5) + t(90, 316, "soil and rubble", 12.5)
b += t(320, 150, "Church door", 13, INK, "middle", "600")
b += t(320, 395, "The door was set at the level people walked on in the Middle Ages.", 12.5, MUTED, "middle")
svg("ground-levels.svg", "Temple of Antoninus and Faustina: the church door sits at the medieval ground level, metres above the ancient one.", b)

# 19. Treadwheel crane -------------------------------------------------------
b = arrow_defs() + head("Treadwheel crane", "Men walking inside the wheel lifted blocks of several tonnes.")
g = 360
b += line(30, g, 610, g, INK, 2)
b += f'<line x1="200" y1="{g}" x2="330" y2="80" stroke="#8a6a44" stroke-width="9"/>'
b += f'<line x1="300" y1="{g}" x2="330" y2="80" stroke="#8a6a44" stroke-width="9"/>'
b += f'<circle cx="160" cy="280" r="76" fill="none" stroke="#8a6a44" stroke-width="7"/>'
for i in range(8):
    a = math.pi * i / 4
    b += line(160, 280, 160 + 76 * math.cos(a), 280 + 76 * math.sin(a), "#8a6a44", 2)
b += f'<circle cx="152" cy="316" r="8" fill="{INK}"/>' + f'<line x1="152" y1="324" x2="148" y2="350" stroke="{INK}" stroke-width="4"/>'
b += f'<path d="M160,280 L330,84 L470,84" fill="none" stroke="{INK}" stroke-width="1.5"/>'
b += line(330, 80, 470, 84, "#8a6a44", 6)
b += f'<circle cx="470" cy="90" r="9" fill="none" stroke="{INK}" stroke-width="2"/>'
b += f'<circle cx="470" cy="160" r="9" fill="none" stroke="{INK}" stroke-width="2"/>'
b += line(462, 92, 462, 160, INK, 1.5) + line(478, 92, 478, 160, INK, 1.5) + line(470, 169, 470, 230, INK, 1.5)
b += f'<rect x="425" y="230" width="90" height="56" fill="{STONE}" stroke="{INK}"/>' + t(470, 263, "travertine", 12, INK, "middle")
b += line(470, 300, 470, 340, ACC, 2.5, arrow="ah")
b += t(40, 180, "Walking turns", 13) + t(40, 196, "the wheel", 13)
b += t(500, 130, "Pulley block:", 13) + t(500, 146, "more pulleys,", 13) + t(500, 162, "less effort", 13)
b += t(330, 390, "Big wheel + pulleys = a few men lift several tonnes", 13, ACC, "middle", "600")
svg("treadwheel-crane.svg", "Roman treadwheel crane: men walking inside a wheel wind a rope through pulleys to lift heavy stone blocks.", b, 400)

# 21. Colosseum section -------------------------------------------------------
b = arrow_defs() + head("The Colosseum in cross-section", "From the outer wall (right) to the arena (left). About 48 m high.")
g = 340
b += line(20, g, 620, g, INK, 2)
pts = []
x, y = 160, g - 55
steps = [(160, g-55), (200, g-55), (200, g-75), (260, g-75), (260, g-100), (330, g-100), (330, g-130), (400, g-130), (400, g-165), (480, g-165), (480, g-200), (540, g-200), (540, 120), (560, 120)]
d = "M" + " L".join(f"{a},{c}" for a, c in steps) + f" L560,{g} L160,{g} Z"
b += f'<path d="{d}" fill="{STONE}" stroke="{INK}" stroke-width="1" opacity="1"/>'
b += f'<rect x="560" y="70" width="30" height="{g-70}" fill="#eadfca" stroke="{INK}"/>'
for y in (130, 190, 250):
    b += line(560, y, 590, y, INK, 1)
for x in (470, 380):
    b += f'<rect x="{x}" y="{170 if x==470 else 230}" width="20" height="{g-(170 if x==470 else 230)}" fill="{STONE2}" stroke="{INK}"/>'
b += f'<path d="M490,{g-40} Q525,{g-80} 560,{g-40}" fill="none" stroke="{INK}" stroke-width="2"/>'
b += f'<path d="M400,{g-40} Q435,{g-80} 470,{g-40}" fill="none" stroke="{INK}" stroke-width="2"/>'
b += f'<path d="M150,{g-40} L150,{g-70} L560,110 L560,130 Z" fill="none" stroke="none"/>'

b += f'<rect x="20" y="{g-40}" width="140" height="10" fill="#d9c08a"/>'
b += f'<rect x="20" y="{g-30}" width="140" height="30" fill="none" stroke="{MUTED}" stroke-dasharray="4 3"/>'
b += t(90, g - 50, "arena floor", 12.5, INK, "middle") + t(90, g - 10, "hypogeum below", 12, MUTED, "middle")
b += t(162, g - 62, "podium", 12, INK)
b += t(552, 84, "Outer wall:", 12.5, INK, "end", "600") + t(552, 100, "travertine", 12.5, INK, "end")
b += t(380, 375, "Ring corridors under the seating", 12.5, INK, "middle")
b += t(250, 140, "Seats rest on sloping vaults", 12.5) + t(250, 156, "carried by radial walls (tufa, brick)", 12.5)
b += t(250, 172, "and concrete, lighter higher up", 12.5)
svg("colosseum-section.svg", "Colosseum cross-section: travertine outer wall, ring corridors and radial walls under sloping seating, the podium, the arena and the hypogeum below.", b, 390)

# 21b. Iron clamp ------------------------------------------------------------------
b = head("Why the walls are full of holes", "Blocks were joined with iron clamps set in lead, not mortar.")
b += f'<rect x="80" y="120" width="230" height="150" fill="{STONE}" stroke="{INK}"/>'
b += f'<rect x="310" y="120" width="230" height="150" fill="{STONE}" stroke="{INK}"/>'
b += f'<rect x="250" y="108" width="120" height="24" fill="#9aa3a8" stroke="{INK}"/>'
b += f'<rect x="250" y="108" width="14" height="40" fill="#9aa3a8" stroke="{INK}"/>' + f'<rect x="356" y="108" width="14" height="40" fill="#9aa3a8" stroke="{INK}"/>'
b += f'<rect x="244" y="104" width="132" height="6" fill="#c7ccd0"/>'
b += t(310, 96, "Iron clamp, sealed with molten lead", 13.5, INK, "middle", "600")
b += t(80, 300, "Medieval Romans chiselled into the joints to take the iron and lead,", 13.5)
b += t(80, 320, "leaving the pock-marks you see all over the travertine.", 13.5)
b += t(80, 356, "Estimated iron in the building: about 300 tonnes.", 13.5, ACC, weight="600")
svg("iron-clamp.svg", "Travertine blocks joined by an iron clamp set in lead; robbing the clamps left the holes in the Colosseum's walls.", b, 380)

# 22. Seating section ----------------------------------------------------------
b = head("Where you sat showed who you were", "Seating zones, simplified. About 50,000 spectators.")
zones = [("Arena", "", "#d9c08a", 30, 300, 90, 40),
         ("Podium", "senators, Vestals", "#7a4a35", 120, 270, 90, 70),
         ("First tier", "knights", ACC, 210, 230, 100, 110),
         ("Second tier", "citizens in togas", "#d0875f", 310, 180, 110, 160),
         ("Third tier", "poorer men", "#e3c9a8", 420, 130, 90, 210),
         ("Top, under the colonnade", "most women, slaves", "#eadfca", 510, 80, 100, 260)]
for name, who, c, x, y, w_, h_ in zones:
    b += f'<rect x="{x}" y="{y}" width="{w_}" height="{h_}" fill="{c}" stroke="{BG}" stroke-width="2"/>'
    col = "#fff" if c in ("#7a4a35", ACC) else INK
    if name == "Top, under the colonnade":
        b += t(x + w_/2, y + 22, "Top tier", 13, col, "middle", "700") + t(x + w_/2, y + 40, "wooden benches", 11.5, col, "middle")
        b += t(x + w_/2, y + 56, "most women,", 11.5, col, "middle") + t(x + w_/2, y + 70, "slaves", 11.5, col, "middle")
    else:
        b += t(x + w_/2, y + 22, name, 13, col, "middle", "700")
        if who:
            for i, part in enumerate(who.split(", ")):
                b += t(x + w_/2, y + 40 + i*15, part, 11.5, col, "middle")
b += t(30, 372, "Emperor's box: middle of a long side, at podium level.", 13.5, INK)
svg("seating-section.svg", "Seating zones from the arena upward: senators on the podium, then knights, citizens, poorer men, and women at the top.", b, 390)

# 23. Hypogeum lift ------------------------------------------------------------
b = arrow_defs() + head("A lift from the underground", "Reconstruction of one lift. Scholars estimate dozens.")
b += f'<rect x="20" y="110" width="600" height="14" fill="#d9c08a" stroke="{INK}"/>'
b += f'<rect x="300" y="110" width="80" height="14" fill="{BG}"/>'
b += f'<path d="M300,110 L262,76" stroke="{INK}" stroke-width="5"/>' + t(250, 72, "trapdoor", 12.5, INK, "end")
b += t(30, 100, "Arena floor: wood covered in sand", 12.5)
b += f'<rect x="295" y="124" width="6" height="240" fill="{STONE2}"/>' + f'<rect x="379" y="124" width="6" height="240" fill="{STONE2}"/>'
b += f'<rect x="305" y="250" width="70" height="80" fill="none" stroke="{INK}" stroke-width="2.5"/>'
for x in range(315, 375, 12):
    b += line(x, 250, x, 330, INK, 1)
b += t(340, 352, "cage", 12.5, INK, "middle")
b += f'<circle cx="340" cy="140" r="9" fill="none" stroke="{INK}" stroke-width="2"/>'
b += line(340, 149, 340, 250, INK, 1.5) + line(331, 140, 180, 290, INK, 1.5)
b += f'<rect x="160" y="290" width="40" height="70" fill="#8a6a44" stroke="{INK}"/>'
b += line(120, 300, 240, 300, "#8a6a44", 5)
b += f'<circle cx="112" cy="300" r="8" fill="{INK}"/>' + f'<circle cx="248" cy="300" r="8" fill="{INK}"/>'
b += t(180, 386, "capstan, turned by men pushing bars", 12.5, INK, "middle")
b += line(440, 330, 440, 160, ACC, 2.5, arrow="ah") + t(452, 240, "cage rises,", 13, ACC, weight="600") + t(452, 256, "trapdoor opens", 13, ACC)
b += t(452, 300, "Guides in the wall slots", 12.5, MUTED) + t(452, 316, "kept the cage straight", 12.5, MUTED)
b += line(20, 364, 620, 364, INK, 2)
svg("hypogeum-lift.svg", "One hypogeum lift: men at a capstan wind a rope over a pulley to raise a cage through a trapdoor in the arena floor.", b, 400)

# 24. Velarium --------------------------------------------------------------------
b = head("The velarium: two theories", "240 masts on the top of the outer wall held the ropes.")
for i, (cx, label) in enumerate(((165, "A. One ring, pulled by ropes"), (475, "B. Separate sail sections"))):
    cy = 215
    b += f'<ellipse cx="{cx}" cy="{cy}" rx="135" ry="110" fill="{STONE}" stroke="{INK}"/>'
    b += f'<ellipse cx="{cx}" cy="{cy}" rx="45" ry="34" fill="#d9c08a" stroke="{INK}"/>'
    for k in range(24):
        a = 2 * math.pi * k / 24
        ox, oy = cx + 135 * math.cos(a), cy + 110 * math.sin(a)
        b += f'<circle cx="{ox:.1f}" cy="{oy:.1f}" r="3" fill="{INK}"/>'
        if i == 0:
            b += line(ox, oy, cx + 45 * math.cos(a), cy + 34 * math.sin(a), WATER, 1)
    if i == 0:
        b += f'<ellipse cx="{cx}" cy="{cy}" rx="45" ry="34" fill="none" stroke="{WATER}" stroke-width="3"/>'
    else:
        for k in range(12):
            a0 = 2 * math.pi * k / 12 + 0.06; a1 = 2 * math.pi * (k + 1) / 12 - 0.06
            pts_ = [(cx + 132 * math.cos(a0), cy + 107 * math.sin(a0)), (cx + 132 * math.cos(a1), cy + 107 * math.sin(a1)),
                    (cx + 50 * math.cos(a1), cy + 38 * math.sin(a1)), (cx + 50 * math.cos(a0), cy + 38 * math.sin(a0))]
            b += '<polygon points="' + " ".join(f"{p:.1f},{q:.1f}" for p, q in pts_) + f'" fill="{WATER}" opacity="0.25" stroke="{WATER}"/>'
    b += t(cx, 352, label, 13.5, INK, "middle", "600")
b += t(320, 382, "Worked by sailors from the fleet at Misenum. Wind loads were enormous.", 12.5, MUTED, "middle")
svg("velarium.svg", "Two theories for the Colosseum's awning: a central ring held by radial ropes, or separate sail sections between masts.", b, 395)

print("ok", len([f for f in os.listdir(OUT) if f.endswith('.svg')]))
