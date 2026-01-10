// --- Burger-Menü Steuerung ---
// Burger-Menü: Steuert das mobile Navigationsmenü, öffnet/schließt Menü beim Klick auf Burger-Icon
const toggleButton = document.getElementById('menu-toggle');
const navLinks = document.getElementById('nav-links');

if (toggleButton && navLinks) {
	// Toggle-Event: Öffnet oder schließt das Menü beim Klick auf Burger-Button
	toggleButton.addEventListener('click', () => {
		navLinks.classList.toggle('show');
	});

	// Link-Klick-Event: Schließt das Menü automatisch nach Klick auf einen Link
	navLinks.querySelectorAll('a').forEach(link => {
		link.addEventListener('click', () => {
			navLinks.classList.remove('show');
		});
	});
}

// Countdown-Funktion: Berechnet und aktualisiert die verbleibende Zeit bis zur nächsten Show
function initCountdown() {
    // Ziel-Datum: Datum und Uhrzeit der nächsten Show
    const targetDate = new Date('2026-01-31T19:00:00').getTime();

    // DOM-Elemente: Referenzen zu den Countdown-Anzeigeelementen
    const daysElement = document.getElementById('days');
    const hoursElement = document.getElementById('hours');
    const minutesElement = document.getElementById('minutes');
    const secondsElement = document.getElementById('seconds');

    // Prüfung: Beendet Funktion wenn Elemente nicht vorhanden sind
    if (!daysElement || !hoursElement || !minutesElement || !secondsElement) {
        return;
    }

    // Update-Funktion: Berechnet die verbleibende Zeit und aktualisiert die Anzeige
    function updateCountdown() {
        const now = new Date().getTime();
        const distance = targetDate - now;

        // Abgelaufen: Setzt Countdown auf 00 wenn Ziel-Datum erreicht ist
        if (distance < 0) {
            daysElement.textContent = '00';
            hoursElement.textContent = '00';
            minutesElement.textContent = '00';
            secondsElement.textContent = '00';
            return;
        }

        // Berechnung: Berechnet Tage, Stunden, Minuten und Sekunden aus Millisekunden
        const days = Math.floor(distance / (1000 * 60 * 60 * 24));
        const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);

        // Aktualisierung: Aktualisiert die Anzeige mit führenden Nullen (z.B. "05" statt "5")
        daysElement.textContent = days.toString().padStart(2, '0');
        hoursElement.textContent = hours.toString().padStart(2, '0');
        minutesElement.textContent = minutes.toString().padStart(2, '0');
        secondsElement.textContent = seconds.toString().padStart(2, '0');
    }

    // Initialisierung: Startet Countdown sofort und aktualisiert jede Sekunde
    updateCountdown();
    setInterval(updateCountdown, 1000);
}

initCountdown(); // Startet den Countdown, falls Elemente vorhanden sind

//Cookies
// Cookie-Banner-Verwaltung: Steuert die Anzeige des Cookie-Banners und speichert Nutzerauswahl

document.addEventListener("DOMContentLoaded", () => {
  // DOM-Elemente: Referenzen zu Cookie-Banner und Buttons
  const banner = document.getElementById("cookie-banner");
  const acceptBtn = document.getElementById("accept-cookies");
  const declineBtn = document.getElementById("decline-cookies");

  // Prüfung: Beendet Funktion wenn Elemente nicht vorhanden sind
  if (!banner || !acceptBtn || !declineBtn) {
    return;
  }

  // Banner-Anzeige: Zeigt Banner nur wenn noch keine Auswahl getroffen wurde
  if (!localStorage.getItem("cookiesChoice")) {
    banner.style.display = "flex";
  }

  // Akzeptieren-Button: Speichert Auswahl und versteckt Banner, aktiviert Cookies
  acceptBtn.addEventListener("click", () => {
    localStorage.setItem("cookiesChoice", "accepted");
    banner.style.display = "none";
    enableCookies(); // Hier würdest du z. B. Analytics aktivieren
  });

  // Ablehnen-Button: Speichert Auswahl und versteckt Banner
  declineBtn.addEventListener("click", () => {
    localStorage.setItem("cookiesChoice", "declined");
    banner.style.display = "none";
  });
});

// Cookie-Aktivierung: Funktion die aufgerufen wird wenn Cookies akzeptiert wurden
function enableCookies() {
  console.log("Cookies wurden akzeptiert — hier kannst du Scripts starten.");
}


// Intersection Observer: Beobachtet wann hervorgehobene Wörter sichtbar werden und aktiviert Animation
const target = document.querySelector('.highlight-word');

// Observer: Überwacht ob Element im sichtbaren Bereich ist und fügt/entfernt 'active'-Klasse
const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    // Aktivierung: Fügt 'active'-Klasse hinzu wenn Element sichtbar wird
    if (entry.isIntersecting) target.classList.add('active');
    // Deaktivierung: Entfernt 'active'-Klasse wenn Element nicht mehr sichtbar ist
    else target.classList.remove('active');
  });
});
