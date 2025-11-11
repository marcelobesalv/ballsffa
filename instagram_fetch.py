"""
Módulo para coletar seguidores e fotos de perfil do Instagram
"""

import json
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired
import time


class InstagramFetcher:
    """Gerencia coleta de seguidores e download de fotos de perfil"""
    
    def __init__(self, demo_mode=False):
        self.demo_mode = demo_mode
        self.client = None
        self.session_file = 'data/session.json'
        self.followers_file = 'data/followers.json'
        
    def login(self):
        """Autentica no Instagram com sessão persistente"""
        if self.demo_mode:
            print("🧪 Modo DEMO ativado - usando dados sintéticos")
            return True
            
        self.client = Client()
        
        # Tenta carregar sessão existente
        if os.path.exists(self.session_file):
            try:
                print("🔄 Carregando sessão existente...")
                self.client.load_settings(self.session_file)
                self.client.login_by_sessionid(self.client.sessionid)
                print("✅ Login via sessão bem-sucedido")
                return True
            except Exception as e:
                print(f"⚠️  Sessão expirada: {e}")
        
        # Login manual
        print("\n🔐 Login necessário")
        username = input("Username: ")
        password = input("Password (não será armazenado): ")
        
        try:
            self.client.login(username, password)
            
            # Salvar sessão
            self.client.dump_settings(self.session_file)
            print("✅ Login bem-sucedido e sessão salva")
            return True
            
        except ChallengeRequired:
            print("\n⚠️  Verificação 2FA necessária")
            print("Siga as instruções no seu dispositivo móvel")
            return False
        except Exception as e:
            print(f"❌ Erro no login: {e}")
            return False
    
    def get_followers_list(self, max_count=10000):
        """Obtém lista de seguidores"""
        if self.demo_mode:
            return self._generate_demo_followers(max_count)
        
        try:
            user_id = self.client.user_id
            print(f"📋 Coletando até {max_count} seguidores...")
            
            followers = []
            amount = min(max_count, 10000)  # Instagram API limit
            
            # Coletar em lotes
            raw_followers = self.client.user_followers(user_id, amount=amount)
            
            for user_id, user_info in raw_followers.items():
                followers.append({
                    'user_id': str(user_id),
                    'username': user_info.username,
                    'full_name': user_info.full_name,
                    'profile_pic_url': str(user_info.profile_pic_url),  # Convert HttpUrl to string
                })
                
                if len(followers) >= max_count:
                    break
            
            print(f"✅ {len(followers)} seguidores coletados")
            return followers
            
        except Exception as e:
            print(f"❌ Erro ao coletar seguidores: {e}")
            return []
    
    def _generate_demo_followers(self, count):
        """Gera seguidores sintéticos para modo demo"""
        import random
        
        demo_names = [
            'adventure_seeker', 'coffee_lover', 'tech_guru', 'nature_fan',
            'music_vibes', 'fitness_beast', 'art_creator', 'book_worm',
            'travel_soul', 'food_explorer', 'game_master', 'photo_ninja'
        ]
        
        followers = []
        for i in range(min(count, 1000)):  # Limita demo
            base_name = random.choice(demo_names)
            followers.append({
                'user_id': str(1000000 + i),
                'username': f"{base_name}_{i}",
                'full_name': f"Demo User {i}",
                'profile_pic_url': f"https://i.pravatar.cc/150?img={i % 70}",
                'is_verified': random.random() < 0.05
            })
        
        return followers
    
    def download_profile_pic(self, follower, timeout=10):
        """Baixa uma foto de perfil"""
        try:
            username = follower['username']
            url = follower['profile_pic_url']
            
            pfp_path = f"assets/pfps/{username}.jpg"
            
            # Verifica se já existe
            if os.path.exists(pfp_path):
                return pfp_path
            
            # Download
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            
            with open(pfp_path, 'wb') as f:
                f.write(response.content)
            
            return pfp_path
            
        except Exception as e:
            print(f"⚠️  Erro ao baixar pfp de {follower['username']}: {e}")
            return None
    
    def download_all_pfps(self, followers, max_workers=10):
        """Download paralelo de todas as fotos de perfil"""
        print(f"⬇️  Baixando {len(followers)} fotos de perfil...")
        
        downloaded = 0
        failed = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.download_profile_pic, f): f 
                for f in followers
            }
            
            for future in as_completed(futures):
                follower = futures[future]
                try:
                    pfp_path = future.result()
                    if pfp_path:
                        follower['pfp_path'] = pfp_path
                        downloaded += 1
                    else:
                        failed += 1
                        
                    # Progress
                    if (downloaded + failed) % 100 == 0:
                        print(f"   Progresso: {downloaded + failed}/{len(followers)}")
                        
                except Exception as e:
                    failed += 1
        
        print(f"✅ Download concluído: {downloaded} ok, {failed} falhas")
        return followers
    
    def fetch_followers(self, max_count=10000):
        """Workflow completo: login, coletar, baixar pfps"""
        
        # Modo demo - não precisa de login
        if self.demo_mode:
            print("🧪 Modo DEMO - gerando seguidores sintéticos")
            followers = self.get_followers_list(max_count)
            followers = self.download_all_pfps(followers)
            
            data = {
                'timestamp': time.time(),
                'count': len(followers),
                'followers': followers
            }
            return data
        
        # Login (modo real)
        if not self.login():
            print("\n❌ Falha no login")
            print("💡 Deseja usar modo DEMO? [s/N]: ", end='')
            use_demo = input().strip().lower()
            if use_demo in ['s', 'sim', 'y', 'yes']:
                self.demo_mode = True
                return self.fetch_followers(max_count)
            else:
                raise Exception("Falha no login e modo demo recusado")
        
        # Coletar seguidores
        followers = self.get_followers_list(max_count)
        
        if not followers or len(followers) == 0:
            print("\n⚠️  Nenhum seguidor coletado!")
            print("💡 Possíveis causas:")
            print("   - Conta sem seguidores")
            print("   - Rate limit do Instagram")
            print("   - Conta privada/bloqueada")
            print("\n💡 Deseja usar modo DEMO? [s/N]: ", end='')
            use_demo = input().strip().lower()
            if use_demo in ['s', 'sim', 'y', 'yes']:
                self.demo_mode = True
                return self.fetch_followers(max_count)
            else:
                raise Exception("Nenhum seguidor coletado e modo demo recusado")
        
        # Download das fotos
        followers = self.download_all_pfps(followers)
        
        # Salvar cache com segurança (usar arquivo temporário)
        data = {
            'timestamp': time.time(),
            'count': len(followers),
            'followers': followers
        }
        
        # Escrever em arquivo temporário primeiro
        temp_file = self.followers_file + '.tmp'
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Se escrita foi bem-sucedida, substituir o arquivo original
            import shutil
            shutil.move(temp_file, self.followers_file)
            print(f"💾 Cache salvo em {self.followers_file}")
        except Exception as e:
            print(f"❌ Erro ao salvar cache: {e}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise
        
        return data