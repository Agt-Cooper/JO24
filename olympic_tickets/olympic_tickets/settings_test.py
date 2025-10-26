"""
Settings spécifiques aux tests — utilisent une base MySQL dédiée
(test_jo_db + user jotest_db) pour ne pas toucher à la base de dev.
"""

from .settings import *  # importe tous les réglages normaux
import os
from dotenv import load_dotenv

#cahrge le fichier .env.test
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env.test"))

# ---------------------------------------------------------
# Base de données de TEST (ne touche pas jo_db)
# ---------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "test_jo_db",          # base utilisée *uniquement pendant les tests*
        "USER": os.getenv("DB_TEST_USER"),           # user dédié aux tests
        "PASSWORD": os.getenv("DB_TEST_PASSWORD"),  # À changer / replacer via .env si besoin
        "HOST": "127.0.0.1",
        "PORT": "3306",
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        "TEST": {
            "NAME": os.getenv("DB_TEST_NAME","test_jo_db"), #ca force le nom pour le test
        },
    }
}

# ---------------------------------------------------------
# Neutraliser certains effets en test (pas d'e-mails réels)
# ---------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
# (Les emails envoyés pendant les tests sont stockés en mémoire: mail.outbox)

# ---------------------------------------------------------
# Optionnel : accélérer les tests (pas de password hashing lent)
# ---------------------------------------------------------
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# ---------------------------------------------------------
# Optionnel : désactiver le CSRF en test si on poste des forms
# (généralement pas obligatoire)
# ---------------------------------------------------------
# CSRF_COOKIE_SECURE = False
# CSRF_USE_SESSIONS = False
