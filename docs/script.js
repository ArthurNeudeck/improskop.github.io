// =====================================================================
// IMPROSKOP – Interaktion auf allen Seiten
// Navigation, Countdown, Cookies, Glanzlicht, Rückblick-Pfeile.
// Die Kamera der Startseite steckt in zellen.js.
// =====================================================================

// --- Liquid Glass ---------------------------------------------------------
// Lichtbrechung per SVG-Filter kann nur Chromium; alle anderen nutzen den Blur.
// Nur auf starken Geräten: der SVG-Filter ist der teuerste Glas-Effekt.
const starkesGeraet = (navigator.hardwareConcurrency || 0) >= 8 && !(navigator.deviceMemory && navigator.deviceMemory <= 4);
if (starkesGeraet && navigator.userAgentData && navigator.userAgentData.brands.some(b => /Chromium/.test(b.brand))) {
    document.documentElement.classList.add('brechung');
}

// Glanzlicht folgt dem Mauszeiger (nur mit Maus)
if (matchMedia('(hover: hover) and (pointer: fine)').matches) {
    document.addEventListener('pointermove', e => {
        const glas = e.target.closest && e.target.closest('.glas');
        if (!glas) return;
        const r = glas.getBoundingClientRect();
        glas.style.setProperty('--gx', `${((e.clientX - r.left) / r.width) * 100}%`);
        glas.style.setProperty('--gy', `${((e.clientY - r.top) / r.height) * 100}%`);
    });
}

// --- Navigation -------------------------------------------------------------
const nav = document.querySelector('.nav');
const toggleButton = document.getElementById('menu-toggle');
const navLinks = document.getElementById('nav-links');

function menuSchliessen() {
    navLinks.classList.remove('offen');
    toggleButton.setAttribute('aria-expanded', 'false');
    toggleButton.setAttribute('aria-label', 'Menü öffnen');
}

if (toggleButton && navLinks) {
    toggleButton.addEventListener('click', () => {
        const offen = navLinks.classList.toggle('offen');
        toggleButton.setAttribute('aria-expanded', String(offen));
        toggleButton.setAttribute('aria-label', offen ? 'Menü schliessen' : 'Menü öffnen');
    });
    navLinks.querySelectorAll('a').forEach(link => link.addEventListener('click', menuSchliessen));
    document.addEventListener('keydown', e => { if (e.key === 'Escape') menuSchliessen(); });
}

// Liegt die Navigation über einer dunklen Fläche? Dann helles Glas-Design.
const dunkleFlaechen = [...document.querySelectorAll('[data-dunkel], .footer--statisch')];
function navFarbe() {
    if (!nav) return;
    const n = nav.getBoundingClientRect();
    const y = n.top + n.height / 2;
    const dunkel = dunkleFlaechen.some(el => {
        const r = el.getBoundingClientRect();
        return r.top <= y && r.bottom >= y;
    });
    nav.toggleAttribute('data-auf-dunkel', dunkel);
}

// --- Countdown ----------------------------------------------------------------
// Zieldatum steht im HTML (data-ziel). Ist es vorbei, wird der Countdown ausgeblendet.
function initCountdown() {
    const countdown = document.getElementById('countdown');
    if (!countdown) return;
    const targetDate = new Date(countdown.dataset.ziel).getTime();
    const felder = ['days', 'hours', 'minutes', 'seconds'].map(id => document.getElementById(id));

    function updateCountdown() {
        const distance = targetDate - Date.now();
        if (distance < 0) {
            countdown.hidden = true;
            clearInterval(takt);
            return;
        }
        const werte = [
            Math.floor(distance / 86400000),
            Math.floor((distance % 86400000) / 3600000),
            Math.floor((distance % 3600000) / 60000),
            Math.floor((distance % 60000) / 1000),
        ];
        felder.forEach((el, i) => { el.textContent = String(werte[i]).padStart(2, '0'); });
    }
    const takt = setInterval(updateCountdown, 1000);
    updateCountdown();
}
initCountdown();

// --- Cookie-Banner ------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    const banner = document.getElementById('cookie-banner');
    const acceptBtn = document.getElementById('accept-cookies');
    const declineBtn = document.getElementById('decline-cookies');
    if (!banner || !acceptBtn || !declineBtn) return;

    let gespeichert = null;
    try { gespeichert = localStorage.getItem('cookiesChoice'); } catch (e) { /* privates Fenster */ }
    if (!gespeichert) banner.style.display = 'flex';

    const wahl = wert => {
        try { localStorage.setItem('cookiesChoice', wert); } catch (e) { /* egal */ }
        banner.style.display = 'none';
    };
    acceptBtn.addEventListener('click', () => { wahl('accepted'); enableCookies(); });
    declineBtn.addEventListener('click', () => wahl('declined'));
});

// Wird aufgerufen, wenn Cookies akzeptiert wurden (z. B. für Analytics)
function enableCookies() {}

// --- Rückblick-Streifen: Pfeile ----------------------------------------------
document.querySelectorAll('[data-streifen]').forEach(knopf => {
    knopf.addEventListener('click', () => {
        const streifen = knopf.closest('section').querySelector('.streifen');
        const bild = streifen.querySelector('figure');
        streifen.scrollBy({ left: Number(knopf.dataset.streifen) * (bild.offsetWidth + 24), behavior: 'smooth' });
    });
});

// --- Navigationsfarbe auf Unterseiten (Startseite: zellen.js) ----------------
if (!document.querySelector('.objekttraeger')) {
    let geplant = false;
    const pruefen = () => { geplant = false; navFarbe(); };
    addEventListener('scroll', () => { if (!geplant) { geplant = true; requestAnimationFrame(pruefen); } }, { passive: true });
    navFarbe();
}
