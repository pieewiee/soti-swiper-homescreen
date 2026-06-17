#!/usr/bin/env python3
"""SOTI MobiControl Offline Template Builder.

Python-Portierung von build-offline-template.ps1.
Lädt externe Abhängigkeiten (CSS/JS/Fonts/Logo) herunter, bettet sie als
Inline-Inhalte bzw. base64 Data-URIs in das HTML-Template ein und wendet die
Konfiguration aus config.json an, sodass eine vollständig offline-fähige
HTML-Datei entsteht.
"""

import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

# Einrückungen für den Device-Info-Block (entspricht den Leerzeichen im Original)
IND20 = " " * 20
IND24 = " " * 24


class C:
    """ANSI-Farbcodes (entsprechen den Write-Host -ForegroundColor Farben)."""

    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    CYAN = "\033[36m"
    GRAY = "\033[90m"
    RESET = "\033[0m"


def enable_ansi() -> None:
    """Aktiviert ANSI/VT-Verarbeitung und UTF-8-Ausgabe unter Windows."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if os.name == "nt":
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            # ENABLE_PROCESSED_OUTPUT | ENABLE_WRAP_AT_EOL_OUTPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass


def log(message: str, color: str = "") -> None:
    """Gibt eine farbige Konsolenzeile aus (entspricht Write-Host)."""
    if color:
        print(f"{color}{message}{C.RESET}")
    else:
        print(message)


def error_exit(message: str) -> None:
    """Gibt eine Fehlermeldung aus und beendet das Programm (entspricht Write-Error + exit 1)."""
    print(f"{C.RED}ERROR: {message}{C.RESET}", file=sys.stderr)
    sys.exit(1)


def get_web_content(url: str, description: str) -> str:
    """Lädt Textinhalt (CSS/JS) mit bis zu 3 Versuchen herunter."""
    log(f"📥 Downloading {description}...", C.YELLOW)

    for attempt in range(1, 4):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(request, timeout=30) as response:
                if getattr(response, "status", 200) == 200:
                    content = response.read().decode("utf-8")
                    log("   ✅ Downloaded successfully", C.GREEN)
                    return content
        except Exception as exc:  # noqa: BLE001 - entspricht catch im Original
            log(f"   ❌ Attempt {attempt} failed: {exc}", C.RED)
            if attempt == 3:
                raise RuntimeError(f"Failed to download {description} after 3 attempts")
            time.sleep(2)

    raise RuntimeError(f"Failed to download {description} after 3 attempts")


def download_bytes(url: str) -> bytes:
    """Lädt Binärinhalt (Fonts/Logo) herunter."""
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def read_text(path: str) -> str:
    """Liest eine Datei als Text und entfernt ein eventuelles BOM (wie Get-Content -Raw)."""
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        return handle.read()


def build_demo_apps() -> list:
    """Demo-App-Daten für alle 19 SOTI-App-Slots."""
    return [
        {"name": "Work Orders", "icon": "work-orders.png", "url": "Launch://com.company.workorders"},
        {"name": "Inventory Scanner", "icon": "inventory.png", "url": "Launch://com.company.scanner"},
        {"name": "Safety Checklist", "icon": "safety.png", "url": "Launch://com.company.safety"},
        {"name": "Time Tracker", "icon": "timetrack.png", "url": "Launch://com.company.timetrack"},
        {"name": "Asset Manager", "icon": "assets.png", "url": "Launch://com.company.assets"},
        {"name": "Quality Control", "icon": "qc.png", "url": "Launch://com.company.qc"},
        {"name": "Maintenance Log", "icon": "maintenance.png", "url": "Launch://com.company.maint"},
        {"name": "Reports Hub", "icon": "reports.png", "url": "Launch://com.company.reports"},
        {"name": "Team Chat", "icon": "chat.png", "url": "Launch://com.company.chat"},
        {"name": "Document Library", "icon": "docs.png", "url": "Launch://com.company.docs"},
        {"name": "Training Portal", "icon": "training.png", "url": "Launch://com.company.training"},
        {"name": "Emergency Contacts", "icon": "emergency.png", "url": "Launch://com.company.emergency"},
        {"name": "Fleet Tracker", "icon": "fleet.png", "url": "Launch://com.company.fleet"},
        {"name": "Compliance Check", "icon": "compliance.png", "url": "Launch://com.company.compliance"},
        {"name": "Production Monitor", "icon": "production.png", "url": "Launch://com.company.production"},
        {"name": "Shift Schedule", "icon": "schedule.png", "url": "Launch://com.company.schedule"},
        {"name": "Equipment Status", "icon": "equipment.png", "url": "Launch://com.company.equipment"},
        {"name": "Facility Map", "icon": "facility.png", "url": "Launch://com.company.facility"},
        {"name": "Help Desk", "icon": "helpdesk.png", "url": "Launch://com.company.helpdesk"},
    ]


def build_device_info(config: dict) -> str:
    """Erzeugt den HTML-Inhalt für das Geräteinformations-Modal."""
    content = ""
    device_info = config.get("deviceInfo", {})
    if not device_info.get("enabled"):
        return content

    for category in device_info.get("categories", {}).values():
        if not category.get("enabled"):
            continue

        title = category.get("title", "")
        icon = category.get("icon", "")

        # Kategorie-Überschrift
        content += f"{IND20}<!-- {title} -->\n"
        content += f'{IND20}<div class="device-info-category">\n'
        content += f'{IND24}<i class="bi {icon} me-1"></i>\n'
        content += f"{IND24}{title}\n"
        content += f"{IND20}</div>\n\n"

        # Felder dieser Kategorie
        for field in category.get("fields", {}).values():
            if not field.get("enabled"):
                continue

            label = field.get("label", "")
            variable = field.get("variable", "")
            content += f'{IND20}<div class="device-info-item">\n'
            content += f'{IND24}<span class="device-info-label">{label}:</span>\n'
            content += f'{IND24}<span class="device-info-value">{variable}</span>\n'
            content += f"{IND20}</div>\n\n"

    return content


def main() -> None:
    enable_ansi()

    parser = argparse.ArgumentParser(
        description="SOTI MobiControl Offline Template Builder",
    )
    parser.add_argument("-c", "--config", dest="config_path", default="config.json")
    parser.add_argument(
        "-t", "--template", dest="template_path", default="soti-final-lockdown-homescreen.html"
    )
    parser.add_argument(
        "-o", "--output", dest="output_path", default="soti-final-lockdown-homescreen-offline.html"
    )
    parser.add_argument("-d", "--demo", dest="demo_mode", action="store_true")
    args = parser.parse_args()

    config_path = args.config_path
    template_path = args.template_path
    output_path = args.output_path
    demo_mode = args.demo_mode

    log("🚀 SOTI MobiControl Offline Template Builder", C.GREEN)
    if demo_mode:
        log("🎭 DEMO MODE ACTIVE", C.YELLOW)
    log("================================================", C.GREEN)

    # Konfiguration laden
    if not os.path.isfile(config_path):
        error_exit(f"Config file not found: {config_path}")

    try:
        config = json.loads(read_text(config_path))
        log("✅ Config loaded successfully", C.GREEN)
    except Exception as exc:  # noqa: BLE001
        error_exit(f"Failed to parse config.json: {exc}")

    # Template laden
    if not os.path.isfile(template_path):
        error_exit(f"Template file not found: {template_path}")

    template = read_text(template_path)
    log("✅ Template loaded successfully", C.GREEN)

    # Demo-Modus: Testdaten für alle 19 SOTI-App-Slots einsetzen
    if demo_mode:
        log("🎭 Demo Mode Enabled - Creating demo homescreen...", C.YELLOW)

        # Ausgabepfad für den Demo-Modus ändern
        output_path = "demo-homescreen.html"

        demo_apps = build_demo_apps()

        for i in range(19):
            app = demo_apps[i]
            template = template.replace(f"<MCLink{i}>", app["url"])
            template = template.replace(f"<MCDISP{i}>", app["name"])
            template = template.replace(f"<MCExeIcon{i}>", app["icon"])
            template = template.replace(f"<MCDispImg{i}>", app["icon"])

        log(f"   ✅ Injected {len(demo_apps)} demo apps", C.GREEN)
        log(f"   📱 Apps: {', '.join(a['name'] for a in demo_apps)}", C.GRAY)

    # Alle Abhängigkeiten herunterladen
    log("\n🔄 Downloading external dependencies...", C.CYAN)

    dependencies: dict = {}
    downloaded_count = 0
    enabled_deps = [d for d in config.get("dependencies", []) if d.get("enabled")]

    for dep in enabled_deps:
        try:
            if dep.get("type") == "font":
                # Font-Dateien als Binärdaten behandeln
                log(f"📥 Downloading font: {dep['name']}...", C.YELLOW)

                font_bytes = download_bytes(dep["url"])
                font_base64 = base64.b64encode(font_bytes).decode("ascii")

                dependencies[dep["name"]] = {
                    "content": f"data:{dep['mimeType']}; base64, {font_base64}",
                    "type": dep["type"],
                    "placeholder": dep["placeholder"],
                }
                size_kb = round(len(font_bytes) / 1024, 1)
                log(f"   ✅ Font downloaded and converted ({size_kb} KB)", C.GREEN)
            else:
                # Textbasierte Abhängigkeiten (CSS, JS)
                dependencies[dep["name"]] = {
                    "content": get_web_content(dep["url"], dep["name"]),
                    "type": dep["type"],
                    "placeholder": dep["placeholder"],
                }
            downloaded_count += 1
        except Exception as exc:  # noqa: BLE001
            log(f"   ❌ Failed to download {dep['name']}: {exc}", C.RED)
            log(f"   ⚠️  Skipping {dep['name']}", C.YELLOW)

    # Logo herunterladen und in base64 umwandeln, falls logoUrl angegeben ist
    branding = config.get("branding", {})
    logo_url = branding.get("logoUrl", "")
    if logo_url:
        try:
            log("📥 Downloading BI logo...", C.YELLOW)

            logo_bytes = download_bytes(logo_url)
            logo_base64 = base64.b64encode(logo_bytes).decode("ascii")

            # MIME-Typ anhand der URL bestimmen, Standard ist PNG
            mime_type = "image/png"
            if re.search(r"\.svg$", logo_url, re.IGNORECASE):
                mime_type = "image/svg+xml"
            elif re.search(r"\.jpg$|\.jpeg$", logo_url, re.IGNORECASE):
                mime_type = "image/jpeg"
            elif re.search(r"\.gif$", logo_url, re.IGNORECASE):
                mime_type = "image/gif"

            dependencies["Logo"] = {
                "content": f"data:{mime_type}; base64, {logo_base64}",
                "type": "logo",
                "placeholder": "LOGO_BASE64_PLACEHOLDER",
            }
            size_kb = round(len(logo_bytes) / 1024, 1)
            log(f"   ✅ Logo converted to base64 successfully ({size_kb} KB)", C.GREEN)
        except Exception as exc:  # noqa: BLE001
            log(f"   ⚠️  Logo download failed: {exc}", C.YELLOW)
            log("   📄 Using embedded SVG fallback", C.YELLOW)
            dependencies["Logo"] = {
                "content": branding.get("logoBase64", ""),
                "type": "logo",
                "placeholder": "LOGO_BASE64_PLACEHOLDER",
            }
    else:
        log("📄 Using embedded SVG logo from config", C.YELLOW)
        dependencies["Logo"] = {
            "content": branding.get("logoBase64", ""),
            "type": "logo",
            "placeholder": "LOGO_BASE64_PLACEHOLDER",
        }

    log(f"✅ Downloaded {downloaded_count} dependencies successfully\n", C.GREEN)

    # Externe Verweise durch eingebettete Inhalte ersetzen
    log("🔧 Embedding dependencies into template...", C.CYAN)

    embedded_count = 0

    for dep_name, dep in dependencies.items():
        try:
            dep_type = dep.get("type")
            if dep_type == "css":
                # Bootstrap-Icons-CSS verarbeiten: Font-URLs durch Platzhalter ersetzen
                css_content = dep["content"]
                if dep_name == "Bootstrap Icons":
                    css_content = re.sub(
                        r'url\("\./fonts/bootstrap-icons\.woff2[^"]*"\)',
                        'url("BOOTSTRAP_ICONS_WOFF2_PLACEHOLDER")',
                        css_content,
                        flags=re.IGNORECASE,
                    )
                    css_content = re.sub(
                        r'url\("\./fonts/bootstrap-icons\.woff[^"]*"\)',
                        'url("BOOTSTRAP_ICONS_WOFF_PLACEHOLDER")',
                        css_content,
                        flags=re.IGNORECASE,
                    )

                embedded_content = f"<style>\n{css_content}\n</style>"
                log(f"   🎨 Embedding CSS: {dep_name}", C.YELLOW)
            elif dep_type == "js":
                embedded_content = f"<script>\n{dep['content']}\n</script>"
                log(f"   ⚡ Embedding JS: {dep_name}", C.YELLOW)
            elif dep_type == "logo":
                embedded_content = dep["content"]
                log(f"   🖼️  Embedding Logo: {dep_name}", C.YELLOW)
            elif dep_type == "font":
                embedded_content = dep["content"]
                log(f"   🔤 Embedding Font: {dep_name}", C.YELLOW)
            else:
                log(f"   ⚠️  Unknown dependency type: {dep_type} for {dep_name}", C.YELLOW)
                continue

            # Platzhalter durch eingebetteten Inhalt ersetzen
            placeholder = dep["placeholder"]
            if placeholder in template:
                template = template.replace(placeholder, embedded_content)
                log(f"   ✅ {dep_name} embedded successfully", C.GREEN)
                embedded_count += 1
            else:
                log(f"   ⚠️  Placeholder not found for {dep_name}", C.YELLOW)
                log(f"   🔍 Looking for: {placeholder}", C.GRAY)

                # Für CSS: vor </head> einfügen
                if dep_type == "css":
                    template = re.sub(
                        r"(\s*</head>)",
                        lambda m: f"\n    {embedded_content}" + m.group(1),
                        template,
                        flags=re.IGNORECASE,
                    )
                    log(f"   ✅ {dep_name} added to head section", C.GREEN)
                    embedded_count += 1
                # Für JS: vor </body> einfügen
                elif dep_type == "js":
                    template = re.sub(
                        r"(\s*</body>)",
                        lambda m: f"\n{embedded_content}\n" + m.group(1),
                        template,
                        flags=re.IGNORECASE,
                    )
                    log(f"   ✅ {dep_name} added before closing body", C.GREEN)
                    embedded_count += 1
                # Für Logo: alternative Platzierung im Skriptabschnitt
                elif dep_type == "logo":
                    logo_pattern = r"(\s*// Create BI Header with base64 logo\s*)"
                    if re.search(logo_pattern, template):
                        template = re.sub(
                            logo_pattern,
                            lambda m: m.group(1)
                            + f'var logoBase64 = "{embedded_content}"; \r\n            ',
                            template,
                        )
                        log(f"   ✅ {dep_name} added to script section", C.GREEN)
                        embedded_count += 1
        except Exception as exc:  # noqa: BLE001
            log(f"   ❌ Failed to embed {dep_name}: {exc}", C.RED)

    log(f"   📊 Embedded {embedded_count} out of {len(dependencies)} dependencies", C.CYAN)

    # Konfigurationswerte anwenden
    log("⚙️  Applying configuration...", C.CYAN)

    template_cfg = config.get("template", {})

    # Titel aktualisieren
    title = template_cfg.get("title", "")
    template = re.sub(
        r"<title>.*?</title>",
        lambda m: f"<title>{title}</title>",
        template,
        flags=re.IGNORECASE,
    )

    # Header-, Footer-Text und Badge aktualisieren
    template = template.replace("HEADER_TEXT_PLACEHOLDER", template_cfg.get("headerText", ""))
    template = template.replace("FOOTER_TEXT_PLACEHOLDER", template_cfg.get("footerText", ""))
    template = template.replace("FOOTER_BADGE_PLACEHOLDER", template_cfg.get("footerBadge", ""))

    # CSS-Custom-Properties mit den Farben aus der Konfiguration aktualisieren
    colors = branding.get("colors", {})
    color_replacements = {
        "--bi-primary": colors.get("primary", ""),
        "--bi-secondary": colors.get("secondary", ""),
        "--bi-neutral": colors.get("neutral", ""),
        "--bi-surface": colors.get("surface", ""),
    }

    for prop, value in color_replacements.items():
        pattern = prop + r":\s*#[0-9A-Fa-f]{ 6 }; "
        replacement = f"{prop}: {value}; "
        template = re.sub(
            pattern, lambda m, r=replacement: r, template, flags=re.IGNORECASE
        )

    # Grid-Konfiguration einsetzen
    apps_cfg = config.get("apps", {})
    grid_config = {
        "gridColumns": {
            "mobile": apps_cfg.get("gridColumns", {}).get("mobile"),
            "tablet": apps_cfg.get("gridColumns", {}).get("tablet"),
        },
        "gridRows": {
            "mobile": apps_cfg.get("gridRows", {}).get("mobile"),
            "tablet": apps_cfg.get("gridRows", {}).get("tablet"),
        },
    }
    grid_json = json.dumps(grid_config, separators=(",", ":"))
    template = template.replace("GRID_CONFIG_PLACEHOLDER", grid_json)

    # Inhalt für das Geräteinformations-Modal erzeugen
    device_info_content = build_device_info(config)

    # Geräteinformations-Platzhalter ersetzen
    template = template.replace(
        "<!-- DEVICE_INFO_CONTENT_PLACEHOLDER -->", device_info_content
    )

    # Metadaten-Kommentar hinzufügen
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    metadata = (
        "    <!--\n"
        "    SOTI MobiControl Offline Template\n"
        f"    Generated: {timestamp}\n"
        f"    Config: {config_path}\n"
        f"    Original Template: {template_path}\n"
        "    All external dependencies embedded for offline use.\n"
        "    -->\n"
        "\n"
    )

    # Hinweis: -replace in PowerShell ist case-insensitiv; die Vorlage nutzt
    # <!doctype html> in Kleinschreibung, daher hier ebenfalls case-insensitiv.
    template = re.sub(
        r"<!DOCTYPE html>",
        lambda m: metadata + "<!DOCTYPE html>",
        template,
        flags=re.IGNORECASE,
    )

    # Endgültiges Template speichern
    try:
        with open(output_path, "w", encoding="utf-8", newline="") as handle:
            handle.write(template)
        log("✅ Offline template created successfully!", C.GREEN)
        log(f"📁 Output file: {output_path}", C.YELLOW)

        file_size = round(os.path.getsize(output_path) / 1024, 2)
        log(f"📊 File size: {file_size} KB", C.YELLOW)
    except Exception as exc:  # noqa: BLE001
        error_exit(f"Failed to save output file: {exc}")

    # Validierung
    log("\n🔍 Validating output...", C.CYAN)

    output_content = read_text(output_path)

    external_links = [
        "cdn.jsdelivr.net",
        "cdnjs.cloudflare.com",
        "fonts.googleapis.com",
    ]

    has_external_deps = False
    for link in external_links:
        if re.search(re.escape(link), output_content, re.IGNORECASE):
            log(f"   ⚠️  Still contains external reference to: {link}", C.YELLOW)
            has_external_deps = True

    if not has_external_deps:
        log("   ✅ No external dependencies found - fully offline ready!", C.GREEN)

    # Zusammenfassung
    log("\n📋 Summary:", C.CYAN)

    type_icons = {"css": "🎨", "js": "⚡", "logo": "🖼️"}
    for dep_name, dep in dependencies.items():
        icon = type_icons.get(dep.get("type"), "📦")
        log(f"   • {icon} {dep_name}: Embedded", C.GREEN)

    log("   • 🏢 BI Branding: Applied", C.GREEN)
    log("   • 📱 Array-based SOTI: Ready", C.GREEN)
    log("   • 🔢 SOTI Variables (0 - 19): Preserved", C.GREEN)
    log("   • 🌐 Offline Compatible: 100%", C.GREEN)

    log("\n🎉 Offline SOTI template ready for deployment!", C.GREEN)
    log(
        f"Upload '{output_path}' to SOTI MobiControl for offline-capable devices.\n",
        C.YELLOW,
    )


if __name__ == "__main__":
    main()
