# instagram-battle

Estrutura do projeto criada como esqueleto. Cole seus códigos nos arquivos correspondentes.

Árvore do projeto:

instagram-battle/
│
├── main.py                 # Orquestrador principal
├── instagram_fetch.py      # Coleta de seguidores
├── simulation_engine.py    # Motor de física
├── renderer.py             # Renderização de vídeo
├── video_export.py         # Exportação final
├── instagram_post.py       # Upload automático
│
├── assets/
│   └── pfps/              # Fotos de perfil (cache)
├── data/
│   ├── followers.json     # Cache de seguidores
│   └── session.json       # Sessão do Instagram
├── output/
│   └── *.mp4              # Vídeos gerados
│
├── requirements.txt
└── README.md

O que fazer agora:

- Substitua os placeholders nos arquivos .py pelos seus códigos.
- Adicione dependências reais em `requirements.txt` e instale via pip.
- Execute `python main.py` para rodar o orquestrador (quando implementado).

Observações:
- Os arquivos `data/*.json` estão vazios; o seu código de coleta deve gravá-los.
- Os diretórios `assets/pfps` e `output` foram criados para cache e saída.
