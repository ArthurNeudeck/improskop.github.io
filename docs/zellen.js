// =====================================================================
// IMPROSKOP – Der Objektträger
// Start: Mikroskop von aussen → Hineinfahrt (Blender-Bilder rückwärts, in der
// durchsichtigen Linse liegt die echte Website) → Linse öffnet sich → die Kamera
// gleitet von Zelle zu Zelle → Übersicht → Hinausfahrt (Bilder vorwärts).
// Alles hängt nur an der Scroll-Position: vor und zurück, kein Einrasten.
// Ohne JS oder bei reduzierter Bewegung bleibt die einfache Zellen-Liste.
// =====================================================================
(() => {
    const objekttraeger = document.querySelector('.objekttraeger');
    if (!objekttraeger || matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const html = document.documentElement;
    const datenSparen = navigator.connection && navigator.connection.saveData;
    const welt = objekttraeger.querySelector('.welt');
    const flecken = welt.querySelector('.flecken');
    const tiefen = [...objekttraeger.querySelectorAll('.tiefe')];
    const zellen = [...welt.querySelectorAll('.zelle')];
    const buehne = document.querySelector('.buehne');
    const leinwand = buehne.querySelector('canvas');
    const stift = leinwand.getContext('2d');
    const panel = document.querySelector('.show-panel');
    const leiste = document.querySelector('.show-leiste');
    const footer = document.querySelector('.footer');
    const okularRand = document.querySelector('.okular-rand');
    const nav = document.querySelector('.nav');
    const scrollweg = document.querySelector('.scrollweg');

    html.classList.add('kamera');

    // Sparmodus für schwache Geräte: wenig Speicher/Kerne, Datensparen – oder (siehe
    // ruckelWaechter) wenn die Seite beim Scrollen messbar ruckelt. Zum Testen: ?leicht
    let leicht = false;
    function sparmodus() {
        if (leicht) return;
        leicht = true;
        html.classList.add('leicht');
        html.classList.remove('brechung');
        if (format) { bilderLaden(); aufbauen(); planen(); }
    }
    // Handys (Touch oder schmaler Bildschirm) immer: dort ist der Grafikchip der Engpass,
    // und den kann die Ruckel-Erkennung (misst den Hauptprozessor) nicht sehen.
    if (datenSparen || location.search.includes('leicht') ||
        matchMedia('(pointer: coarse), (max-width: 900px)').matches ||
        (navigator.deviceMemory && navigator.deviceMemory <= 4) ||
        (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 4)) {
        leicht = true;
        html.classList.add('leicht');
        html.classList.remove('brechung');
    }

    const begrenze = (w, min = 0, max = 1) => Math.min(max, Math.max(min, w));
    const bereich = (w, von, bis) => begrenze((w - von) / (bis - von));
    const sanft = t => t * t * (3 - 2 * t);
    const mix = (a, b, t) => a + (b - a) * t;
    // Zoom gleichmässig wirken lassen: Massstab logarithmisch mischen
    const mixMassstab = (a, b, t) => Math.exp(mix(Math.log(a), Math.log(b), t));
    const mixKamera = (a, b, t) => ({
        x: mix(a.x, b.x, sanft(t)),
        y: mix(a.y, b.y, sanft(t)),
        s: mixMassstab(a.s, b.s, t),
    });

    // =================================================================
    // Blender-Bildfolge (eine Folge für Hinein- und Hinausfahrt)
    // =================================================================
    const BILDER = 96;
    const BLASE = 0.21;         // = --blase in style.css
    let format = null;
    let bilder = [];
    let linsen = null;          // pro Bild: Lage der Linse {x, y, rx, ry} (0..1)
    let letztesBild = -1;

    const bildFormat = () => (innerWidth / innerHeight < 0.9 ? 'hoch' : 'quer');

    function bilderLaden() {
        format = bildFormat();
        const ordner = format;
        bilder = new Array(BILDER).fill(null);
        letztesBild = -1;
        linsen = null;
        fetch(`media/outro/linse-${ordner}.json`)
            .then(r => r.json())
            .then(daten => { if (ordner === format) { linsen = daten; planen(); } })
            .catch(() => { /* ohne Linsendaten bleibt der Objektträger bis zur Linse verborgen */ });

        // Schlussbild zuerst (erster Bildschirm), dann grob nach fein.
        // Immer nur jedes 2. Bild (48 statt 96: halbe Bildrate, halber Speicher).
        // Sparmodus: zusätzlich 60 % Grösse (Ordner *-leicht).
        const quelle = leicht ? `${ordner}-leicht` : ordner;
        const vorhanden = i => i % 2 === 0 || i === BILDER - 1;
        const reihenfolge = [BILDER - 1];
        if (!datenSparen) {
            for (const schritt of [16, 8, 4, 2, 1])
                for (let i = 0; i < BILDER; i += schritt)
                    if (vorhanden(i) && !reihenfolge.includes(i)) reihenfolge.push(i);
        }
        let naechstes = 0;
        const laden = () => {
            if (naechstes >= reihenfolge.length || ordner !== format || quelle !== (leicht ? `${format}-leicht` : format)) return;
            const i = reihenfolge[naechstes++];
            const img = new Image();
            img.decoding = 'async';
            // vor dem ersten Zeichnen dekodieren, damit das nicht mitten im Scrollen passiert
            img.onload = () => img.decode().catch(() => {}).then(() => {
                img.bereit = true; letztesBild = -1; planen(); laden();
            });
            img.onerror = laden;
            img.src = `media/outro/${quelle}/${String(i + 1).padStart(4, '0')}.webp`;
            bilder[i] = img;
        };
        // Erst das Schlussbild (= erster Bildschirm), den Rest erst nach dem Laden der Seite
        // oder beim ersten Scrollen – so bremst die Bildfolge den Seitenaufbau nicht.
        laden();
        let gestartet = false;
        const rest = () => {
            if (gestartet) return;
            gestartet = true;
            removeEventListener('scroll', rest);
            for (let k = 0; k < 4; k++) laden();   // höchstens 4 Downloads gleichzeitig
        };
        addEventListener('scroll', rest, { passive: true, once: true });
        if (document.readyState === 'complete') setTimeout(rest, 300);
        else addEventListener('load', () => setTimeout(rest, 300), { once: true });
    }

    const geladen = i => bilder[i] && bilder[i].bereit;

    function naechstesGeladenes(ziel) {
        for (let d = 0; d < BILDER; d++) {
            if (geladen(ziel - d)) return ziel - d;
            if (geladen(ziel + d)) return ziel + d;
        }
        return -1;
    }

    // Bildmasse für "cover"
    function abdeckung(iw, ih, cw, ch) {
        const s = Math.max(cw / iw, ch / ih);
        return { x: (cw - iw * s) / 2, y: (ch - ih * s) / 2, w: iw * s, h: ih * s };
    }

    function zeichne(index) {
        const i = naechstesGeladenes(index);
        if (i < 0 || i === letztesBild) return;
        const img = bilder[i];
        const m = abdeckung(img.naturalWidth, img.naturalHeight, leinwand.width, leinwand.height);
        stift.clearRect(0, 0, leinwand.width, leinwand.height);
        stift.drawImage(img, m.x, m.y, m.w, m.h);
        letztesBild = i;
        buehne.setAttribute('data-film-bereit', '');
    }

    // Linse in Bild i, in CSS-Pixeln
    function linse(i) {
        if (!linsen) return null;
        const l = linsen[begrenze(Math.round(i), 0, BILDER - 1)];
        const iw = format === 'quer' ? 1600 : 900, ih = format === 'quer' ? 900 : 1600;
        const m = abdeckung(iw, ih, innerWidth, innerHeight);
        return { x: m.x + l.x * m.w, y: m.y + l.y * m.h, r: Math.max(l.rx * m.w, l.ry * m.h) };
    }

    // =================================================================
    // Präparat: Flecken, Bläschen, Deko-Bakterien (reproduzierbar per Zufallssaat)
    // =================================================================
    function zufall(saat) {
        return () => {
            saat |= 0; saat = (saat + 0x6D2B79F5) | 0;
            let t = Math.imul(saat ^ (saat >>> 15), 1 | saat);
            t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
            return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
        };
    }

    function element(klasse, x, y, groesse, extra = '') {
        const el = document.createElement('div');
        el.className = klasse;
        el.style.cssText = `left:${x}px;top:${y}px;width:${groesse}px;height:${groesse}px;${extra}`;
        return el;
    }

    function praeparatAnlegen(breite, hoehe) {
        const z = zufall(7);
        const farben = ['rgb(231 219 196 / 0.9)', 'rgb(237 201 203 / 0.55)', 'rgb(211 202 223 / 0.6)', 'rgb(216 195 156 / 0.4)'];
        flecken.replaceChildren();
        tiefen.forEach(t => t.replaceChildren());
        for (let i = 0; i < 12; i++) {
            const g = 320 + z() * 900;
            const rand = z() < 0.35;
            flecken.append(element(rand ? 'fleck fleck--rand' : 'fleck fleck--weich',
                z() * breite - g / 2, z() * hoehe - g / 2, g,
                rand ? `transform:scale(1,${0.7 + z() * 0.5}) rotate(${z() * 180}deg)`
                     : `--fleck-farbe:${farben[i % farben.length]};transform:scale(1,${0.6 + z() * 0.6})`));
        }
        for (let i = 0; i < 18; i++) {
            const g = 10 + Math.pow(z(), 2) * 130;
            flecken.append(element('blaeschen', z() * breite, z() * hoehe, g));
        }
        // Deko-Bakterien in den Lücken zwischen den Zellen
        zellen.slice(0, -1).forEach((zelle, i) => {
            const frei0 = zelle.offsetTop + zelle.offsetHeight * (1 + BLASE);
            const frei1 = zellen[i + 1].offsetTop - zellen[i + 1].offsetHeight * BLASE;
            const y = frei0 + (frei1 - frei0) * (0.3 + z() * 0.4);
            const g = 50 + z() * 110;
            flecken.append(element('bakterie', z() * (breite - g), y - g / 2, g,
                `height:${g * (0.55 + z() * 0.3)}px;animation-delay:${-z() * 10}s`));
        });
        const [hinten] = tiefen;
        for (let i = 0; i < 10; i++) {
            const g = 8 + Math.pow(z(), 2) * 90;
            hinten.append(element('blaeschen', z() * breite, z() * hoehe, g));
        }
    }

    // =================================================================
    // Zeitachse
    // =================================================================
    let achse = [];
    let gesamt = 0;
    let vw = 0, vh = 0, oben = 0, unten = 0;
    let einstieg, abschied, rVoll;
    let andock = null;

    function andockMessen() {
        panel.style.setProperty('--andock-x', '0px');
        panel.style.setProperty('--andock-y', '0px');
        panel.style.setProperty('--andock-s', '1');
        const p = panel.getBoundingClientRect();
        const l = leiste.getBoundingClientRect();
        const s = begrenze((l.height * 2.4) / p.height, 0.2, 1);
        andock = { x: l.left - p.left, y: l.top - p.top, s };
    }

    function aufbauen() {
        vw = innerWidth;
        vh = innerHeight;
        const handy = vw < 760;
        const zellBreite = handy ? vw - 24 : Math.min(1080, vw - 96);
        const weltBreite = handy ? vw * 1.35 : zellBreite * 1.9;
        welt.style.setProperty('--welt-breite', `${weltBreite}px`);
        welt.style.setProperty('--zell-breite', `${zellBreite}px`);
        // Die Glas-Blase ragt um BLASE (Anteil der Zellgrösse) über den Inhalt hinaus:
        // Abstände so wählen, dass sich benachbarte Blasen nicht berühren.
        const abstand = vh * (handy ? 0.3 : 0.4);
        zellen.forEach((z, i) => {
            z.style.marginTop = i ? `${abstand + BLASE * (zellen[i - 1].offsetHeight + z.offsetHeight)}px` : '';
        });
        welt.style.paddingTop = `${vh * 0.6 + BLASE * zellen[0].offsetHeight}px`;
        welt.style.paddingBottom = `${vh * 0.6 + BLASE * zellen[zellen.length - 1].offsetHeight}px`;
        tiefen.forEach(t => t.style.setProperty('--welt-breite', `${weltBreite}px`));

        // Ränder: Show-Leiste oben, auf dem Handy Navigation unten
        const l = leiste.getBoundingClientRect();
        oben = l.bottom + 16;
        const n = nav.getBoundingClientRect();
        unten = handy ? vh - n.top + 16 : 24;
        const H = vh - oben - unten;
        const ax = vw / 2, ay = oben + H / 2;

        const weltHoehe = welt.offsetHeight;
        tiefen.forEach(t => t.style.setProperty('--welt-hoehe', `${weltHoehe * 1.2}px`));
        praeparatAnlegen(weltBreite, weltHoehe);

        // Kamerazustände je Zelle (Weltpunkt, der im Anker liegt, + Massstab)
        const puffer = 32;
        const stationen = zellen.map(z => {
            const x = z.offsetLeft + z.offsetWidth / 2;
            const y = z.offsetTop, h = z.offsetHeight;
            if (h + 2 * puffer <= H) {
                const mitte = { x, y: y + h / 2, s: 1 };
                return { anfang: mitte, ende: mitte, weg: vh * 0.25 };
            }
            return {
                anfang: { x, y: y - puffer + H / 2, s: 1 },
                ende: { x, y: y + h + puffer - H / 2, s: 1 },
                weg: h + 2 * puffer - H,
            };
        });
        const tiefster = handy ? 0.55 : 0.42;
        einstieg = { x: stationen[0].anfang.x, y: zellen[0].offsetTop + zellen[0].offsetHeight / 2, s: handy ? 0.7 : 0.6 };
        // Ende: von der letzten Zelle aus nach oben hinaus – der Objektträger gleitet hoch und weg
        const letzte = zellen[zellen.length - 1];
        abschied = { x: stationen[stationen.length - 1].ende.x, y: letzte.offsetTop + letzte.offsetHeight * (1 + BLASE) + H * 0.9, s: 0.6 };
        rVoll = Math.hypot(vw, vh) / 2 + 4;

        achse = [];
        const neu = (typ, laenge, daten = {}) => achse.push({ typ, laenge, ...daten });
        neu('hinein', vh * 1.3);
        neu('oeffnen', vh * 0.6, { von: einstieg, nach: stationen[0].anfang });
        stationen.forEach((st, i) => {
            neu('zelle', st.weg, { von: st.anfang, nach: st.ende, zelle: i });
            if (i < stationen.length - 1)
                neu('uebergang', vh * 0.9, { von: st.ende, nach: stationen[i + 1].anfang, tiefster, zelle: i });
        });
        neu('abschied', vh * 0.9, { von: stationen[stationen.length - 1].ende, nach: abschied });
        neu('hinaus', vh * 1.3);
        let pos = 0;
        achse.forEach(a => { a.start = pos; pos += a.laenge; });
        gesamt = pos;
        scrollweg.style.setProperty('--scrollweg', `${gesamt + vh}px`);
        welt.dataset.anker = `${ax},${ay}`;

        const dpr = leicht ? 1 : Math.min(devicePixelRatio || 1, 1.5);
        leinwand.width = Math.round(vw * dpr);
        leinwand.height = Math.round(vh * dpr);
        letztesBild = -1;
        andockMessen();
    }

    // Wo auf der Zeitachse beginnt Zelle i?
    const zellBeginn = i => achse.find(a => a.typ === 'zelle' && a.zelle === i);

    // =================================================================
    // Ein Bild berechnen
    // =================================================================
    function setze(el, name, wert) { el.style.setProperty(name, wert); }

    function weltZeigen(kam) {
        const [ax, ay] = welt.dataset.anker.split(',').map(Number);
        const genau = kam.s > 0.999;
        const tx = ax - kam.x * kam.s, ty = ay - kam.y * kam.s;
        welt.style.transform = genau
            ? `translate3d(${Math.round(tx)}px, ${Math.round(ty)}px, 0)`
            : `translate3d(${tx}px, ${ty}px, 0) scale(${kam.s})`;
        tiefen.forEach(t => {
            const k = Number(t.dataset.faktor);
            t.style.transform = `translate3d(${ax - kam.x * kam.s * k}px, ${ay - kam.y * kam.s * k}px, 0) scale(${kam.s})`;
        });
    }

    // Objektträger in die Linse des Renderbildes legen
    function inLinse(i) {
        const l = linse(i), l1 = linse(0);
        if (!l || !l1) { setze(objekttraeger, '--loch', '0px'); return; }
        setze(objekttraeger, '--loch', `${l1.r}px`);
        setze(objekttraeger, '--lx', `${l.x - vw / 2}px`);
        setze(objekttraeger, '--ly', `${l.y - vh / 2}px`);
        setze(objekttraeger, '--ls', String(l.r / l1.r));
    }

    function frei(loch) {
        setze(objekttraeger, '--loch', `${loch}px`);
        setze(objekttraeger, '--lx', '0px');
        setze(objekttraeger, '--ly', '0px');
        setze(objekttraeger, '--ls', '1');
    }

    const organellenJeZelle = zellen.map(z => [...z.querySelectorAll('.organell')]);
    const bewegt = new Set();      // Zellen, deren Fotos gerade verschoben sind

    function organellenTreiben(a, t) {
        // Im Übergang treiben die Fotos der beiden Zellen hinterher und drehen sich leicht
        const welle = Math.sin(Math.PI * t);
        const richtung = Math.sign(a.nach.x - a.von.x) || 1;
        [a.zelle, a.zelle + 1].forEach(i => {
            bewegt.add(i);
            organellenJeZelle[i].forEach(o => {
                const tiefe = Number(o.dataset.tiefe || 1) - 1;
                setze(o, '--dx', `${-richtung * welle * tiefe * 160}px`);
                setze(o, '--dy', `${-welle * tiefe * 120}px`);
                setze(o, '--dr', `${richtung * welle * tiefe * 14}deg`);
            });
        });
    }

    function organellenRuhig(ausser) {
        bewegt.forEach(i => {
            if (ausser.includes(i)) return;
            organellenJeZelle[i].forEach(o => {
                o.style.removeProperty('--dx'); o.style.removeProperty('--dy'); o.style.removeProperty('--dr');
            });
            bewegt.delete(i);
        });
    }

    // Nur Zellen malen, die die Kamera gerade sieht (Layout bleibt, nur das Malen entfällt)
    let letzteSichtbare = '';
    function zellenZeigen(liste) {
        const schluessel = liste.join(',');
        if (schluessel === letzteSichtbare) return;
        letzteSichtbare = schluessel;
        zellen.forEach((z, k) => z.toggleAttribute('data-fern', !liste.includes(k)));
    }

    let letzteAktive = null;
    function aktiveZelle(i, nahBei) {
        const schluessel = `${i}|${nahBei}`;
        if (schluessel === letzteAktive) return;   // nur ändern, was sich ändert
        letzteAktive = schluessel;
        zellen.forEach((z, k) => {
            z.classList.toggle('aktiv', k === i);
            z.classList.toggle('nah', Math.abs(k - nahBei) <= 1);
        });
    }

    function andocken(a) {
        setze(panel, '--andock-x', `${andock.x * a}px`);
        setze(panel, '--andock-y', `${andock.y * a}px`);
        setze(panel, '--andock-s', String(mix(1, andock.s, a)));
        setze(panel, '--panel-o', String(1 - bereich(a, 0.55, 0.95)));
        panel.toggleAttribute('data-weg', a > 0.97);
        const o = bereich(a, 0.6, 1);
        setze(leiste, '--leiste-o', String(o));
        leiste.toggleAttribute('data-da', o > 0.01);
    }

    function takt() {
        geplant = false;
        if (!achse.length) return;
        const y = begrenze(scrollY, 0, gesamt);
        const a = achse.find(s => y < s.start + s.laenge) || achse[achse.length - 1];
        const t = a.laenge ? bereich(y, a.start, a.start + a.laenge) : 1;

        let film = null, dunkel = false, randR = 0, randO = 0, footerO = 0, sichtbar = [0];
        andocken(a.typ === 'hinein' ? sanft(bereich(t, 0, 0.6)) : 1);

        switch (a.typ) {
            case 'hinein':
                film = (BILDER - 1) * (1 - t);
                weltZeigen(einstieg);
                inLinse(film);
                dunkel = true;
                aktiveZelle(-1, 0);
                break;
            case 'oeffnen': {
                const r0 = (linse(0) || { r: vh * 0.25 }).r;
                const loch = mix(r0, rVoll, sanft(t));
                frei(loch);
                weltZeigen(mixKamera(a.von, a.nach, t));
                randR = loch; randO = 1 - bereich(t, 0.55, 0.95);
                dunkel = loch < rVoll * 0.55;
                aktiveZelle(t > 0.8 ? 0 : -1, 0);
                break;
            }
            case 'zelle':
                frei(rVoll);
                weltZeigen(mixKamera(a.von, a.nach, t));
                aktiveZelle(a.zelle, a.zelle);
                sichtbar = [a.zelle];
                organellenRuhig([]);
                break;
            case 'uebergang':
                frei(rVoll);
                weltZeigen({
                    x: mix(a.von.x, a.nach.x, sanft(t)),
                    y: mix(a.von.y, a.nach.y, sanft(t)),
                    s: Math.pow(a.tiefster, Math.sin(Math.PI * t)),
                });
                aktiveZelle(t < 0.15 ? a.zelle : t > 0.85 ? a.zelle + 1 : -1, t < 0.5 ? a.zelle : a.zelle + 1);
                organellenRuhig([a.zelle, a.zelle + 1]);
                if (!leicht) organellenTreiben(a, t);
                sichtbar = [a.zelle, a.zelle + 1];
                break;
            case 'abschied': {
                // nach oben hinaus: die letzte Zelle gleitet hoch, der Okular-Kreis schliesst sich
                const r0 = (linse(0) || { r: vh * 0.25 }).r;
                const loch = mix(rVoll, r0, sanft(bereich(t, 0.3, 1)));
                frei(loch);
                weltZeigen(mixKamera(a.von, a.nach, t));
                randR = loch; randO = bereich(t, 0.35, 0.7);
                dunkel = loch < rVoll * 0.55;
                aktiveZelle(t < 0.2 ? zellen.length - 1 : -1, zellen.length - 1);
                organellenRuhig([]);
                sichtbar = [zellen.length - 1];
                break;
            }
            case 'hinaus':
                film = (BILDER - 1) * t;
                weltZeigen(abschied);
                sichtbar = [zellen.length - 1];
                inLinse(film);
                dunkel = true;
                footerO = sanft(bereich(t, 0.7, 1));
                break;
        }

        zellenZeigen(sichtbar);
        buehne.toggleAttribute('hidden', film === null);
        if (film !== null) zeichne(Math.round(film));
        setze(okularRand, '--rand-r', `${randR}px`);
        setze(okularRand, '--rand-o', String(randO));
        setze(footer, '--footer-o', String(footerO));
        footer.toggleAttribute('data-da', footerO > 0.01);
        nav.toggleAttribute('data-auf-dunkel', dunkel);
    }

    let geplant = false;
    function planen() {
        if (!geplant) { geplant = true; requestAnimationFrame(takt); }
    }

    // Ruckel-Wächter: Solange gescrollt wird, misst eine Bildschleife die echten Abstände
    // zwischen zwei gezeichneten Bildern. Liegt der Median der letzten 30 Bilder über 30 ms
    // (unter ~33 Bilder/s), schaltet die Seite einmalig in den Sparmodus.
    const abstaende = [];
    let letzterScroll = 0, schleifeLaeuft = false;
    function messen(t, vorher) {
        if (leicht) return;
        if (vorher !== undefined) {
            abstaende.push(t - vorher);
            if (abstaende.length > 30) abstaende.shift();      // gleitendes Fenster: letzte 30 Bilder
            if (abstaende.length === 30 && [...abstaende].sort((x, y) => x - y)[15] > 30) { sparmodus(); return; }
        }
        if (performance.now() - letzterScroll < 300) requestAnimationFrame(t2 => messen(t2, t));
        else { schleifeLaeuft = false; abstaende.length = 0; }   // Pause: neu messen
    }
    addEventListener('scroll', () => {
        letzterScroll = performance.now();
        if (!schleifeLaeuft && !leicht) { schleifeLaeuft = true; requestAnimationFrame(t => messen(t)); }
    }, { passive: true });

    // =================================================================
    // Anker, Tastatur, Grössenänderung
    // =================================================================
    function zuZelle(i, versatz = 0, verhalten = 'smooth') {
        const a = zellBeginn(i);
        if (a) scrollTo({ top: a.start + begrenze(versatz, 0, a.laenge), behavior: verhalten });
    }

    document.addEventListener('click', e => {
        const link = e.target.closest && e.target.closest('a[href^="#"]');
        if (!link) return;
        const ziel = document.getElementById(link.getAttribute('href').slice(1));
        const zelle = ziel && ziel.closest('.zelle');
        if (!zelle) return;
        e.preventDefault();
        zuZelle(zellen.indexOf(zelle));
        zelle.focus({ preventScroll: true });
    });

    // Tab-Navigation: die Kamera folgt dem Fokus
    document.addEventListener('focusin', e => {
        const zelle = e.target.closest && e.target.closest('.zelle');
        if (!zelle) return;
        const i = zellen.indexOf(zelle);
        const a = zellBeginn(i);
        if (!a || (scrollY >= a.start && scrollY <= a.start + a.laenge && e.target === zelle)) return;
        let versatz = 0;
        for (let el = e.target; el && el !== zelle; el = el.offsetParent) versatz += el.offsetTop;
        zuZelle(i, versatz - (vh - oben - unten) * 0.3, 'instant');
    });

    let format0 = null;
    addEventListener('resize', () => {
        const anteil = gesamt ? scrollY / gesamt : 0;
        aufbauen();
        if (format0 !== bildFormat()) { format0 = bildFormat(); bilderLaden(); }
        scrollTo({ top: anteil * gesamt, behavior: 'instant' });
        planen();
    });
    // Grosse Ebenen nur während der Bewegung auf dem Grafikchip halten; in Ruhe freigeben
    // (spart Grafikspeicher, und der Browser malt den Text danach einmal gestochen scharf).
    let ruheTimer = 0;
    addEventListener('scroll', () => {
        html.classList.add('in-bewegung');
        clearTimeout(ruheTimer);
        ruheTimer = setTimeout(() => html.classList.remove('in-bewegung'), 200);
    }, { passive: true });
    addEventListener('scroll', planen, { passive: true });

    format0 = bildFormat();
    bilderLaden();
    aufbauen();
    // Schriften verändern Zellhöhen: danach die Zeitachse neu messen
    if (document.fonts) document.fonts.ready.then(() => { aufbauen(); planen(); });
    addEventListener('load', () => { aufbauen(); planen(); });
    takt();
})();
