# EKOS Log Monitor

Application Python pour surveiller les logs d'EKOS et les envoyer vers un canal Discord via webhook.

## 🚀 Fonctionnalités

- **Surveillance automatique** : Détecte le fichier de log le plus récent dans un répertoire et ses sous-répertoires
- **Recherche récursive** : Parcourt tous les sous-répertoires pour trouver les logs EKOS
- **Vérification périodique** : Vérifie régulièrement s'il y a un nouveau fichier de log plus récent
- **Envoi en temps réel** : Envoie les nouvelles lignes de logs vers Discord
- **Rate limiting intelligent** : Évite les limitations Discord avec gestion des délais
- **Batching avec timeout** : Envoi par batch avec délai configurable pour la réactivité
- **Gestion d'erreurs robuste** : Retry automatique et backoff exponentiel
- **Configuration flexible** : Variables d'environnement pour personnalisation
- **Arrêt propre** : Gestion des signaux pour un arrêt sécurisé

## 📋 Prérequis

- Python 3.9+
- pipenv
- Accès au répertoire des logs EKOS
- Webhook Discord configuré

## 🛠️ Installation

1. **Cloner ou télécharger le projet**
   ```bash
   cd /path/to/project
   ```

2. **Installer les dépendances avec pipenv**
   ```bash
   pipenv install
   ```

3. **Configurer l'environnement**
   ```bash
   cp env.example .env
   # Éditer le fichier .env avec vos paramètres
   ```

## ⚙️ Configuration

Créez un fichier `.env` avec les paramètres suivants :

```env
# Configuration Discord (obligatoire)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_url

# Configuration des logs EKOS (obligatoire)
EKOS_LOGS_DIRECTORY=/path/to/ekos/logs/directory

# Configuration de l'application (optionnel)
LOG_LEVEL=INFO
RATE_LIMIT_DELAY=1.0
BATCH_SIZE=10
BATCH_TIMEOUT=30.0
FILE_CHECK_INTERVAL=60
MAX_RETRIES=3
```

### Paramètres de configuration

| Paramètre | Description | Défaut |
|-----------|-------------|--------|
| `DISCORD_WEBHOOK_URL` | URL du webhook Discord | - |
| `EKOS_LOGS_DIRECTORY` | Répertoire contenant les logs EKOS | - |
| `LOG_LEVEL` | Niveau de log (DEBUG, INFO, WARNING, ERROR) | INFO |
| `RATE_LIMIT_DELAY` | Délai entre les envois (secondes) | 1.0 |
| `BATCH_SIZE` | Nombre de logs par message | 10 |
| `BATCH_TIMEOUT` | Délai max avant envoi forcé (secondes) | 30.0 |
| `FILE_CHECK_INTERVAL` | Intervalle de vérification des fichiers (secondes) | 60 |
| `MAX_RETRIES` | Nombre max de tentatives en cas d'échec | 3 |

## 🚀 Utilisation

### Démarrage de l'application

```bash
# Activer l'environnement pipenv
pipenv shell

# Lancer l'application
python main.py
```

### Arrêt de l'application

- Appuyez sur `Ctrl+C` pour un arrêt propre
- L'application enverra les logs restants avant de s'arrêter

## 📊 Fonctionnement

1. **Recherche récursive** : L'application scanne récursivement le répertoire et identifie le fichier `.log` le plus récent
2. **Surveillance en temps réel** : Utilise `watchdog` pour détecter les modifications du fichier
3. **Vérification périodique** : Vérifie régulièrement s'il y a un nouveau fichier de log plus récent
4. **Collecte des nouvelles lignes** : Lit uniquement les nouvelles lignes ajoutées depuis le démarrage
5. **Envoi par batch avec timeout** : Accumule les logs et les envoie par groupes ou après un délai configurable
6. **Rate limiting** : Respecte les limitations Discord avec des délais configurables

## 🔧 Stratégie de Batching et Rate Limiting

L'application implémente une stratégie hybride pour optimiser les performances :

### Batching intelligent
- **Envoi immédiat** : Si le batch atteint `BATCH_SIZE` logs
- **Envoi différé** : Si `BATCH_TIMEOUT` secondes se sont écoulées depuis le dernier log
- **Timer réinitialisé** : À chaque nouveau log reçu

### Rate Limiting
- **Délai configurable** entre les envois (`RATE_LIMIT_DELAY`)
- **Détection automatique** des erreurs 429 (rate limit)
- **Backoff exponentiel** en cas d'échec
- **Retry automatique** avec nombre de tentatives configurable

### Exemple de comportement
- `BATCH_SIZE=10`, `BATCH_TIMEOUT=30s`
- Si 5 logs arrivent rapidement → envoi après 30s
- Si 10 logs arrivent rapidement → envoi immédiat
- Si 3 logs arrivent, puis 2 autres 20s plus tard → envoi après 30s supplémentaires

## 🔍 Recherche récursive et vérification périodique

L'application gère intelligemment la structure de répertoires d'EKOS :

### Recherche récursive
- **Parcours complet** : Explore tous les sous-répertoires
- **Détection automatique** : Trouve le fichier `.log` le plus récent
- **Gestion des dates** : Fonctionne avec la structure par jour d'EKOS

### Vérification périodique
- **Intervalle configurable** : `FILE_CHECK_INTERVAL` (défaut: 60s)
- **Détection des redémarrages** : Détecte quand EKOS crée un nouveau répertoire
- **Basculement automatique** : Passe automatiquement au nouveau fichier de log

### Exemple de structure supportée
```
/ekos/logs/
├── 2024-01-15/
│   ├── ekos_2024-01-15.log
│   └── ekos_2024-01-15_restart.log
├── 2024-01-16/
│   └── ekos_2024-01-16.log
└── 2024-01-17/
    └── ekos_2024-01-17.log  ← Fichier surveillé
```

## 📝 Logs de l'application

L'application génère ses propres logs dans :
- **Console** : Affichage en temps réel
- **Fichier** : `ekos_monitor.log` dans le répertoire du projet

## 🐛 Dépannage

### Erreurs courantes

1. **Configuration manquante**
   ```
   ❌ DISCORD_WEBHOOK_URL n'est pas configuré
   ```
   → Vérifiez que le fichier `.env` existe et contient l'URL du webhook

2. **Répertoire inexistant**
   ```
   ❌ Le répertoire /path/to/logs n'existe pas
   ```
   → Vérifiez le chemin dans `EKOS_LOGS_DIRECTORY`

3. **Aucun fichier de log**
   ```
   Aucun fichier de log trouvé dans le répertoire et ses sous-répertoires
   ```
   → Vérifiez que le répertoire contient des fichiers `.log`

### Vérification du webhook Discord

Testez votre webhook avec curl :
```bash
curl -H "Content-Type: application/json" \
     -X POST \
     -d '{"content":"Test message"}' \
     https://discord.com/api/webhooks/your_webhook_url
```

## 📁 Structure du projet

```
ekos-log-monitor/
├── main.py              # Point d'entrée principal
├── config.py            # Gestion de la configuration
├── discord_sender.py    # Envoi vers Discord
├── log_monitor.py       # Surveillance des logs
├── Pipfile              # Dépendances pipenv
├── env.example          # Exemple de configuration
├── README.md           # Documentation
└── .env                # Configuration (à créer)
```

## 🤝 Contribution

1. Fork le projet
2. Créez une branche pour votre fonctionnalité
3. Committez vos changements
4. Poussez vers la branche
5. Ouvrez une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## 🆘 Support

Pour toute question ou problème :
1. Vérifiez les logs de l'application
2. Consultez la section dépannage
3. Ouvrez une issue sur GitHub 