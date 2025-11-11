# 🎮 Balls FFA - Battle Royale dos Seguidores

Um jogo onde seus seguidores do Instagram lutam entre si como bolas em uma arena até sobrar apenas um vencedor!

## 🎯 Como Funciona

1. **Coleta** os seguidores da sua conta do Instagram
2. **Transforma** cada seguidor em uma bola colorida com sua foto de perfil  
3. **Simula** uma batalha física onde as bolas colidem e se danificam
4. **Gera** um vídeo da batalha completa até restar apenas 1 vencedor

## 🚀 Como Usar

```bash
# Instalar dependências
pip install -r requirements.txt

# Rodar com dados reais (precisa fazer login no Instagram)
python main.py --max-participants 100

# Testar com dados fake
python main.py --demo --max-participants 50
```

## ⚙️ Física do Jogo

- Bolas **ricocheteiam** pela arena constantemente
- **Colisões** causam dano baseado em velocidade e tamanho
- Bolas **crescem** quando matam outras (ficam mais fortes)
- **Sobreviventes** ficam mais rápidos conforme crescem
- Último sobrevivente é o **vencedor**! 🏆
