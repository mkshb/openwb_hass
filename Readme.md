# openWB Home Assistant Integration - ENGLISH

This Home Assistant custom integration seamlessly connects your openWB charging station to your smart home via MQTT. It automatically reads all relevant MQTT data and creates matching sensors – including data for wallbox, vehicles, battery, and photovoltaic system (PV).

---

## 🔧 Features

### ✅ Automatic MQTT Discovery

- Subscribes to all `openWB/#` topics via MQTT.
- Automatically detects new devices and values.
- Creates matching entities (sensors) on-the-fly.

---

### ⚡ Supported Device Categories

| Category          | Example Topic                        | Description                              |
|-------------------|---------------------------------------|------------------------------------------|
| **Charge Points** | `openWB/chargepoint/0/#`              | Status, configuration, phases, etc.      |
| **Vehicles**      | `openWB/vehicle/0/#`                 | SoC, template, info, etc.                |
| **Battery**       | `openWB/bat/0/#`                     | Charging power, SoC, current, etc.       |
| **PV System**     | `openWB/pv/0/#`                      | Generation, voltages, error messages     |
| **Summaries**     | `openWB/bat/get/`, `openWB/pv/get/`  | Total power, energy, etc.                |
| **Meter Data**    | `openWB/counter/0/#`                 | Import/export, power, frequency, etc.    |

---

### 🧠 Template Names

- Automatically loads names for `charge_template` and `ev_template` from the following topics:
  - `openWB/vehicle/template/charge_template/<id>`
  - `openWB/vehicle/template/ev_template/<id>`

These templates are displayed as human-readable text (e.g., `Fast Charge`, `Overnight Slow`).

---

### 🎚️ Select Entity for Charge Template

- The integration automatically creates a `select` entity for each detected vehicle.
- This select entity allows switching between available `charge_template` profiles in openWB directly from the Home Assistant UI.

---

## 🛣️ Roadmap

- [x] Automatic detection of MQTT topics (`openWB/#`)
- [x] Dynamic creation of sensor entities
- [x] Support for vehicle templates (`charge_template`, `ev_template`)
- [x] Chargepoint configuration mapped to individual entities
- [x] Select entities for choosing charge templates

### Planned:
- [ ] Extended control of openWB via `set/` topics
- [ ] Automated charging planning using PV/SoC forecasts
- [ ] Multilingual UI (DE/EN)

---
---
# openWB Home Assistant Integration - GERMAN

Diese Home Assistant Custom Integration bindet eine openWB-Ladestation über MQTT nahtlos in dein Smart Home ein. Sie liest automatisch alle relevanten MQTT-Daten aus und erstellt daraus passende Sensoren – inklusive Wallbox-, Fahrzeug-, Batterie- und PV-Daten.

---

## 🔧 Funktionen

### ✅ Automatische MQTT-Erkennung

- Abonniert alle `openWB/#`-Topics per MQTT.
- Erkennt automatisch neue Geräte und Werte.
- Erstellt passende Entitäten (Sensoren) on-the-fly.

---

### ⚡ Unterstützte Gerätegruppen

| Gerätegruppe | Beispiel-Topic                        | Beschreibung                             |
|--------------|----------------------------------------|------------------------------------------|
| **Ladepunkte**   | `openWB/chargepoint/0/#`             | Status, Konfiguration, Phasen etc.       |
| **Fahrzeuge**    | `openWB/vehicle/0/#`                | SoC, Template, Info, etc.                |
| **Batterie**     | `openWB/bat/0/#`                    | Ladeleistung, SoC, Strom etc.            |
| **PV-Anlage**    | `openWB/pv/0/#`                     | Erzeugung, Spannungen, Fehlertexte       |
| **Summenwerte**  | `openWB/bat/get/`, `openWB/pv/get/` | Gesamtleistung, Energie etc.             |
| **Zählerdaten**  | `openWB/counter/0/#`                | Import/Export, Leistung, Frequenz etc.   |

---

### 🧠 Template-Namen

- Lädt automatisch die Namen für `charge_template` und `ev_template` aus den Topics:
  - `openWB/vehicle/template/charge_template/<id>`
  - `openWB/vehicle/template/ev_template/<id>`

Diese Vorlagen werden korrekt als lesbarer Text angezeigt (z. B. `Schnellladen`, `Langsam über Nacht`).

### 🎚️ Auswahl-Entität für Charge Template

- Die Integration erstellt automatisch eine `select`-Entität für jedes erkannte Fahrzeug.
- Diese Entität erlaubt es, das aktuell verwendete `charge_template`-Profil direkt über die Home Assistant-Oberfläche umzuschalten.

## 🛣️ Roadmap

- [x] Automatische Erkennung von MQTT-Topics (`openWB/#`)
- [x] Dynamische Erstellung von Sensoren
- [x] Unterstützung für Fahrzeug-Templates (`charge_template`, `ev_template`)
- [x] Ladepunkt-Konfiguration als Entitäten
- [x] Select-Entitäten für Ladeprofile

### Geplant:
- [ ] Weitere Steuerung von openWB via `set/`-Topics
- [ ] Automatisierte Ladeplanung mit PV-/SoC-Prognosen
- [ ] Mehrsprachige Oberfläche (DE/EN)


---

# Screenshots

![Overview Entities](images/overview-entities.png)
![Example Entities](images/example-entities.png)
![Change Charging Template](images/change-charging-template.png)
