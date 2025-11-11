#!/usr/bin/env python3
"""
Script de configuração inicial do Instagram
"""

from instagram_fetch import InstagramFetcher
from pathlib import Path
import sys

def main():
    print("🔐 CONFIGURAÇÃO DA CONTA INSTAGRAM")
    print("="*50)
    
    # Criar diretórios
    Path("data").mkdir(exist_ok=True)
    Path("assets/pfps").mkdir(parents=True, exist_ok=True)
    
    # Inicializar fetcher
    fetcher = InstagramFetcher()
    
    # Tentar login
    print("\n📱 Fazendo login no Instagram...")
    if not fetcher.login():
        print("\n❌ Falha no login. Possíveis causas:")
        print("  - Senha incorreta")
        print("  - 2FA não completado")
        print("  - Instagram bloqueou temporariamente")
        sys.exit(1)
    
    print("\n✅ Login bem-sucedido!")
    print(f"📁 Sessão salva em: {fetcher.session_file}")
    
    # Coletar amostra de seguidores
    print("\n👥 Coletando amostra de seguidores (100)...")
    try:
        data = fetcher.fetch_followers(max_count=100)
        print(f"\n✅ {data['count']} seguidores coletados")
        print(f"📁 Cache salvo em: {fetcher.followers_file}")
        
        print("\n🎉 CONFIGURAÇÃO CONCLUÍDA!")
        print("\nPróximos passos:")
        print("  1. Execute: python main.py --day 1")
        print("  2. Ou teste: python main.py --demo")
        
    except Exception as e:
        print(f"\n⚠️ Erro ao coletar seguidores: {e}")
        print("Mas a sessão foi salva com sucesso.")
        print("Tente executar: python main.py --day 1")

if __name__ == "__main__":
    main()