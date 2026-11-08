/* Rome Walk: offline audio walking guide.
   Plain JavaScript, no build step. Content comes from data/stops.js (window.GUIDE). */
(function () {
  "use strict";

  const G = window.GUIDE;
  const STOPS = G.stops;
  const byN = Object.fromEntries(STOPS.map((s) => [s.n, s]));
  const THREADS = ["Politics", "Engineering", "Daily life", "Philosophy"];
  const NEAR_RADIUS_M = 35;

  /* ---------- Settings (stored on this phone only) ---------- */
  const store = {
    get(k, d) { try { const v = localStorage.getItem("rw." + k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem("rw." + k, JSON.stringify(v)); } catch (e) { /* private mode */ } },
  };
  const S = {
    visited: new Set(store.get("visited", [])),
    coreOnly: store.get("coreOnly", false),
    thread: store.get("thread", ""),
    voice: store.get("voice", ""),
    rate: store.get("rate", 1.0),
    autoplay: store.get("autoplay", false),
    gps: store.get("gps", false),
  };
  const saveVisited = () => store.set("visited", [...S.visited]);

  /* ---------- Helpers ---------- */
  const $ = (sel, el = document) => el.querySelector(sel);
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const paras = (text) => text.split(/\n\n+/).filter(Boolean);
  const minutesOf = (text) => Math.max(1, Math.round(text.split(/\s+/).length / 150 / S.rate));
  function distM(a, b) {
    const R = 6371000, toR = Math.PI / 180;
    const dLat = (b.lat - a.lat) * toR, dLon = (b.lon - a.lon) * toR;
    const h = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * toR) * Math.cos(b.lat * toR) * Math.sin(dLon / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(h));
  }
  const fmtDist = (m) => (m < 1000 ? Math.round(m / 5) * 5 + " m" : (m / 1000).toFixed(1) + " km");
  const mapsLink = (lat, lon, name) => `https://maps.apple.com/?ll=${lat},${lon}&q=${encodeURIComponent(name)}`;

  /* ---------- Audio engine: recorded file if present, else the phone's voice ---------- */
  const Player = {
    stop: null, part: null, chunks: [], idx: 0, playing: false, audioEl: null, utter: null, token: 0,

    voices() { return (window.speechSynthesis && speechSynthesis.getVoices()) || []; },
    pickVoice() {
      const vs = this.voices().filter((v) => /^en/i.test(v.lang));
      if (S.voice) { const v = vs.find((x) => x.voiceURI === S.voice); if (v) return v; }
      const score = (v) => (/premium/i.test(v.name) ? 30 : 0) + (/enhanced/i.test(v.name) ? 20 : 0) +
        (/en-GB/i.test(v.lang) ? 5 : 0) + (/en-US/i.test(v.lang) ? 3 : 0) + (v.localService ? 2 : 0) -
        (/(compact|eloquence|novelty|bells|bubbles|cellos|organ|whisper|zarvox|trinoids|bahh|boing|jester|superstar|wobble|albert|bad news|good news)/i.test(v.name) ? 50 : 0);
      return vs.sort((a, b) => score(b) - score(a))[0] || null;
    },

    start(stop, part) {
      this.halt(true);
      this.stop = stop; this.part = part; this.idx = 0; this.token++;
      const text = part === "deep" ? stop.deep : stop.core;
      // chunk = one or two sentences, tagged with its paragraph for highlighting
      this.chunks = [];
      paras(text).forEach((p, pi) => {
        const sentences = p.match(/[^.!?]+[.!?]+["”']?(\s|$)|[^.!?]+$/g) || [p];
        let buf = "";
        sentences.forEach((s) => {
          buf += s;
          if (buf.length > 160) { this.chunks.push({ t: buf.trim(), p: pi }); buf = ""; }
        });
        if (buf.trim()) this.chunks.push({ t: buf.trim(), p: pi });
      });
      const file = stop.audio && stop.audio[part];
      this.showBar();
      // play through the speaker even when the iPhone's silent switch is on (Safari 17+)
      try { if (navigator.audioSession) navigator.audioSession.type = "playback"; } catch (e) {}
      this.playing = true;
      if (file) this.playFile(file); else this.speakNext();
      this.updateBar();
    },

    playFile(src) {
      const a = this.audioEl || (this.audioEl = new Audio());
      a.src = src; a.playbackRate = 1; a.currentTime = 0;
      a.ontimeupdate = () => { if (a.duration) this.setProgress(a.currentTime / a.duration); };
      a.onended = () => this.finished();
      a.play().catch(() => { this.audioEl = null; this.speakNext(); });
      if ("mediaSession" in navigator) {
        navigator.mediaSession.metadata = new MediaMetadata({ title: this.stop.n + ". " + this.stop.title, artist: "Rome Walk",
          artwork: [{ src: "icons/icon-512.png", sizes: "512x512", type: "image/png" }] });
        navigator.mediaSession.setActionHandler("play", () => this.toggle());
        navigator.mediaSession.setActionHandler("pause", () => this.toggle());
      }
    },

    speakNext() {
      if (!window.speechSynthesis) { alert("This browser cannot read text aloud. Read the text on screen instead."); this.halt(); return; }
      if (this.idx >= this.chunks.length) { this.finished(); return; }
      const c = this.chunks[this.idx];
      const u = new SpeechSynthesisUtterance(c.t);
      // a chosen voice that is not downloaded can be silent on iOS: after one silent attempt, use the default
      const v = this.plainVoice ? null : this.pickVoice();
      if (v) { u.voice = v; u.lang = v.lang; } else { u.lang = "en-GB"; }
      u.rate = S.rate; u.pitch = 1;
      const tok = this.token;
      let started = false;
      u.onstart = () => { started = true; };
      u.onend = () => { if (tok !== this.token || !this.playing) return; this.idx++; this.speakNext(); };
      u.onerror = (e) => { if (tok !== this.token) return; if (e.error === "interrupted" || e.error === "canceled") return; this.idx++; this.speakNext(); };
      this.utter = u;
      // iOS drops an utterance queued right after cancel(), so give the engine a moment
      const go = () => {
        if (tok !== this.token) return;
        speechSynthesis.resume();
        speechSynthesis.speak(u);
        setTimeout(() => {
          if (tok !== this.token || started || !this.playing || this.plainVoice) return;
          this.plainVoice = true; this.token++; speechSynthesis.cancel();
          setTimeout(() => this.speakNext(), 150);
        }, 2500);
      };
      if (speechSynthesis.speaking || speechSynthesis.pending) setTimeout(go, 150); else go();
      this.highlight(c.p);
      this.setProgress(this.idx / this.chunks.length);
    },

    toggle() {
      if (!this.stop) return;
      if (this.audioEl && this.audioEl.src && !this.audioEl.ended && this.stop.audio && this.stop.audio[this.part]) {
        if (this.audioEl.paused) { this.audioEl.play(); this.playing = true; } else { this.audioEl.pause(); this.playing = false; }
      } else if (this.playing) {
        // iOS pause/resume for speech is unreliable: cancel and remember the position instead
        this.playing = false; this.token++; speechSynthesis.cancel();
      } else {
        this.playing = true; this.token++; this.speakNext();
      }
      this.updateBar();
    },

    back() {
      if (!this.stop) return;
      if (this.audioEl && this.stop.audio && this.stop.audio[this.part]) { this.audioEl.currentTime = Math.max(0, this.audioEl.currentTime - 10); return; }
      this.idx = Math.max(0, this.idx - 1);
      if (this.playing) { this.token++; speechSynthesis.cancel(); this.speakNext(); }
    },

    halt(keepBar) {
      this.token++; this.playing = false;
      if (window.speechSynthesis && (speechSynthesis.speaking || speechSynthesis.pending)) speechSynthesis.cancel();
      if (this.audioEl) { this.audioEl.pause(); }
      this.highlight(-1);
      if (!keepBar) { this.stop = null; $("#player").hidden = true; }
      this.updateBar();
    },

    finished() {
      const s = this.stop, part = this.part;
      this.playing = false; this.setProgress(1); this.highlight(-1); this.updateBar();
      $("#playerSub").textContent = part === "core" && s.deep ? "Finished. Deep dive available on the stop page." : "Finished";
    },

    showBar() { $("#player").hidden = false; },
    updateBar() {
      if (!this.stop) return;
      $("#playerTitle").textContent = this.stop.n + ". " + this.stop.title;
      const label = this.part === "deep" ? "Deep dive" : (this.stop.isCore ? "Core" : "Stop");
      $("#playerSub").textContent = label + (this.playing ? " · playing" : " · paused");
      const b = $("#pToggle");
      b.innerHTML = this.playing ? "&#10074;&#10074;" : "&#9654;";
      b.setAttribute("aria-label", this.playing ? "Pause" : "Play");
    },
    setProgress(f) { $("#playerProgress").style.width = Math.round(f * 100) + "%"; },
    highlight(pi) {
      document.querySelectorAll(".prose p.speaking").forEach((p) => p.classList.remove("speaking"));
      if (pi < 0 || !this.stop) return;
      const el = document.querySelector(`.prose[data-stop="${this.stop.n}"][data-part="${this.part}"] p[data-p="${pi}"]`);
      if (el) el.classList.add("speaking");
    },
  };
  $("#pToggle").onclick = () => Player.toggle();
  $("#pStop").onclick = () => Player.halt();
  $("#pBack").onclick = () => Player.back();
  if (window.speechSynthesis) speechSynthesis.onvoiceschanged = () => { if (location.hash.startsWith("#/plan")) render(); };

  /* ---------- GPS ---------- */
  const Geo = { watch: null, pos: null, err: "", dismissed: new Set(), lastAuto: 0 };
  function startGps() {
    if (!("geolocation" in navigator)) { Geo.err = "This browser has no GPS access."; return; }
    if (Geo.watch !== null) return;
    S.gps = true; store.set("gps", true);
    Geo.watch = navigator.geolocation.watchPosition(
      (p) => { Geo.pos = { lat: p.coords.latitude, lon: p.coords.longitude, acc: p.coords.accuracy }; Geo.err = ""; onPosition(); },
      (e) => { Geo.err = e.code === 1 ? "Location permission was refused. Allow it in Settings > Privacy > Location Services > Safari Websites." : "Waiting for a GPS fix..."; onPosition(); },
      { enableHighAccuracy: true, maximumAge: 5000, timeout: 30000 });
  }
  function stopGps() {
    if (Geo.watch !== null) navigator.geolocation.clearWatch(Geo.watch);
    Geo.watch = null; Geo.pos = null; S.gps = false; store.set("gps", false); onPosition();
  }
  function nearest() {
    if (!Geo.pos) return null;
    let best = null;
    STOPS.forEach((s) => { const d = distM(Geo.pos, s); if (!best || d < best.d) best = { s, d }; });
    return best;
  }
  function onPosition() {
    const view = currentView();
    if (view === "map") drawMap(false);
    if (view === "route") updateDistances();
    const nb = $("#near");
    const n = nearest();
    if (!n || n.d > NEAR_RADIUS_M || S.visited.has(n.s.n) || Geo.dismissed.has(n.s.n) ||
        (Player.stop && Player.stop.n === n.s.n)) { nb.hidden = true; return; }
    if (S.autoplay && !Player.playing && Date.now() - Geo.lastAuto > 60000) {
      Geo.lastAuto = Date.now(); Geo.dismissed.add(n.s.n); Player.start(n.s, "core"); nb.hidden = true; return;
    }
    nb.innerHTML = `<span>You are at stop ${n.s.n}: ${esc(n.s.title)}</span><span><button data-play="${n.s.n}">Play</button> <button data-x="${n.s.n}" aria-label="Dismiss">&times;</button></span>`;
    nb.hidden = false;
    nb.classList.toggle("low", $("#player").hidden);
  }
  $("#near").addEventListener("click", (e) => {
    const p = e.target.closest("[data-play]"), x = e.target.closest("[data-x]");
    if (p) { const s = byN[+p.dataset.play]; Geo.dismissed.add(s.n); location.hash = "#/stop/" + s.n; Player.start(s, "core"); $("#near").hidden = true; }
    if (x) { Geo.dismissed.add(+x.dataset.x); $("#near").hidden = true; }
  });

  /* ---------- Views ---------- */
  function currentView() {
    const h = location.hash;
    if (h.startsWith("#/stop/")) return "stop";
    if (h.startsWith("#/map")) return "map";
    if (h.startsWith("#/plan")) return "plan";
    return "route";
  }

  function render() {
    const view = currentView();
    document.querySelectorAll(".tabs a").forEach((a) => a.classList.toggle("on", a.dataset.tab === view || (view === "stop" && a.dataset.tab === "route")));
    const v = $("#view");
    if (view === "stop") v.innerHTML = stopView(byN[+location.hash.split("/")[2]] || STOPS[0]);
    else if (view === "map") { v.innerHTML = mapView(); drawMap(true); }
    else if (view === "plan") v.innerHTML = planView();
    else { v.innerHTML = routeView(); updateDistances(); }
    if (Player.stop) Player.highlight(Player.chunks[Player.idx] ? Player.chunks[Player.idx].p : -1);
  }

  function visible(s) {
    if (S.coreOnly && !s.isCore) return false;
    if (S.thread && !s.threads.includes(S.thread)) return false;
    return true;
  }

  function routeView() {
    const coreN = STOPS.filter((s) => s.isCore).length;
    let h = `<div class="filters">
      <button class="chip ${S.coreOnly ? "on" : ""}" data-core>Core only (${coreN})</button>
      ${THREADS.map((t) => `<button class="chip ${S.thread === t ? "on" : ""}" data-thread="${t}">${t}</button>`).join("")}
    </div>`;
    const place = (id) => G.places.find((p) => p.id === id);
    G.sections.forEach((sec, i) => {
      h += `<h2 class="section-h">${esc(sec.title)}</h2><p class="section-intro">${esc(sec.intro)}</p>`;
      if (i === 0) h += `<div class="waypoint">9:00 Enter: ${esc(place("entrance").name)}</div>`;
      if (i === 2) h += `<div class="waypoint">11:45 Walk to lunch, Via Cavour 215 (about 7 min). Leave by 12:35 for Colosseum security at 12:45.</div>`;
      sec.stops.map((n) => byN[n]).filter(visible).forEach((s) => {
        h += `<a class="stop-row ${s.isCore ? "core" : ""} ${S.visited.has(s.n) ? "done" : ""}" href="#/stop/${s.n}">
          <span class="num">${s.n}</span>
          <span class="meta"><span class="t">${esc(s.title)}</span>
          <span class="s">${s.isCore ? "Core" : "Optional"} · ${s.threads.join(", ")} · ${s.minutes} min<span class="dist" data-n="${s.n}"></span></span></span>
          ${S.visited.has(s.n) ? '<span class="tick">✓</span>' : ""}</a>`;
      });
      if (i === 1) h += `<div class="waypoint">Exit at Largo della Salara Vecchia. If that gate is closed, use the Arch of Titus exit (about 12 min to lunch).</div>`;
    });
    return h;
  }
  function updateDistances() {
    document.querySelectorAll(".dist").forEach((el) => {
      el.textContent = Geo.pos ? " · " + fmtDist(distM(Geo.pos, byN[+el.dataset.n])) + " away" : "";
    });
  }

  function proseBlock(s, part, text) {
    return `<div class="prose" data-stop="${s.n}" data-part="${part}">${paras(text).map((p, i) => `<p data-p="${i}">${esc(p)}</p>`).join("")}</div>`;
  }

  function stopView(s) {
    const prev = byN[s.n - 1], next = byN[s.n + 1];
    const gallery = s.images.length ? `<div class="gallery">${s.images.map((im) =>
      `<figure><img src="${esc(im.src)}" alt="${esc(im.caption)}" loading="lazy" data-cap="${esc(im.caption + (im.credit ? " — " + im.credit : ""))}">
       <figcaption>${esc(im.caption)}${im.credit ? `<br><span class="small">${esc(im.credit)}</span>` : ""}</figcaption></figure>`).join("")}</div>` : "";
    return `
      <div class="stop-head"><span class="num" style="${s.isCore ? "background:var(--accent);color:var(--accent-ink)" : ""}">${s.n}</span><h1>${esc(s.title)}</h1></div>
      <div class="badges">${s.isCore ? '<span class="badge core">CORE</span>' : '<span class="badge plain">Optional</span>'}
        ${s.threads.map((t) => `<span class="badge">${esc(t)}</span>`).join("")}
        ${s.note && !/^Optional$/i.test(s.note) ? `<span class="badge plain">${esc(s.note.replace(/^Optional,?\s*/i, ""))}</span>` : ""}</div>
      <div class="play-row">
        <button class="play" data-start="core">▶ ${s.isCore ? "Core" : "Listen"}<small>about ${minutesOf(s.core)} min</small></button>
        ${s.deep ? `<button class="play alt" data-start="deep">▶ Deep dive<small>${esc(s.deepTitle)} · ${minutesOf(s.deep)} min</small></button>`
                 : `<a class="play alt" href="${mapsLink(s.lat, s.lon, s.title)}" style="text-decoration:none">⌖ Show in Maps<small>Apple Maps</small></a>`}
      </div>
      ${proseBlock(s, "core", s.core)}
      ${s.lookFor ? `<div class="lookfor"><h3>Look for</h3>${esc(s.lookFor)}</div>` : ""}
      ${gallery}
      ${s.deep ? `<details class="deep" ${Player.stop === s && Player.part === "deep" ? "open" : ""}><summary>Deep dive: ${esc(s.deepTitle)}</summary>${proseBlock(s, "deep", s.deep)}</details>` : ""}
      <label class="visited"><input type="checkbox" data-visited ${S.visited.has(s.n) ? "checked" : ""}> Seen it</label>
      ${s.deep ? `<div class="row-actions"><a class="btn" href="${mapsLink(s.lat, s.lon, s.title)}">⌖ Show in Maps</a><a class="btn" href="#/map">Route map</a></div>` : ""}
      <div class="stop-nav">
        ${prev ? `<a href="#/stop/${prev.n}">← ${prev.n}. ${esc(short(prev.title))}</a>` : "<span></span>"}
        ${next ? `<a href="#/stop/${next.n}">${next.n}. ${esc(short(next.title))} →</a>` : `<a href="#/">All stops</a>`}
      </div>`;
  }
  const short = (t) => t.split(/[:(]/)[0].trim().slice(0, 26);

  /* ---------- Map (drawn from coordinates; GPS dot works without data) ---------- */
  const M = { zoom: store.get("zoom", 1.6) };
  function mapView() {
    return `<div class="map-tools">
        <button class="btn" data-gps>${Geo.watch !== null ? "Stop GPS" : "Start GPS"}</button>
        <button class="btn" data-zoom="1.3">+</button><button class="btn" data-zoom="0.77">−</button>
        <button class="btn" data-center>Me</button>
      </div>
      <div class="map-wrap" id="mapWrap"></div>
      <p class="gps-status" id="gpsStatus"></p>
      <p class="small">Simplified map, north up. Orange line: morning route. Blue line: afternoon. Tap a number to open the stop.
      For street-level directions, use Apple Maps with Rome downloaded for offline use (see Plan tab).</p>`;
  }
  const all = STOPS.map((s) => ({ lat: s.lat, lon: s.lon })).concat(G.places);
  const B = {
    la0: Math.min(...all.map((p) => p.lat)) - 0.0012, la1: Math.max(...all.map((p) => p.lat)) + 0.0010,
    lo0: Math.min(...all.map((p) => p.lon)) - 0.0018, lo1: Math.max(...all.map((p) => p.lon)) + 0.0014,
  };
  const KX = 111320 * Math.cos(41.89 * Math.PI / 180), KY = 110570;
  const MW = (B.lo1 - B.lo0) * KX, MH = (B.la1 - B.la0) * KY;
  const xy = (lat, lon) => [(lon - B.lo0) * KX, (B.la1 - lat) * KY];

  function drawMap(first) {
    const wrap = $("#mapWrap");
    if (!wrap) return;
    const keep = first ? null : { l: wrap.scrollLeft, t: wrap.scrollTop };
    const px = wrap.clientWidth * M.zoom, scale = px / MW, ph = MH * scale;
    const P = (lat, lon) => xy(lat, lon).map((v) => v * scale);
    const line = (pts, color, dash) => `<polyline points="${pts.map((p) => P(p.lat, p.lon).join(",")).join(" ")}" fill="none" stroke="${color}" stroke-width="${Math.max(2, 3 * M.zoom / 1.6)}" stroke-dasharray="${dash}" stroke-linejoin="round" stroke-linecap="round" opacity=".85"/>`;
    const place = (id) => G.places.find((p) => p.id === id);
    const morning = [place("entrance")].concat(STOPS.filter((s) => s.n <= 18), [place("exit"), place("lunch")]);
    const afternoon = [place("lunch"), place("colosseum-gate"), byN[19], byN[21], byN[22], byN[23], byN[24], byN[25], byN[20]];
    // landmarks: Colosseum ellipse (~189 x 156 m) and Circus Maximus (~600 x 140 m, axis NW-SE)
    const [cx, cy] = P(41.89021, 12.49223);
    const [c1x, c1y] = P(41.88625, 12.48195), [c2x, c2y] = P(41.88395, 12.48825);
    const circAng = Math.atan2(c2y - c1y, c2x - c1x) * 180 / Math.PI, circLen = Math.hypot(c2x - c1x, c2y - c1y);
    const lbl = (lat, lon, t, size) => { const [x, y] = P(lat, lon); return `<text x="${x}" y="${y}" font-size="${size * Math.sqrt(M.zoom)}" fill="#8a7a66" text-anchor="middle" font-style="italic" font-family="Georgia, serif">${t}</text>`; };
    let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${px}" height="${ph}" viewBox="0 0 ${px} ${ph}">`;
    svg += `<ellipse cx="${cx}" cy="${cy}" rx="${94.5 * scale}" ry="${78 * scale}" fill="#e2d2b4" stroke="#b9a27c"/>`;
    svg += `<rect x="${c1x}" y="${c1y - 70 * scale}" width="${circLen}" height="${140 * scale}" rx="${70 * scale}" fill="#dfe3c8" stroke="#b9b48c" transform="rotate(${circAng} ${c1x} ${c1y})"/>`;
    svg += lbl(41.8880, 12.4860, "Palatine", 15) + lbl(41.8922, 12.4864, "Roman Forum", 15) + lbl(41.8902, 12.4922, "Colosseum", 12) +
           lbl(41.8853, 12.4840, "Circus Maximus", 12) + lbl(41.8945, 12.4900, "Monti", 13);
    svg += line(morning, "#b5532f", "1 0") + line(afternoon, "#3d7aa8", "7 6");
    G.places.forEach((p) => {
      const [x, y] = P(p.lat, p.lon);
      const col = p.kind === "lunch" ? "#4c7a46" : "#3d7aa8";
      svg += `<rect x="${x - 7}" y="${y - 7}" width="14" height="14" rx="3" fill="${col}" stroke="#fff" stroke-width="2"/>`;
      svg += `<text x="${x + 11}" y="${y + 4}" font-size="${11 * Math.sqrt(M.zoom)}" fill="${col}" font-weight="700" font-family="-apple-system, sans-serif">${esc(p.kind === "lunch" ? "Lunch" : p.name.split("(")[0].trim())}</text>`;
    });
    STOPS.forEach((s) => {
      const [x, y] = P(s.lat, s.lon);
      const r = s.isCore ? 12 : 10, done = S.visited.has(s.n);
      svg += `<a href="#/stop/${s.n}"><circle cx="${x}" cy="${y}" r="${r}" fill="${s.isCore ? "#b5532f" : "#fffaf2"}" stroke="${s.isCore ? "#fff" : "#b5532f"}" stroke-width="2" opacity="${done ? 0.5 : 1}"/>
        <text x="${x}" y="${y + 4}" font-size="11" font-weight="700" text-anchor="middle" fill="${s.isCore ? "#fff" : "#b5532f"}" font-family="-apple-system, sans-serif">${s.n}</text></a>`;
    });
    if (Geo.pos) {
      const [x, y] = P(Geo.pos.lat, Geo.pos.lon);
      svg += `<circle cx="${x}" cy="${y}" r="${Math.max(10, Geo.pos.acc * scale)}" fill="#2f7cf6" opacity=".15"/>`;
      svg += `<circle cx="${x}" cy="${y}" r="8" fill="#2f7cf6" stroke="#fff" stroke-width="3"/>`;
    }
    svg += `</svg>`;
    wrap.innerHTML = svg;
    if (keep) { wrap.scrollLeft = keep.l; wrap.scrollTop = keep.t; }
    else if (first) centerOn(Geo.pos || byN[6]);
    const st = $("#gpsStatus");
    if (st) {
      const n = nearest();
      st.textContent = Geo.watch === null ? "GPS is off. Tap Start GPS to show your position (works in flight mode too)." :
        Geo.err ? Geo.err : !Geo.pos ? "Waiting for a GPS fix..." :
        `Accuracy about ${Math.round(Geo.pos.acc)} m. Nearest: stop ${n.s.n}, ${fmtDist(n.d)}.` +
        (Geo.pos.lat < B.la0 || Geo.pos.lat > B.la1 || Geo.pos.lon < B.lo0 || Geo.pos.lon > B.lo1 ? " You are outside this map." : "");
    }
  }
  function centerOn(p) {
    const wrap = $("#mapWrap"); if (!wrap || !p) return;
    const scale = wrap.clientWidth * M.zoom / MW;
    const [x, y] = xy(p.lat, p.lon).map((v) => v * scale);
    wrap.scrollLeft = x - wrap.clientWidth / 2; wrap.scrollTop = y - wrap.clientHeight / 2;
  }

  /* ---------- Plan & settings ---------- */
  function planView() {
    const vs = Player.voices().filter((v) => /^en/i.test(v.lang));
    const cur = Player.pickVoice();
    return `<div class="plan">
      <div class="card"><h2>Saturday 14 November</h2>
      <table>
        <tr><td>9:00</td><td>Enter at the Palatine (Via di San Gregorio 30) or the Arch of Titus gate. Forum and Palatine open at 9:00.</td></tr>
        <tr><td>9:00–10:10</td><td>Palatine Hill, stops 1–6</td></tr>
        <tr><td>10:10–11:45</td><td>Roman Forum, stops 7–18, east to west</td></tr>
        <tr><td>11:45</td><td>Exit at Largo della Salara Vecchia (fallback: Arch of Titus). Walk to lunch, about 7 min.</td></tr>
        <tr><td>12:00</td><td>Lunch, Via Cavour 215. Leave by 12:35.</td></tr>
        <tr><td>12:45</td><td>Colosseum security. Bring ID. No backpacks or large bags.</td></tr>
        <tr><td>13:00–14:15</td><td>Colosseum, stops 19–25. 75 minutes, one-way route.</td></tr>
      </table>
      <p class="small">Winter hours: the park closes 16:30, last entry 15:30. Check the official MyColosseum app or the gate signs on the day.</p></div>

      <div class="card"><h2>Ready for offline?</h2>
        <p id="offlineStatus" class="small">Checking...</p>
        <button class="btn" data-recheck>Check again</button>
        <p class="small">Test before you go: open the app from the Home Screen, switch on flight mode, and play a stop.</p></div>

      <div class="card"><h2>Voice</h2>
        <label for="voiceSel">English voice on this phone</label>
        <select id="voiceSel">${vs.length ? vs.map((v) => `<option value="${esc(v.voiceURI)}" ${cur && cur.voiceURI === v.voiceURI ? "selected" : ""}>${esc(v.name)} (${esc(v.lang)})</option>`).join("") : "<option>Voices are loading...</option>"}</select>
        <label for="rate">Speed: <b id="rateVal">${S.rate.toFixed(2)}×</b></label>
        <input id="rate" type="range" min="0.75" max="1.3" step="0.05" value="${S.rate}">
        <div class="row-actions"><button class="btn" data-testvoice>Test voice</button><button class="btn" data-stopvoice>Stop</button></div>
        <p class="small">Every stop has a recorded voice, so this is only a backup. For a better backup voice: iPhone Settings › Accessibility › Read &amp; Speak › Voices › English (on iOS 18 and older: Spoken Content), and download an <b>Enhanced</b> or <b>Premium</b> voice. Then pick it here.</p></div>

      <div class="card"><h2>Location</h2>
        <button class="btn ${Geo.watch !== null ? "" : "primary"}" data-gps>${Geo.watch !== null ? "Stop GPS" : "Start GPS"}</button>
        <label class="visited"><input type="checkbox" data-autoplay ${S.autoplay ? "checked" : ""}> Auto-play the core audio when you reach a stop</label>
        <p class="small">GPS works in flight mode. Keep the screen on while walking: iPhone stops speech when the screen locks.</p></div>

      <div class="card"><h2>Backup maps</h2>
        <p class="small">In Apple Maps, download Rome for offline use (tap your profile › Offline Maps). The “Show in Maps” buttons then work without data.</p>
        <div class="row-actions"><a class="btn" href="maps/rome-guide.kml" download>Pins (KML)</a><a class="btn" href="maps/rome-guide.gpx" download>Pins (GPX)</a></div>
        <p class="small">Open either file in Organic Maps to get all stops as pins on a full offline map.</p></div>

      <div class="card"><h2>Progress</h2>
        <p class="small">${S.visited.size} of ${STOPS.length} stops marked as seen.</p>
        <button class="btn" data-reset>Clear “seen” marks</button></div>

      <p class="small">Diagrams drawn for this guide. Dates and figures are the best estimates of current scholarship; several are debated, and the audio says so where it matters.</p>
    </div>`;
  }

  async function offlineStatus() {
    const el = $("#offlineStatus"); if (!el) return;
    if (!("serviceWorker" in navigator) || !window.caches) { el.innerHTML = '<span class="status-warn">This browser cannot store the app offline.</span>'; return; }
    try {
      const reg = await navigator.serviceWorker.getRegistration();
      if (!reg || !navigator.serviceWorker.controller) { el.innerHTML = '<span class="status-warn">Not ready yet.</span> Reload once while online, then check again.'; return; }
      const ch = new MessageChannel();
      ch.port1.onmessage = (e) => {
        const { cached, total, version } = e.data;
        el.innerHTML = cached === total
          ? `<span class="status-ok">Ready: all ${total} files stored on this phone.</span> <span class="small">Version ${esc(version)}</span>`
          : `<span class="status-warn">${cached} of ${total} files stored.</span> Stay online for a minute, then check again.`;
      };
      navigator.serviceWorker.controller.postMessage({ type: "status" }, [ch.port2]);
    } catch (e) { el.textContent = "Could not check: " + e.message; }
  }

  /* ---------- Events ---------- */
  document.addEventListener("click", (e) => {
    const t = e.target.closest("button, img, [data-visited]");
    if (!t) return;
    const d = t.dataset;
    if ("core" in d) { S.coreOnly = !S.coreOnly; store.set("coreOnly", S.coreOnly); render(); }
    else if (d.thread) { S.thread = S.thread === d.thread ? "" : d.thread; store.set("thread", S.thread); render(); }
    else if (d.start) {
      const s = byN[+location.hash.split("/")[2]];
      if (d.start === "deep") { const det = $("details.deep"); if (det) det.open = true; }
      Player.start(s, d.start);
    }
    else if ("gps" in d) { Geo.watch !== null ? stopGps() : startGps(); render(); }
    else if (d.zoom) { M.zoom = Math.min(8, Math.max(0.8, M.zoom * +d.zoom)); store.set("zoom", M.zoom); const w = $("#mapWrap");
      const cx = (w.scrollLeft + w.clientWidth / 2) * +d.zoom, cy = (w.scrollTop + w.clientHeight / 2) * +d.zoom;
      drawMap(false); w.scrollLeft = cx - w.clientWidth / 2; w.scrollTop = cy - w.clientHeight / 2; }
    else if ("center" in d) { if (!Geo.pos) startGps(); centerOn(Geo.pos || byN[6]); }
    else if ("testvoice" in d) { Player.start({ n: 0, title: "Voice test", core: "Welcome to the Palatine Hill. This is how the guide will sound.", deep: "", audio: {} }, "core"); }
    else if ("stopvoice" in d) Player.halt();
    else if ("recheck" in d) offlineStatus();
    else if ("reset" in d) { if (confirm("Clear all “seen” marks?")) { S.visited.clear(); saveVisited(); render(); } }
    else if (t.tagName === "IMG" && t.closest(".gallery")) {
      const lb = $("#lightbox"); $("img", lb).src = t.src; $(".lb-cap", lb).textContent = t.dataset.cap || t.alt; lb.hidden = false;
    }
  });
  document.addEventListener("change", (e) => {
    const t = e.target;
    if ("visited" in t.dataset) {
      const n = +location.hash.split("/")[2];
      t.checked ? S.visited.add(n) : S.visited.delete(n); saveVisited();
    } else if ("autoplay" in t.dataset) { S.autoplay = t.checked; store.set("autoplay", S.autoplay); if (S.autoplay) startGps(); }
    else if (t.id === "voiceSel") { S.voice = t.value; store.set("voice", S.voice); }
  });
  document.addEventListener("input", (e) => {
    if (e.target.id === "rate") { S.rate = +e.target.value; store.set("rate", S.rate); $("#rateVal").textContent = S.rate.toFixed(2) + "×"; }
  });
  $("#lightbox").addEventListener("click", () => { $("#lightbox").hidden = true; });

  window.addEventListener("hashchange", () => { render(); window.scrollTo(0, 0); if (currentView() === "plan") offlineStatus(); });
  render();
  if (currentView() === "plan") offlineStatus();
  if (S.gps) startGps();

  /* ---------- Offline support ---------- */
  if ("serviceWorker" in navigator && location.protocol !== "file:") {
    // updateViaCache "none": always fetch sw.js fresh, so a new version is found on the next open
    const hadController = !!navigator.serviceWorker.controller;
    navigator.serviceWorker.register("sw.js", { updateViaCache: "none" }).then((reg) => {
      reg.update().catch(() => {});
      if (currentView() === "plan") setTimeout(offlineStatus, 1500);
    }).catch(() => {});
    // when a new version has taken over, reload once so the new files are shown (not while audio plays)
    let reloaded = false;
    navigator.serviceWorker.addEventListener("controllerchange", () => {
      if (!hadController || reloaded || Player.playing) return;
      reloaded = true; location.reload();
    });
  }
})();
