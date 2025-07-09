import os
import time
import logging
import threading
from typing import Optional, List
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from discord_sender import DiscordSender

logger = logging.getLogger(__name__)

class LogFileHandler(FileSystemEventHandler):
    """Gestionnaire d'événements pour les fichiers de logs"""
    
    def __init__(self, discord_sender: DiscordSender, batch_size: int = 10, batch_timeout: float = 30.0):
        self.discord_sender = discord_sender
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.pending_logs = []
        self.current_file = None
        self.file_position = 0
        self.last_log_time = 0
        self.batch_timer = None
        self.timer_lock = threading.Lock()
        self.running = True
        
        # Démarrer le thread de surveillance du timeout
        self.timeout_thread = threading.Thread(target=self._timeout_monitor, daemon=True)
        self.timeout_thread.start()
    
    def _timeout_monitor(self):
        """Thread de surveillance du timeout de batch"""
        while self.running:
            try:
                with self.timer_lock:
                    if self.pending_logs and self.last_log_time > 0:
                        time_since_last_log = time.time() - self.last_log_time
                        if time_since_last_log >= self.batch_timeout:
                            logger.debug(f"Timeout de batch atteint ({self.batch_timeout}s), envoi des {len(self.pending_logs)} logs")
                            self._send_pending_logs()
                            self.last_log_time = 0  # Reset timer
                
                time.sleep(1)  # Vérifier toutes les secondes
                
            except Exception as e:
                logger.error(f"Erreur dans le thread de timeout: {e}")
                time.sleep(5)  # Attendre un peu en cas d'erreur
    
    def _reset_batch_timer(self):
        """Réinitialiser le timer de batch"""
        with self.timer_lock:
            self.last_log_time = time.time()
    
    def _add_log_to_batch(self, log_line: str):
        """Ajouter un log au batch et gérer l'envoi"""
        self.pending_logs.append(log_line)
        self._reset_batch_timer()  # Réinitialiser le timer
        
        # Envoyer si le batch est plein
        if len(self.pending_logs) >= self.batch_size:
            logger.debug(f"Batch plein ({self.batch_size} logs), envoi immédiat")
            self._send_pending_logs()
            self.last_log_time = 0  # Reset timer après envoi
    
    def on_created(self, event):
        """Appelé quand un nouveau fichier est créé"""
        if not event.is_directory and event.src_path.endswith('.log'):
            logger.info(f"Nouveau fichier de log détecté: {event.src_path}")
            self._switch_to_new_file(event.src_path)
    
    def on_modified(self, event):
        """Appelé quand un fichier est modifié"""
        if not event.is_directory and event.src_path.endswith('.log'):
            if event.src_path == self.current_file:
                self._read_new_lines(event.src_path)
    
    def _switch_to_new_file(self, file_path: str):
        """Basculer vers un nouveau fichier de log"""
        self.current_file = file_path
        self.file_position = 0
        logger.info(f"Surveillance du fichier: {file_path}")
        
        # Lire les dernières lignes du fichier pour éviter d'envoyer l'historique
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                self.file_position = len(lines)
                logger.info(f"Position initiale: {self.file_position} lignes")
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du fichier {file_path}: {e}")
    
    def _read_new_lines(self, file_path: str):
        """Lire les nouvelles lignes ajoutées au fichier"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
                if len(lines) > self.file_position:
                    new_lines = lines[self.file_position:]
                    self.file_position = len(lines)
                    
                    # Traiter les nouvelles lignes
                    for line in new_lines:
                        line = line.strip()
                        if line:  # Ignorer les lignes vides
                            self._add_log_to_batch(line)
                        
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du fichier {file_path}: {e}")
    
    def _send_pending_logs(self):
        """Envoyer les logs en attente vers Discord"""
        if self.pending_logs:
            logger.info(f"Envoi de {len(self.pending_logs)} logs vers Discord")
            if self.discord_sender.send_logs(self.pending_logs):
                self.pending_logs = []
            else:
                logger.error("Échec de l'envoi des logs vers Discord")
    
    def stop(self):
        """Arrêter le handler et envoyer les logs restants"""
        self.running = False
        if self.pending_logs:
            logger.info(f"Arrêt - envoi des {len(self.pending_logs)} logs restants")
            self._send_pending_logs()

class LogMonitor:
    """Moniteur principal pour surveiller les logs EKOS"""
    
    def __init__(self, logs_directory: str, discord_sender: DiscordSender, batch_size: int = 10, batch_timeout: float = 30.0):
        self.logs_directory = logs_directory
        self.discord_sender = discord_sender
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.observer = Observer()
        self.handler = LogFileHandler(discord_sender, batch_size, batch_timeout)
        self.running = False
    
    def _find_latest_log_file(self) -> Optional[str]:
        """Trouver le fichier de log le plus récent"""
        try:
            log_files = []
            for file in os.listdir(self.logs_directory):
                if file.endswith('.log'):
                    file_path = os.path.join(self.logs_directory, file)
                    if os.path.isfile(file_path):
                        log_files.append(file_path)
            
            if not log_files:
                logger.warning("Aucun fichier de log trouvé dans le répertoire")
                return None
            
            # Trier par date de modification (le plus récent en premier)
            latest_file = max(log_files, key=os.path.getmtime)
            logger.info(f"Fichier de log le plus récent: {latest_file}")
            return latest_file
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche du fichier de log le plus récent: {e}")
            return None
    
    def start(self):
        """Démarrer la surveillance des logs"""
        if self.running:
            logger.warning("La surveillance est déjà en cours")
            return
        
        # Trouver le fichier de log le plus récent
        latest_file = self._find_latest_log_file()
        if latest_file:
            self.handler._switch_to_new_file(latest_file)
        
        # Configurer l'observateur
        self.observer.schedule(self.handler, self.logs_directory, recursive=False)
        self.observer.start()
        self.running = True
        
        # Envoyer le message de démarrage
        self.discord_sender.send_startup_message()
        
        logger.info(f"Surveillance démarrée pour le répertoire: {self.logs_directory}")
    
    def stop(self):
        """Arrêter la surveillance des logs"""
        if not self.running:
            return
        
        self.observer.stop()
        self.observer.join()
        self.running = False
        
        # Arrêter le handler et envoyer les logs restants
        self.handler.stop()
        
        logger.info("Surveillance arrêtée")
    
    def is_running(self) -> bool:
        """Vérifier si la surveillance est en cours"""
        return self.running 