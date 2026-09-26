import os
import re
import datetime
import requests
from typing import Optional

class VaultExporter:
    """Exports generated dossiers to local project storage and Obsidian Vault."""

    def __init__(self, vault_path: Optional[str] = None):
        self.vault_path = vault_path or os.getenv("VAULT_SCANS_PATH", "D:/Start/Market_Intelligence_Vault/06_Market_Scans")
        self.local_output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "output")
        
        # Ensure directories exist
        os.makedirs(self.local_output_path, exist_ok=True)
        if self.vault_path:
            os.makedirs(self.vault_path, exist_ok=True)

    def _sanitize_filename(self, text: str) -> str:
        clean = re.sub(r'[\\/*?:"<>| ]', '_', text.strip())
        return re.sub(r'_+', '_', clean)[:50]

    def export(self, topic: str, markdown_content: str) -> str:
        """Saves report to both output directories."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
        safe_topic = self._sanitize_filename(topic)
        filename = f"{timestamp}_{safe_topic}.md"

        # 1. Save to local project output
        local_file = os.path.join(self.local_output_path, filename)
        with open(local_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        # 2. Save directly to Obsidian Vault
        vault_file = None
        if self.vault_path and os.path.exists(self.vault_path):
            vault_file = os.path.join(self.vault_path, filename)
            with open(vault_file, "w", encoding="utf-8") as f:
                f.write(markdown_content)

        # 3. Trigger Webhook alert if configured
        self._notify_webhook(topic, local_file)

        return vault_file or local_file

    def _notify_webhook(self, topic: str, file_path: str):
        discord_url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
        if discord_url:
            try:
                requests.post(
                    discord_url,
                    json={
                        "content": f"🎯 **New Market Intelligence Dossier Generated!**\n**Topic:** `{topic}`\nSaved to Obsidian Vault & Project Output."
                    },
                    timeout=5
                )
            except Exception:
                pass
