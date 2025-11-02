# Image Integration Plan

## templates/quotes/home.html:389 Hero Section
- Verwende ein vollbreites Hintergrundbild via CSS (`.hero-section { background-image: url('/static/img/hero-townhouse.jpg'); background-size: cover; background-position: center; }`) oder fuege rechts innerhalb der `.hero-content`-Row ein `<img class="img-fluid rounded-4 shadow-lg">` mit `src="{% static 'img/hero-townhouse.jpg' %}"` hinzu.
- Motiv: modernes Hamburger Stadthaus mit PV-Modulen in warmem Abendlicht; sorgt fuer Lokalkolorit und unterstreicht den Premium-Charakter.

## templates/quotes/home.html:435 Drei Schritte
- Platziere je Schritt eine kleine Bildkachel (`<img class="rounded-circle shadow-sm mb-3 step-photo">`) ueber der Zahl, z. B. Upload-Screenshot, Elektriker am Zaehlerfeld, Fertige Inbetriebnahme.
- Definiere eine einheitliche Groesse (200x200 px) und hinterlege die Assets als `static/img/step-1.jpg`, `step-2.jpg`, `step-3.jpg`.

## templates/quotes/home.html:477 Vertrauensbereich
- Ersetze die Font-Awesome-Icons durch Logos der Zertifikate (`<img src="{% static 'img/logo-vde.svg' %}" alt="VDE Zertifikat" class="cert-logo">`).
- CSS: `.cert-logo { max-width: 160px; filter: drop-shadow(0 2px 6px rgba(0,0,0,0.15)); }`.

## templates/quotes/home.html:525 Leistungen
- Fuege neben den Listen ein Vorher-Nachher-Foto eines modernisierten Schaltschrankes hinzu (`<figure class="text-center"><img class="img-fluid rounded-3 shadow" src="{% static 'img/service-switchgear.jpg' %}"><figcaption class="small text-muted mt-2">Vorbereiteter Zaehlerschrank nach aktueller TAB</figcaption></figure>`).
- Alternativ kannst du eine Collage mit Detailaufnahmen (Ueberspannungsschutz, Verteiler, Messgeraet) einbauen.

## templates/quotes/home.html:600 Kontakt
- Hinterlege fuer die Kontaktkarten dezente Hintergrundbilder (`background-image: url('{% static 'img/contact-hotline.jpg' %}')`) oder fuege ein Gruppenfoto des Service-Teams als breites Banner unterhalb der Karten ein.
- Achte auf dezente Transparenzen (`rgba(0,0,0,0.35)`) fuer Textlesbarkeit, falls Hintergrundbilder verwendet werden.
