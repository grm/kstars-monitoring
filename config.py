import os
from dotenv import load_dotenv
from typing import Optional

# Charger les variables d'environnement
load_dotenv()

class Config:
    """Configuration de l'application de surveillance des logs EKOS"""
    
    def __init__(self):
        self.discord_webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        self.ekos_logs_directory = os.getenv('EKOS_LOGS_DIRECTORY')
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.rate_limit_delay = float(os.getenv('RATE_LIMIT_DELAY', '1.0'))
        self.batch_size = int(os.getenv('BATCH_SIZE', '10'))
        self.batch_timeout = float(os.getenv('BATCH_TIMEOUT', '30.0'))
        self.file_check_interval = int(os.getenv('FILE_CHECK_INTERVAL', '60'))
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
    
    def validate(self) -> bool:
        """Valider la configuration"""
        if not self.discord_webhook_url:
            print("❌ DISCORD_WEBHOOK_URL n'est pas configuré")
            return False
        
        if not self.ekos_logs_directory:
            print("❌ EKOS_LOGS_DIRECTORY n'est pas configuré")
            return False
        
        if not os.path.exists(self.ekos_logs_directory):
            print(f"❌ Le répertoire {self.ekos_logs_directory} n'existe pas")
            return False
        
        print("✅ Configuration validée")
        return True
    
    def __str__(self) -> str:
        return f"""
Configuration:
- Discord Webhook: {'✅ Configuré' if self.discord_webhook_url else '❌ Non configuré'}
- Répertoire logs EKOS: {self.ekos_logs_directory}
- Niveau de log: {self.log_level}
- Délai rate limit: {self.rate_limit_delay}s
- Taille batch: {self.batch_size}
- Timeout batch: {self.batch_timeout}s
- Intervalle vérification fichiers: {self.file_check_interval}s
- Max tentatives: {self.max_retries}
""" 