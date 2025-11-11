"""
Módulo para upload automático no Instagram
"""

import os
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired
import time


class InstagramPoster:
    """Gerencia upload de vídeos no Instagram"""
    
    def __init__(self, session_file='data/session.json'):
        self.session_file = session_file
        self.client = None
    
    def login(self):
        """Autentica no Instagram"""
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
        password = input("Password: ")
        
        try:
            self.client.login(username, password)
            
            # Salvar sessão
            self.client.dump_settings(self.session_file)
            print("✅ Login bem-sucedido")
            return True
            
        except ChallengeRequired:
            print("\n⚠️  Verificação 2FA necessária")
            print("Siga as instruções no seu dispositivo")
            return False
        except Exception as e:
            print(f"❌ Erro no login: {e}")
            return False
    
    def upload_video(self, video_path, caption, post_type='reel', thumbnail_path=None):
        """Faz upload de vídeo no Instagram"""
        
        if not os.path.exists(video_path):
            print(f"❌ Vídeo não encontrado: {video_path}")
            return None
        
        # Confirmar upload
        print("\n" + "="*60)
        print("📤 CONFIRMAÇÃO DE UPLOAD")
        print("="*60)
        print(f"Vídeo: {video_path}")
        print(f"Tipo: {post_type}")
        print(f"\nLegenda:\n{caption}")
        print("="*60)
        
        confirm = input("\nConfirma o upload? [s/N]: ")
        if confirm.lower() != 's':
            print("❌ Upload cancelado")
            return None
        
        # Login
        if not self.login():
            print("❌ Falha no login")
            return None
        
        try:
            print(f"\n📤 Fazendo upload do {post_type}...")
            
            if post_type == 'reel':
                # Upload como Reel
                media = self.client.clip_upload(
                    video_path,
                    caption=caption,
                    thumbnail=thumbnail_path
                )
            else:
                # Upload como post no feed
                media = self.client.video_upload(
                    video_path,
                    caption=caption,
                    thumbnail=thumbnail_path
                )
            
            # Obter URL da publicação
            media_id = media.id
            code = media.code
            url = f"https://www.instagram.com/p/{code}/"
            
            print(f"✅ Upload concluído com sucesso!")
            print(f"🔗 URL: {url}")
            print(f"📊 Media ID: {media_id}")
            
            return url
            
        except Exception as e:
            print(f"❌ Erro durante upload: {e}")
            return None
    
    def upload_with_retry(self, video_path, caption, post_type='reel', 
                         thumbnail_path=None, max_retries=3):
        """Upload com retry automático"""
        
        for attempt in range(max_retries):
            try:
                result = self.upload_video(video_path, caption, post_type, thumbnail_path)
                
                if result:
                    return result
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 30
                    print(f"⏳ Aguardando {wait_time}s antes de tentar novamente...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                print(f"❌ Tentativa {attempt + 1}/{max_retries} falhou: {e}")
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 30
                    print(f"⏳ Aguardando {wait_time}s antes de tentar novamente...")
                    time.sleep(wait_time)
        
        print("❌ Todas as tentativas de upload falharam")
        return None
    
    def get_account_info(self):
        """Retorna informações da conta"""
        if not self.client:
            if not self.login():
                return None
        
        try:
            user_id = self.client.user_id
            user_info = self.client.user_info(user_id)
            
            return {
                'username': user_info.username,
                'full_name': user_info.full_name,
                'followers': user_info.follower_count,
                'following': user_info.following_count,
                'posts': user_info.media_count
            }
        except Exception as e:
            print(f"❌ Erro ao obter info da conta: {e}")
            return None