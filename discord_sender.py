import requests
import time
import logging
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DiscordSender:
    """Classe pour envoyer des messages vers Discord avec gestion du rate limiting"""
    
    def __init__(self, webhook_url: str, rate_limit_delay: float = 1.0, max_retries: int = 3):
        self.webhook_url = webhook_url
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.last_send_time = 0
    
    def _wait_for_rate_limit(self):
        """Attendre le délai nécessaire pour respecter le rate limiting"""
        current_time = time.time()
        time_since_last_send = current_time - self.last_send_time
        
        if time_since_last_send < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_send
            logger.debug(f"Attente de {sleep_time:.2f}s pour respecter le rate limiting")
            time.sleep(sleep_time)
    
    def _send_message(self, content: str, retry_count: int = 0) -> bool:
        """Envoyer un message vers Discord avec gestion des erreurs"""
        try:
            self._wait_for_rate_limit()
            
            payload = {
                "content": content,
                "username": "EKOS Log Monitor",
                "avatar_url": "https://www.indilib.org/images/ekos-logo.png"
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            self.last_send_time = time.time()
            
            if response.status_code == 204:
                logger.debug("Message envoyé avec succès")
                return True
            elif response.status_code == 429:
                # Rate limit atteint
                retry_after = int(response.headers.get('Retry-After', 5))
                logger.warning(f"Rate limit atteint, attente de {retry_after}s")
                time.sleep(retry_after)
                return self._send_message(content, retry_count)
            else:
                logger.error(f"Erreur lors de l'envoi: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur réseau: {e}")
            if retry_count < self.max_retries:
                logger.info(f"Tentative {retry_count + 1}/{self.max_retries}")
                time.sleep(2 ** retry_count)  # Backoff exponentiel
                return self._send_message(content, retry_count + 1)
            return False
    
    def send_logs(self, logs: List[str]) -> bool:
        """Envoyer une liste de logs vers Discord"""
        if not logs:
            return True
        
        # Préparer le message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content = f"**📋 Nouveaux logs EKOS - {timestamp}**\n"
        
        # Ajouter les logs (limiter à 1900 caractères pour éviter les limites Discord)
        for log in logs:
            if len(content + log + "\n") > 1900:
                content += "...\n*[Message tronqué]*"
                break
            content += f"```{log}```\n"
        
        return self._send_message(content)
    
    def send_startup_message(self) -> bool:
        """Envoyer un message de démarrage"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content = f"🚀 **EKOS Log Monitor démarré**\n*{timestamp}*\n\nLa surveillance des logs EKOS est maintenant active."
        return self._send_message(content)
    
    def send_error_message(self, error: str) -> bool:
        """Envoyer un message d'erreur"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content = f"❌ **Erreur EKOS Log Monitor**\n*{timestamp}*\n\n```{error}```"
        return self._send_message(content) 