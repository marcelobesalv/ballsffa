"""
Renderizador de vídeo com OpenCV
"""

import cv2
import numpy as np
from PIL import Image
import os


class BattleRenderer:
    """Renderiza frames da batalha em vídeo"""
    
    def __init__(self, width=1080, height=1920, fps=30):
        self.width = width
        self.height = height
        self.fps = fps
        
        # Cores
        self.bg_color = (20, 20, 30)
        self.text_color = (255, 255, 255)
        self.hp_bar_bg = (50, 50, 50)
        self.hp_bar_full = (0, 255, 100)
        self.hp_bar_low = (255, 50, 50)
        
        # Fontes (OpenCV)
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_bold = cv2.FONT_HERSHEY_DUPLEX
        self.font_scale_title = 2.0
        self.font_scale_normal = 0.6
        self.font_thickness = 2
        self.font_thickness_bold = 3
        
        # LOD (Level of Detail)
        self.max_visible_particles = 200
        
        # Cache de imagens de perfil
        self.pfp_cache = {}
    
    def render_video(self, battle_frames, followers, winner, day, output_path):
        """Renderiza vídeo completo"""
        print(f"🎬 Renderizando {len(battle_frames)} frames...")
        
        # Configurar writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, self.fps, 
                                 (self.width, self.height))
        
        if not writer.isOpened():
            raise Exception("Não foi possível criar o VideoWriter")
        
        # Carregar fotos de perfil em cache
        self._load_pfp_cache(followers)
        
        # Frame inicial (título)
        for _ in range(self.fps * 2):  # 2 segundos
            frame = self._render_intro_frame(day, len(followers))
            writer.write(frame)
        
        # Frames da batalha
        for i, frame_data in enumerate(battle_frames):
            frame = self._render_battle_frame(frame_data, followers, day)
            writer.write(frame)
            
            if (i + 1) % 100 == 0:
                print(f"   Renderizados: {i+1}/{len(battle_frames)} frames")
        
        # Frame final (vencedor)
        for _ in range(self.fps * 3):  # 3 segundos
            frame = self._render_winner_frame(winner)
            writer.write(frame)
        
        writer.release()
        print(f"✅ Vídeo renderizado: {output_path}")
        
        return output_path
    
    def _load_pfp_cache(self, followers):
        """Carrega fotos de perfil em cache"""
        print("📷 Carregando fotos de perfil...")
        
        for follower in followers[:self.max_visible_particles]:
            pfp_path = follower.get('pfp_path')
            if pfp_path and os.path.exists(pfp_path):
                try:
                    img = Image.open(pfp_path)
                    # Keep larger size for better quality when scaled
                    img = img.resize((200, 200))
                    img = np.array(img)
                    
                    if img.shape[2] == 4:  # RGBA
                        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
                    elif img.shape[2] == 3:  # RGB
                        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                    
                    self.pfp_cache[follower['username']] = img
                except Exception as e:
                    print(f"⚠️  Erro ao carregar pfp de {follower['username']}: {e}")
    
    def _render_intro_frame(self, day, total_followers):
        """Renderiza frame de introdução"""
        frame = np.full((self.height, self.width, 3), self.bg_color, dtype=np.uint8)
        
        # Título
        title = f"Dia:{day}"
        subtitle = "fazendo meus seguidores lutarem"
        info = f"Seguidores: {total_followers}"
        
        # Título principal
        title_size = cv2.getTextSize(title, self.font_bold, self.font_scale_title, self.font_thickness_bold)[0]
        title_x = (self.width - title_size[0]) // 2
        title_y = self.height // 3
        
        cv2.putText(frame, title, (title_x, title_y), self.font_bold,
                   self.font_scale_title, self.text_color, self.font_thickness_bold, cv2.LINE_AA)
        
        # Subtítulo
        subtitle_size = cv2.getTextSize(subtitle, self.font, 
                                       self.font_scale_normal * 1.5, self.font_thickness)[0]
        subtitle_x = (self.width - subtitle_size[0]) // 2
        subtitle_y = title_y + 80
        
        cv2.putText(frame, subtitle, (subtitle_x, subtitle_y), self.font,
                   self.font_scale_normal * 1.5, self.text_color, self.font_thickness, cv2.LINE_AA)
        
        # Info
        info_size = cv2.getTextSize(info, self.font, 
                                   self.font_scale_normal * 1.2, self.font_thickness)[0]
        info_x = (self.width - info_size[0]) // 2
        info_y = self.height * 2 // 3
        
        cv2.putText(frame, info, (info_x, info_y), self.font,
                   self.font_scale_normal * 1.2, (100, 200, 255), self.font_thickness, cv2.LINE_AA)
        
        return frame
    
    def _render_battle_frame(self, frame_data, followers, day):
        """Renderiza um frame da batalha"""
        frame = np.full((self.height, self.width, 3), self.bg_color, dtype=np.uint8)
        
        positions = frame_data['positions']
        hp = frame_data['hp']
        alive = frame_data['alive']
        alive_count = frame_data['alive_count']
        radius = frame_data.get('radius', np.full(len(positions), 10.0))  # Raios dinâmicos
        kills = frame_data.get('kills', np.zeros(len(positions)))  # Kills
        
        # Draw HUD first (at edges)
        hud_top_height = 80
        hud_bottom_height = 80
        self._draw_hud(frame, day, alive_count, len(followers), hud_top_height, hud_bottom_height)
        
        # Escalar posições para o canvas (battle area between HUD elements)
        battle_height = self.height - hud_top_height - hud_bottom_height
        scale_x = self.width * 0.95 / 1000.0
        scale_y = battle_height * 0.95 / 1000.0
        offset_x = self.width * 0.025
        offset_y = hud_top_height + (battle_height * 0.025)
        
        # Selecionar subset visível (LOD)
        alive_indices = np.where(alive)[0]
        
        if len(alive_indices) > self.max_visible_particles:
            # Priorizar bolas maiores (mais interessantes)
            sizes = radius[alive_indices]
            # Pegar as maiores + amostra aleatória
            n_largest = min(50, len(alive_indices))
            largest_idx = alive_indices[np.argsort(sizes)[-n_largest:]]
            
            remaining = self.max_visible_particles - n_largest
            if remaining > 0 and len(alive_indices) > n_largest:
                other_idx = np.setdiff1d(alive_indices, largest_idx)
                step = len(other_idx) / remaining
                sample_idx = other_idx[::max(1, int(step))][:remaining]
                visible_indices = np.concatenate([largest_idx, sample_idx])
            else:
                visible_indices = largest_idx
        else:
            visible_indices = alive_indices
        
        # Ordenar por tamanho (desenhar menores primeiro)
        visible_indices = visible_indices[np.argsort(radius[visible_indices])]
        
        # Desenhar partículas
        for idx in visible_indices:
            x = int(positions[idx, 0] * scale_x + offset_x)
            y = int(positions[idx, 1] * scale_y + offset_y)
            
            # HP para cor
            hp_ratio = hp[idx] / 100.0
            color = self._interpolate_color(self.hp_bar_low, self.hp_bar_full, hp_ratio)
            
            # Raio escalado
            display_radius = int(radius[idx] * scale_x * 0.8)
            display_radius = max(5, min(display_radius, 100))  # Limitar tamanho na tela
            
            # Desenhar círculo
            cv2.circle(frame, (x, y), display_radius, color, -1)
            cv2.circle(frame, (x, y), display_radius, (255, 255, 255), 2)
            
            # Desenhar pfp circular (scale with ball size)
            username = followers[idx]['username']
            if username in self.pfp_cache and display_radius > 8:
                self._draw_circular_pfp(frame, x, y, display_radius, username)
            
            # Health bar acima da bola
            if display_radius > 5:
                self._draw_health_bar(frame, x, y, display_radius, hp_ratio)
            
            # Mostrar kills para bolas grandes
            if kills[idx] > 0 and display_radius > 15:
                kill_text = f"{int(kills[idx])}"
                cv2.putText(frame, kill_text, (x - 10, y + 5),
                           self.font, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
        
        return frame
    
    def _render_winner_frame(self, winner):
        """Renderiza frame do vencedor"""
        frame = np.full((self.height, self.width, 3), self.bg_color, dtype=np.uint8)
        
        # Título
        title = "VENCEDOR"
        username = f"@{winner['username']}"
        
        # Desenhar título
        title_size = cv2.getTextSize(title, self.font_bold, 2.5, 4)[0]
        title_x = (self.width - title_size[0]) // 2
        title_y = self.height // 4
        
        cv2.putText(frame, title, (title_x, title_y), self.font_bold,
                   2.5, (255, 215, 0), 4, cv2.LINE_AA)
        
        # Foto do vencedor (se disponível)
        pfp_path = winner.get('pfp_path')
        if pfp_path and os.path.exists(pfp_path):
            try:
                pfp = Image.open(pfp_path)
                pfp = pfp.resize((300, 300))
                pfp = np.array(pfp)
                
                if pfp.shape[2] == 4:
                    pfp = cv2.cvtColor(pfp, cv2.COLOR_RGBA2BGR)
                else:
                    pfp = cv2.cvtColor(pfp, cv2.COLOR_RGB2BGR)
                
                pfp_x = (self.width - 300) // 2
                pfp_y = self.height // 2 - 150
                
                frame[pfp_y:pfp_y+300, pfp_x:pfp_x+300] = pfp
                
                # Borda dourada
                cv2.rectangle(frame, (pfp_x-5, pfp_y-5), 
                            (pfp_x+305, pfp_y+305), (255, 215, 0), 5)
            except:
                pass
        
        # Username
        username_size = cv2.getTextSize(username, self.font_bold, 1.8, 3)[0]
        username_x = (self.width - username_size[0]) // 2
        username_y = self.height * 3 // 4
        
        cv2.putText(frame, username, (username_x, username_y), self.font_bold,
                   1.8, self.text_color, 3, cv2.LINE_AA)
        
        return frame
    
    def _draw_hud(self, frame, day, alive_count, total, hud_top_height, hud_bottom_height):
        """Desenha HUD informativo nas bordas"""
        # Top HUD - Title
        title = f"Dia:{day} - Batalha de Seguidores"
        title_size = cv2.getTextSize(title, self.font_bold, 
                                     self.font_scale_normal * 1.2, self.font_thickness)[0]
        title_x = (self.width - title_size[0]) // 2
        title_y = hud_top_height // 2 + 10
        
        cv2.putText(frame, title, (title_x, title_y), self.font_bold,
                   self.font_scale_normal * 1.2, self.text_color, self.font_thickness, cv2.LINE_AA)
        
        # Bottom HUD - Alive counter
        alive_text = f"Vivos: {alive_count}/{total}"
        alive_size = cv2.getTextSize(alive_text, self.font_bold,
                                    self.font_scale_normal * 1.5, self.font_thickness_bold)[0]
        alive_x = (self.width - alive_size[0]) // 2
        alive_y = self.height - (hud_bottom_height // 2) + 10
        
        cv2.putText(frame, alive_text, (alive_x, alive_y), self.font_bold,
                   self.font_scale_normal * 1.5, (100, 255, 100), self.font_thickness_bold, cv2.LINE_AA)
        
        # Add separator lines
        cv2.line(frame, (0, hud_top_height), (self.width, hud_top_height), (100, 100, 100), 2)
        cv2.line(frame, (0, self.height - hud_bottom_height), 
                (self.width, self.height - hud_bottom_height), (100, 100, 100), 2)
    
    def _interpolate_color(self, color1, color2, ratio):
        """Interpola entre duas cores"""
        ratio = np.clip(ratio, 0, 1)
        return tuple(int(c1 + (c2 - c1) * ratio) for c1, c2 in zip(color1, color2))
    
    def _draw_circular_pfp(self, frame, x, y, radius, username):
        """Desenha profile picture circular dentro da bola"""
        if username not in self.pfp_cache:
            return
        
        pfp = self.pfp_cache[username]
        
        # Tamanho da pfp baseado no raio da bola (80% do diâmetro)
        pfp_diameter = int(radius * 1.6)
        pfp_diameter = max(10, min(pfp_diameter, 150))  # Limites
        
        try:
            # Resize pfp
            resized_pfp = cv2.resize(pfp, (pfp_diameter, pfp_diameter))
            
            # Criar máscara circular
            mask = np.zeros((pfp_diameter, pfp_diameter), dtype=np.uint8)
            cv2.circle(mask, (pfp_diameter // 2, pfp_diameter // 2), pfp_diameter // 2, 255, -1)
            
            # Aplicar máscara
            masked_pfp = cv2.bitwise_and(resized_pfp, resized_pfp, mask=mask)
            
            # Calcular posição
            x1 = x - pfp_diameter // 2
            y1 = y - pfp_diameter // 2
            x2 = x1 + pfp_diameter
            y2 = y1 + pfp_diameter
            
            # Verificar bounds
            if x1 < 0 or y1 < 0 or x2 >= self.width or y2 >= self.height:
                return
            
            # Blending: apenas sobrescrever onde a máscara é diferente de zero
            mask_3channel = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            mask_bool = mask > 0
            
            frame_roi = frame[y1:y2, x1:x2]
            frame_roi[mask_bool] = masked_pfp[mask_bool]
            
        except Exception as e:
            pass  # Silently fail if pfp can't be drawn
    
    def _draw_health_bar(self, frame, x, y, radius, hp_ratio):
        """Desenha barra de HP acima da bola"""
        # Dimensões da barra
        bar_width = int(radius * 1.8)
        bar_height = max(4, int(radius * 0.3))
        bar_x = x - bar_width // 2
        bar_y = y - radius - bar_height - 5  # 5px acima da bola
        
        # Verificar bounds
        if bar_y < 0 or bar_x < 0 or bar_x + bar_width >= self.width:
            return
        
        # Background da barra (cinza escuro)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height),
                     self.hp_bar_bg, -1)
        
        # Barra de HP (colorida)
        hp_width = int(bar_width * hp_ratio)
        hp_color = self._interpolate_color(self.hp_bar_low, self.hp_bar_full, hp_ratio)
        
        if hp_width > 0:
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + hp_width, bar_y + bar_height),
                         hp_color, -1)
        
        # Borda da barra
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height),
                     (255, 255, 255), 1)