# Web-Pot 🛡️

Portal de **Suport Intern** del Consell Comarcal del Tarragonès.

Aplicació web lleugera per a la gestió de suport intern, en fase de proves mentre es completa la migració de l'Active Directory.

## Funcionalitats

- 🔐 Inici de sessió amb usuari, contrasenya i token MFA
- 👤 Autocreació d'usuaris (registre)
- 🏠 Pàgina de benvinguda amb accés a futures funcionalitats
- 🐳 Preparada per Docker

## Requisits

- Docker i Docker Compose

## Desplegament ràpid

```bash
docker compose up -d --build
```

L'aplicació estarà disponible a **http://localhost:5000**

## Desenvolupament local

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
# venv\Scripts\activate    # Windows
pip install -r requirements.txt
python run.py
```

## Estructura

```
Web-Pot/
├── app/
│   ├── __init__.py          # Factory de l'aplicació
│   ├── models.py            # Model d'usuari (SQLite)
│   ├── routes.py            # Rutes (login, register, welcome)
│   ├── templates/           # Plantilles HTML
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── register.html
│   │   └── welcome.html
│   └── static/
│       └── style.css
├── config.py
├── run.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .gitignore
```

## Nota

> Aquesta plataforma està en fase de proves. El token MFA accepta qualsevol valor mentre no es tingui l'AD configurat.
