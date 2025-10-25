function initCountdown() {
    const targetDate = new Date('2025-10-25T19:00:00').getTime();
    
    const daysElement = document.getElementById('days');
    const hoursElement = document.getElementById('hours');
    const minutesElement = document.getElementById('minutes');
    const secondsElement = document.getElementById('seconds');
    
    function updateCountdown() {
        const now = new Date().getTime();
        const distance = targetDate - now;
        
        if (distance < 0) {
            daysElement.textContent = '00';
            hoursElement.textContent = '00';
            minutesElement.textContent = '00';
            secondsElement.textContent = '00';
            return;
        }
        
        const days = Math.floor(distance / (1000 * 60 * 60 * 24));
        const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);
        
        daysElement.textContent = days.toString().padStart(2, '0');
        hoursElement.textContent = hours.toString().padStart(2, '0');
        minutesElement.textContent = minutes.toString().padStart(2, '0');
        secondsElement.textContent = seconds.toString().padStart(2, '0');
    }
    
    updateCountdown();
    setInterval(updateCountdown, 1000);
}

initCountdown(); // Startet den Countdown

//Cookies

document.addEventListener("DOMContentLoaded", () => {
  const banner = document.getElementById("cookie-banner");
  const acceptBtn = document.getElementById("accept-cookies");
  const declineBtn = document.getElementById("decline-cookies");

  // Prüfen, ob Nutzer schon gewählt hat
  if (!localStorage.getItem("cookiesChoice")) {
    banner.style.display = "flex";
  }

  acceptBtn.addEventListener("click", () => {
    localStorage.setItem("cookiesChoice", "accepted");
    banner.style.display = "none";
    enableCookies(); // Hier würdest du z. B. Analytics aktivieren
  });

  declineBtn.addEventListener("click", () => {
    localStorage.setItem("cookiesChoice", "declined");
    banner.style.display = "none";
  });
});

function enableCookies() {
  console.log("Cookies wurden akzeptiert — hier kannst du Scripts starten.");
}

// --- Burger-Menü Steuerung ---
const toggleButton = document.getElementById('menu-toggle');
const navLinks = document.getElementById('nav-links');

toggleButton.addEventListener('click', () => {
	navLinks.classList.toggle('show');
});

// Menü automatisch schließen, wenn ein Link angeklickt wird
navLinks.querySelectorAll('a').forEach(link => {
	link.addEventListener('click', () => {
		navLinks.classList.remove('show');
	});
});