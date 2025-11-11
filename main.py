#!/usr/bin/env python3
"""
Sistema de Batalha de Seguidores do Instagram
Orquestrador principal do projeto
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Importações dos módulos do projeto
from instagram_fetch import InstagramFetcher
from simulation_engine import BattleSimulator
from renderer import BattleRenderer
from video_export import VideoExporter
from instagram_post import InstagramPoster


def ensure_directories():
    """Cria estrutura de diretórios necessária"""
    dirs = ['assets/pfps', 'data', 'output']
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)


def get_consent():
    """Solicita confirmação de consentimento dos seguidores"""
    print("\n" + "="*60)
    print("⚠️  AVISO DE CONSENTIMENTO")
    print("="*60)
    print("\nEste projeto usa usernames e fotos de perfil de seguidores.")
    print("Certifique-se de ter postado o aviso de consentimento:")
    print("\n>>> TEXTO SUGERIDO PARA POSTAR <<<")
    print("-"*60)
    print("AVISO: nesta conta estamos fazendo um vídeo-jogo experimental")
    print("onde os seguidores podem aparecer como personagens (usando")
    print("username e foto de perfil).")
    print("\nAo seguir esta conta, você concorda que seu username e foto")
    print("de perfil poderão ser usados neste projeto e exibidos em")
    print("vídeos públicos.")
    print("\nSe não concordar, basta deixar de seguir. Obrigado!")
    print("-"*60)
    
    confirm = input("\n✅ Confirma que seus seguidores foram avisados? [s/N]: ")
    if confirm.lower() != 's':
        print("❌ Operação cancelada — consentimento obrigatório.")
        sys.exit(0)
    print("✅ Consentimento confirmado. Prosseguindo...\n")


def parse_arguments():
    """Parse argumentos da linha de comando"""
    parser = argparse.ArgumentParser(
        description='Sistema de Batalha de Seguidores do Instagram'
    )
    
    parser.add_argument('--day', type=int, default=1,
                       help='Número do dia (exibido no título)')
    parser.add_argument('--max-participants', type=int, default=10000,
                       help='Número máximo de bolas simuladas')
    parser.add_argument('--hp-default', type=float, default=100.0,
                       help='Vida inicial de cada bola')
    parser.add_argument('--damage-base', type=float, default=5.0,
                       help='Dano base por colisão')
    parser.add_argument('--fps', type=int, default=30,
                       help='Taxa de quadros do vídeo')
    parser.add_argument('--duration', type=int, default=60,
                       help='Duração máxima em segundos')
    parser.add_argument('--output', type=str, default=None,
                       help='Caminho de saída do vídeo')
    parser.add_argument('--upload', type=str, default='false',
                       choices=['true', 'false'],
                       help='Se deve publicar após gerar')
    parser.add_argument('--post-as', type=str, default='reel',
                       choices=['feed', 'reel'],
                       help='Tipo de postagem no Instagram')
    parser.add_argument('--caption-template', type=str, default=None,
                       help='Template customizado da legenda')
    parser.add_argument('--demo', action='store_true',
                       help='Modo teste com imagens genéricas')
    parser.add_argument('--skip-fetch', action='store_true',
                       help='Pular coleta (usar cache existente)')
    
    return parser.parse_args()


def main():
    """Função principal"""
    print("🎮 Sistema de Batalha de Seguidores do Instagram")
    print("="*60)
    
    args = parse_arguments()
    ensure_directories()
    
    # Define output path
    if args.output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"output/battle_day{args.day}_{timestamp}.mp4"
    
    # Solicitar consentimento (exceto em modo demo)
    if not args.demo:
        get_consent()
    
    # ETAPA 1: Coletar seguidores
    print("\n📥 ETAPA 1: Coletando seguidores...")
    print("-"*60)
    
    fetcher = InstagramFetcher(demo_mode=args.demo)
    
    # Verificar se há cache disponível
    cache_exists = os.path.exists('data/followers.json')
    
    if args.skip_fetch:
        if not cache_exists:
            print("❌ Erro: --skip-fetch usado mas nenhum cache encontrado!")
            print("💡 Solução: Execute sem --skip-fetch para coletar seguidores")
            sys.exit(1)
        
        print("⏭️  Pulando coleta (usando cache existente)")
        with open('data/followers.json', 'r', encoding='utf-8') as f:
            followers_data = json.load(f)
    else:
        # Perguntar se deve usar cache (se existir)
        if cache_exists and not args.demo:
            with open('data/followers.json', 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            print(f"📦 Cache encontrado com {cached_data['count']} seguidores")
            print(f"   Data: {datetime.fromtimestamp(cached_data['timestamp']).strftime('%d/%m/%Y %H:%M')}")
            use_cache = input("   Deseja usar o cache? [S/n]: ").strip().lower()
            
            if use_cache in ['', 's', 'sim', 'y', 'yes']:
                followers_data = cached_data
                print("✅ Usando cache existente")
            else:
                print("🔄 Coletando novos seguidores...")
                followers_data = fetcher.fetch_followers(max_count=args.max_participants)
        else:
            # Não há cache ou é modo demo
            followers_data = fetcher.fetch_followers(max_count=args.max_participants)
    
    followers = followers_data['followers'][:args.max_participants]
    
    if len(followers) == 0:
        print("❌ Erro: Nenhum seguidor disponível!")
        print("💡 Dicas:")
        print("   - Use --demo para testar com dados sintéticos")
        print("   - Verifique se seu login no Instagram funcionou")
        print("   - Certifique-se de ter seguidores na conta")
        sys.exit(1)
    
    # Avisar se o número solicitado for maior que o disponível
    if len(followers) < args.max_participants:
        print(f"⚠️  Aviso: Solicitado {args.max_participants} participantes, mas apenas {len(followers)} disponíveis")
        print(f"   Usando todos os {len(followers)} seguidores do cache")
    
    print(f"✅ {len(followers)} seguidores carregados")
    
    # ETAPA 2: Simular batalha
    print("\n⚔️  ETAPA 2: Simulando batalha...")
    print("-"*60)
    
    simulator = BattleSimulator(
        followers=followers,
        hp_default=args.hp_default,
        damage_base=args.damage_base
    )
    
    battle_frames = simulator.run_simulation(
        max_frames=args.fps * args.duration,
        fps=args.fps
    )
    
    winner = simulator.get_winner()
    print(f"🏆 Vencedor: @{winner['username']}")
    
    # ETAPA 3: Renderizar vídeo
    print("\n🎬 ETAPA 3: Renderizando vídeo...")
    print("-"*60)
    
    renderer = BattleRenderer(
        width=1080,
        height=1920,  # Formato vertical para Reels
        fps=args.fps
    )
    
    video_path = renderer.render_video(
        battle_frames=battle_frames,
        followers=followers,
        winner=winner,
        day=args.day,
        output_path=args.output
    )
    
    print(f"✅ Vídeo salvo em: {video_path}")
    
    # ETAPA 4: Publicar no Instagram (opcional)
    if args.upload == 'true':
        print("\n📤 ETAPA 4: Publicando no Instagram...")
        print("-"*60)
        
        poster = InstagramPoster()
        
        # Gerar legenda
        if args.caption_template:
            caption = args.caption_template.format(
                day=args.day,
                winner=winner['username']
            )
        else:
            caption = (
                f"Dia:{args.day} — fazendo meus seguidores lutarem! 🏆\n"
                f"Vencedor: @{winner['username']}\n\n"
                f"Se não quiser aparecer, basta deixar de seguir."
            )
        
        result = poster.upload_video(
            video_path=video_path,
            caption=caption,
            post_type=args.post_as,
            thumbnail_path=winner.get('pfp_path')
        )
        
        if result:
            print(f"✅ Publicado com sucesso!")
            print(f"🔗 URL: {result}")
        else:
            print("❌ Falha ao publicar")
    else:
        print("\n⏭️  Upload pulado (use --upload true para publicar)")
    
    print("\n" + "="*60)
    print("🎉 PROCESSO CONCLUÍDO!")
    print("="*60)


if __name__ == "__main__":
    main()