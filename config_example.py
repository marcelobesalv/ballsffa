"""
Arquivo de configuração centralizado
"""

# ===== CONFIGURAÇÕES DE SIMULAÇÃO =====

# Física
ARENA_WIDTH = 1000.0
ARENA_HEIGHT = 1000.0
PARTICLE_RADIUS = 10.0
MAX_SPEED = 5.0
FRICTION = 0.98

# Combate
HP_DEFAULT = 100.0
DAMAGE_BASE = 5.0
STRENGTH_MIN = 0.8
STRENGTH_MAX = 1.2

# Performance
GRID_SIZE = 50.0  # Para spatial hashing
MAX_VISIBLE_PARTICLES = 200  # LOD

# ===== CONFIGURAÇÕES DE VÍDEO =====

# Resolução
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920  # Formato vertical (Reels)
VIDEO_FPS = 30

# Durações (em segundos)
INTRO_DURATION = 2
OUTRO_DURATION = 3
MAX_BATTLE_DURATION = 60

# Cores (BGR)
BG_COLOR = (20, 20, 30)
TEXT_COLOR = (255, 255, 255)
HP_BAR_FULL = (0, 255, 100)
HP_BAR_LOW = (255, 50, 50)
HP_BAR_BG = (50, 50, 50)

# ===== CONFIGURAÇÕES DO INSTAGRAM =====

# Limites
MAX_REEL_DURATION = 60  # segundos
MAX_VIDEO_SIZE_MB = 100  # megabytes
RECOMMENDED_BITRATE = '5000k'

# Rate limiting
DOWNLOAD_MAX_WORKERS = 10
DOWNLOAD_TIMEOUT = 10  # segundos

# ===== CONFIGURAÇÕES DE CACHE =====

# Diretórios
ASSETS_DIR = 'assets'
PFPS_DIR = 'assets/pfps'
DATA_DIR = 'data'
OUTPUT_DIR = 'output'

# Arquivos
FOLLOWERS_CACHE = 'data/followers.json'
SESSION_FILE = 'data/session.json'

# ===== TEMPLATES =====

# Template de legenda padrão
CAPTION_TEMPLATE = """Dia:{day} — fazendo meus seguidores lutarem! 🏆
Vencedor: @{winner}

Se não quiser aparecer, basta deixar de seguir."""

# Texto de consentimento
CONSENT_TEXT = """AVISO: nesta conta estamos fazendo um vídeo-jogo experimental 
onde os seguidores podem aparecer como personagens (usando 
username e foto de perfil).

Ao seguir esta conta, você concorda que seu username e foto 
de perfil poderão ser usados neste projeto e exibidos em 
vídeos públicos.

Se não concordar, basta deixar de seguir. Obrigado!"""

# ===== CONFIGURAÇÕES DE DEBUG =====

DEBUG = False
VERBOSE = True
SHOW_PROGRESS = True

# ===== PRESETS =====

PRESETS = {
    'quick': {
        'max_participants': 500,
        'duration': 20,
        'hp_default': 50,
        'damage_base': 10
    },
    'normal': {
        'max_participants': 5000,
        'duration': 60,
        'hp_default': 100,
        'damage_base': 5
    },
    'epic': {
        'max_participants': 50000,
        'duration': 120,
        'hp_default': 200,
        'damage_base': 3
    },
    'ultra': {
        'max_participants': 100000,
        'duration': 180,
        'hp_default': 300,
        'damage_base': 2
    }
}


def get_preset(name):
    """Retorna configurações de um preset"""
    return PRESETS.get(name, PRESETS['normal'])


def print_config():
    """Imprime configurações atuais"""
    print("⚙️  CONFIGURAÇÕES ATUAIS")
    print("="*50)
    print(f"Arena: {ARENA_WIDTH}x{ARENA_HEIGHT}")
    print(f"Vídeo: {VIDEO_WIDTH}x{VIDEO_HEIGHT} @ {VIDEO_FPS}fps")
    print(f"HP Padrão: {HP_DEFAULT}")
    print(f"Dano Base: {DAMAGE_BASE}")
    print(f"Max Visible: {MAX_VISIBLE_PARTICLES}")
    print("="*50)
