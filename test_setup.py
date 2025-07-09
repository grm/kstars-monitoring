#!/usr/bin/env python3
"""
Script de test pour vérifier la configuration et les dépendances
"""

import sys
import os
import importlib
from config import Config

def test_imports():
    """Tester l'importation des modules requis"""
    print("🔍 Test des imports...")
    
    required_modules = [
        'watchdog',
        'requests', 
        'dotenv',
        'schedule'
    ]
    
    failed_imports = []
    
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n❌ Modules manquants: {', '.join(failed_imports)}")
        print("💡 Installez les dépendances avec: pipenv install")
        return False
    
    print("✅ Tous les imports sont OK")
    return True

def test_config():
    """Tester la configuration"""
    print("\n🔍 Test de la configuration...")
    
    config = Config()
    
    # Vérifier les variables obligatoires
    if not config.discord_webhook_url:
        print("  ❌ DISCORD_WEBHOOK_URL non configuré")
        print("    💡 Ajoutez DISCORD_WEBHOOK_URL dans votre fichier .env")
        return False
    else:
        print("  ✅ DISCORD_WEBHOOK_URL configuré")
    
    if not config.ekos_logs_directory:
        print("  ❌ EKOS_LOGS_DIRECTORY non configuré")
        print("    💡 Ajoutez EKOS_LOGS_DIRECTORY dans votre fichier .env")
        return False
    else:
        print("  ✅ EKOS_LOGS_DIRECTORY configuré")
    
    # Vérifier que le répertoire existe
    if not os.path.exists(config.ekos_logs_directory):
        print(f"  ❌ Le répertoire {config.ekos_logs_directory} n'existe pas")
        return False
    else:
        print(f"  ✅ Le répertoire {config.ekos_logs_directory} existe")
    
    # Vérifier qu'il y a des fichiers .log
    log_files = [f for f in os.listdir(config.ekos_logs_directory) if f.endswith('.log')]
    if not log_files:
        print(f"  ⚠️  Aucun fichier .log trouvé dans {config.ekos_logs_directory}")
    else:
        print(f"  ✅ {len(log_files)} fichier(s) .log trouvé(s)")
    
    print("✅ Configuration OK")
    return True

def test_discord_webhook():
    """Tester la connexion Discord"""
    print("\n🔍 Test de la connexion Discord...")
    
    config = Config()
    
    if not config.discord_webhook_url:
        print("  ❌ Impossible de tester: DISCORD_WEBHOOK_URL non configuré")
        return False
    
    try:
        import requests
        
        # Test simple du webhook
        payload = {
            "content": "🧪 Test de connexion - EKOS Log Monitor",
            "username": "EKOS Log Monitor Test"
        }
        
        response = requests.post(
            config.discord_webhook_url,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 204:
            print("  ✅ Webhook Discord fonctionnel")
            return True
        else:
            print(f"  ❌ Erreur webhook: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"  ❌ Erreur de connexion: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    Test de Configuration                      ║
║                    EKOS Log Monitor                          ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    all_tests_passed = True
    
    # Test des imports
    if not test_imports():
        all_tests_passed = False
    
    # Test de la configuration
    if not test_config():
        all_tests_passed = False
    
    # Test Discord (optionnel)
    if all_tests_passed:
        test_discord_webhook()
    
    print("\n" + "="*60)
    if all_tests_passed:
        print("🎉 Tous les tests de base sont passés!")
        print("💡 Vous pouvez maintenant lancer l'application avec: python main.py")
    else:
        print("❌ Certains tests ont échoué")
        print("💡 Corrigez les problèmes avant de lancer l'application")
    print("="*60)

if __name__ == "__main__":
    main() 