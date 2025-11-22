#!/usr/bin/env python
"""
Test-Skript für n8n Arbeitsvorbereiter-Workflow

Sendet Test-Webhooks an den n8n Workflow und zeigt die Antworten an.

Usage:
    python test_n8n_workflow.py --precheck-id 64
    python test_n8n_workflow.py --precheck-id 64 --production
    python test_n8n_workflow.py --list-prechecks
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Dict, Any

import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax


console = Console()


class N8nWorkflowTester:
    """Tester für n8n Arbeitsvorbereiter-Workflow"""

    def __init__(self, n8n_url: str = "http://localhost:5678", django_url: str = None):
        self.n8n_url = n8n_url
        self.django_url = django_url or "http://192.168.178.30:8025"
        self.api_key = "test-key-123"  # Für Tests

    def test_webhook_url(self) -> str:
        """Gibt die Test-Webhook URL zurück"""
        return f"{self.n8n_url}/webhook-test/precheck-submitted"

    def production_webhook_url(self) -> str:
        """Gibt die Production-Webhook URL zurück"""
        return f"{self.n8n_url}/webhook/precheck-submitted"

    def send_webhook(self, precheck_id: int, test_mode: bool = True, production: bool = False) -> Dict[str, Any]:
        """
        Sendet Webhook an n8n

        Args:
            precheck_id: ID des Prechecks
            test_mode: Test-Mode Flag für Django
            production: Wenn True, nutze Production-Webhook (Workflow muss aktiv sein)

        Returns:
            Response-Dict von n8n
        """
        webhook_url = self.production_webhook_url() if production else self.test_webhook_url()

        payload = {
            "event": "precheck_submitted",
            "precheck_id": precheck_id,
            "test_mode": test_mode,
            "api_base_url": self.django_url,
            "api_endpoints": {
                "precheck_data": f"/api/integrations/precheck/{precheck_id}/",
                "pricing_data": "/api/integrations/pricing/"
            },
            "metadata": {
                "customer_email": f"test-{precheck_id}@example.com",
                "has_customer": True,
                "has_site": True,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }

        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }

        console.print(f"\n[bold cyan]📤 Sende Webhook an n8n...[/bold cyan]")
        console.print(f"URL: {webhook_url}")
        console.print(f"Precheck-ID: {precheck_id}")
        console.print(f"Mode: {'Production' if production else 'Test'}")

        try:
            response = requests.post(
                webhook_url,
                json=payload,
                headers=headers,
                timeout=60  # Agent kann 10-20s brauchen
            )

            console.print(f"\n[bold]Status Code:[/bold] {response.status_code}")

            if response.status_code == 200:
                console.print("[bold green]✅ Webhook erfolgreich gesendet![/bold green]")
                return response.json()
            else:
                console.print(f"[bold red]❌ Fehler: {response.status_code}[/bold red]")
                console.print(f"Response: {response.text}")
                return {"error": response.text, "status_code": response.status_code}

        except requests.exceptions.ConnectionError:
            console.print(f"[bold red]❌ Verbindungsfehler![/bold red]")
            console.print(f"Ist n8n erreichbar unter {self.n8n_url}?")
            return {"error": "Connection failed"}
        except requests.exceptions.Timeout:
            console.print(f"[bold red]❌ Timeout! (>60s)[/bold red]")
            console.print("Workflow braucht zu lange. Check n8n Executions!")
            return {"error": "Timeout"}
        except Exception as e:
            console.print(f"[bold red]❌ Fehler: {e}[/bold red]")
            return {"error": str(e)}

    def display_response(self, response: Dict[str, Any]):
        """Zeigt n8n Response übersichtlich an"""

        if "error" in response:
            console.print(Panel(
                f"[bold red]Fehler:[/bold red] {response['error']}",
                title="❌ n8n Response",
                border_style="red"
            ))
            return

        # Erfolgreiche Response
        table = Table(title="✅ n8n Workflow Response", show_header=True, header_style="bold cyan")
        table.add_column("Feld", style="cyan", no_wrap=True)
        table.add_column("Wert", style="green")

        table.add_row("Success", "✅ " + str(response.get("success", False)))
        table.add_row("Precheck ID", str(response.get("precheck_id", "N/A")))
        table.add_row("Overall Status", response.get("overall_status", "N/A"))
        table.add_row("Plausibility Score", f"{response.get('plausibility_score', 0)}%")
        table.add_row("Site Visit Required", "✅ Ja" if response.get("requires_site_visit") else "❌ Nein")
        table.add_row("Effort Hours", f"{response.get('estimated_effort_hours', 0)}h")
        table.add_row("Recommendations", str(response.get("recommendations_count", 0)))
        table.add_row("Workflow Execution", response.get("workflow_execution_id", "N/A")[:16] + "...")

        console.print(table)

        # Nachricht
        message = response.get("message", "")
        if message:
            console.print(Panel(
                message,
                title="📋 Nachricht",
                border_style="green"
            ))

    def check_django_api(self, precheck_id: int) -> bool:
        """
        Prüft, ob Django API erreichbar ist und Precheck existiert

        Returns:
            True wenn erreichbar, False sonst
        """
        url = f"{self.django_url}/api/integrations/precheck/{precheck_id}/"

        console.print(f"\n[bold cyan]🔍 Prüfe Django API...[/bold cyan]")
        console.print(f"URL: {url}")

        try:
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                console.print("[bold green]✅ Django API erreichbar![/bold green]")
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    precheck = data[0]
                    console.print(f"Kunde: {precheck.get('customer', {}).get('name', 'N/A')}")
                    console.print(f"PV-Leistung: {precheck.get('project', {}).get('desired_power_kw', 0)} kW")
                return True
            else:
                console.print(f"[bold red]❌ Fehler: {response.status_code}[/bold red]")
                console.print(f"Response: {response.text[:200]}")
                return False

        except requests.exceptions.ConnectionError:
            console.print(f"[bold red]❌ Django nicht erreichbar![/bold red]")
            console.print(f"Läuft Django Server auf {self.django_url}?")
            return False
        except Exception as e:
            console.print(f"[bold red]❌ Fehler: {e}[/bold red]")
            return False

    def list_prechecks(self):
        """Listet verfügbare Prechecks auf"""
        # Versuche mehrere IDs
        console.print("\n[bold cyan]📋 Suche verfügbare Prechecks...[/bold cyan]")

        found_prechecks = []
        for precheck_id in range(1, 101):  # Teste IDs 1-100
            try:
                url = f"{self.django_url}/api/integrations/precheck/{precheck_id}/"
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        found_prechecks.append((precheck_id, data[0]))
            except:
                continue

        if not found_prechecks:
            console.print("[bold yellow]⚠️ Keine Prechecks gefunden[/bold yellow]")
            console.print(f"Django Server läuft auf {self.django_url}?")
            return

        # Tabelle erstellen
        table = Table(title="Verfügbare Prechecks", show_header=True, header_style="bold cyan")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Kunde", style="white")
        table.add_column("PV-Leistung", style="green")
        table.add_column("Speicher", style="green")
        table.add_column("Wallbox", style="green")
        table.add_column("Status", style="yellow")

        for precheck_id, precheck in found_prechecks:
            customer = precheck.get('customer', {})
            project = precheck.get('project', {})
            metadata = precheck.get('metadata', {})

            table.add_row(
                str(precheck_id),
                customer.get('name', 'N/A')[:30],
                f"{project.get('desired_power_kw', 0)} kW",
                f"{project.get('storage_kwh', 0)} kWh" if project.get('has_storage') else "-",
                "✅" if project.get('has_wallbox') else "❌",
                metadata.get('quote_status', 'N/A')
            )

        console.print(table)
        console.print(f"\n[bold green]✅ {len(found_prechecks)} Prechecks gefunden[/bold green]")
        console.print(f"\nTest mit: [bold cyan]python test_n8n_workflow.py --precheck-id <ID>[/bold cyan]")


def main():
    parser = argparse.ArgumentParser(
        description="Test n8n Arbeitsvorbereiter-Workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Test mit Precheck ID 64
  python test_n8n_workflow.py --precheck-id 64

  # Production Webhook (Workflow muss aktiv sein!)
  python test_n8n_workflow.py --precheck-id 64 --production

  # Verfügbare Prechecks auflisten
  python test_n8n_workflow.py --list-prechecks

  # Andere n8n URL
  python test_n8n_workflow.py --precheck-id 64 --n8n-url http://192.168.1.100:5678
        """
    )

    parser.add_argument(
        "--precheck-id",
        type=int,
        help="ID des Prechecks zum Testen"
    )
    parser.add_argument(
        "--production",
        action="store_true",
        help="Nutze Production-Webhook (Workflow muss aktiv sein!)"
    )
    parser.add_argument(
        "--n8n-url",
        default="http://localhost:5678",
        help="n8n Server URL (default: http://localhost:5678)"
    )
    parser.add_argument(
        "--django-url",
        default="http://192.168.178.30:8025",
        help="Django Server URL (default: http://192.168.178.30:8025)"
    )
    parser.add_argument(
        "--list-prechecks",
        action="store_true",
        help="Listet alle verfügbaren Prechecks auf"
    )

    args = parser.parse_args()

    # ASCII Art Header
    console.print("""
[bold cyan]
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   n8n Workflow Tester: Arbeitsvorbereiter Agent         ║
║   PV-Service Django → n8n Integration                    ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
[/bold cyan]
    """)

    # Tester initialisieren
    tester = N8nWorkflowTester(n8n_url=args.n8n_url, django_url=args.django_url)

    # List Prechecks
    if args.list_prechecks:
        tester.list_prechecks()
        sys.exit(0)

    # Precheck ID erforderlich
    if not args.precheck_id:
        console.print("[bold red]❌ Fehler: --precheck-id erforderlich[/bold red]")
        console.print("Nutze --help für weitere Informationen")
        sys.exit(1)

    # Django API prüfen
    if not tester.check_django_api(args.precheck_id):
        console.print("\n[bold yellow]⚠️ Django API nicht erreichbar oder Precheck existiert nicht[/bold yellow]")
        console.print("n8n wird trotzdem getestet, aber möglicherweise mit Fehler...")

    # Webhook senden
    response = tester.send_webhook(
        precheck_id=args.precheck_id,
        test_mode=True,
        production=args.production
    )

    # Response anzeigen
    tester.display_response(response)

    # Erfolgsstatus
    if response.get("success"):
        console.print("\n[bold green]✅ Test erfolgreich abgeschlossen![/bold green]")

        if not args.production:
            console.print("\n[bold yellow]💡 Tipp:[/bold yellow]")
            console.print("Für Production-Test nutze: [bold cyan]--production[/bold cyan]")
            console.print("(Workflow muss in n8n aktiviert sein!)")

        sys.exit(0)
    else:
        console.print("\n[bold red]❌ Test fehlgeschlagen[/bold red]")
        console.print("\n[bold yellow]Troubleshooting:[/bold yellow]")
        console.print("1. n8n läuft und Workflow ist aktiv (bei --production)?")
        console.print("2. Django API erreichbar und Precheck existiert?")
        console.print("3. OpenAI Credentials korrekt konfiguriert?")
        console.print("4. Check n8n Executions für Details")
        sys.exit(1)


if __name__ == "__main__":
    main()
