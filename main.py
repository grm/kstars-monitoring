#!/usr/bin/env python3
"""
EKOS Log Monitor - Surveillance des logs EKOS vers Discord
"""

import sys
import signal
import logging
import time
from config import Config
from discord_sender import DiscordSender
from log_monitor import LogMonitor

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ekos_monitor.log')
    ]
)

logger = logging.getLogger(__name__)

class EKOSMonitor:
    """Application principale de surveillance des logs EKOS"""
    
    def __init__(self):
        self.config = Config()
        self.discord_sender = None
        self.log_monitor = None
        self.running = False
        
        # Configuration des signaux pour l'arrêt propre
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Gestionnaire de signaux pour l'arrêt propre"""
        logger.info(f"Signal {signum} reçu, arrêt en cours...")
        self.stop()
    
    def initialize(self) -> bool:
        """Initialiser l'application"""
        logger.info("🚀 Initialisation de EKOS Log Monitor")
        
        # Valider la configuration
        if not self.config.validate():
            logger.error("❌ Configuration invalide")
            return False
        
        # Afficher la configuration
        logger.info(self.config)
        
        # Initialiser le sender Discord
        self.discord_sender = DiscordSender(
            webhook_url=self.config.discord_webhook_url,
            rate_limit_delay=self.config.rate_limit_delay,
            max_retries=self.config.max_retries
        )
        
        # Initialiser le moniteur de logs
        self.log_monitor = LogMonitor(
            logs_directory=self.config.ekos_logs_directory,
            discord_sender=self.discord_sender,
            batch_size=self.config.batch_size,
            batch_timeout=self.config.batch_timeout,
            file_check_interval=self.config.file_check_interval
        )
        
        logger.info("✅ Initialisation terminée")
        return True
    
    def start(self):
        """Démarrer l'application"""
        if not self.initialize():
            logger.error("❌ Échec de l'initialisation")
            sys.exit(1)
        
        try:
            logger.info("🔄 Démarrage de la surveillance...")
            self.log_monitor.start()
            self.running = True
            
            logger.info("✅ Surveillance active - Appuyez sur Ctrl+C pour arrêter")
            
            # Boucle principale
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("⚠️ Interruption clavier détectée")
        except Exception as e:
            logger.error(f"❌ Erreur inattendue: {e}")
            if self.discord_sender:
                self.discord_sender.send_error_message(str(e))
        finally:
            self.stop()
    
    def stop(self):
        """Arrêter l'application"""
        if not self.running:
            return
        
        logger.info("🛑 Arrêt de l'application...")
        self.running = False
        
        if self.log_monitor:
            self.log_monitor.stop()
        
        logger.info("✅ Application arrêtée")

def main():
    """Point d'entrée principal"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    EKOS Log Monitor                          ║
║              Surveillance des logs vers Discord              ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    monitor = EKOSMonitor()
    monitor.start()

if __name__ == "__main__":
    main() 