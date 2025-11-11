"""
Motor de simulação física escalável com NumPy e Numba
"""

import numpy as np
from numba import jit, prange
import time


class BattleSimulator:
    """Simula batalha em massa entre seguidores"""
    
    def __init__(self, followers, hp_default=100.0, damage_base=5.0):
        self.followers = followers
        self.n_particles = len(followers)
        self.hp_default = hp_default
        self.damage_base = damage_base
        
        # Arena
        self.arena_width = 1000.0
        self.arena_height = 1000.0
        
        # Física
        self.particle_radius = 10.0
        self.max_speed = 8.0  # Base speed
        self.bounce_damping = 0.98  # Slight energy loss on walls (makes collision boosts more visible)
        
        # Spatial grid para otimização
        self.grid_size = 50.0
        
        # Thresholds para crescimento global
        self.growth_thresholds = [500, 250, 100, 50, 25, 10, 5]
        self.last_growth_threshold = self.n_particles + 1
        
        # Inicializar arrays
        self._init_arrays()
        
    def _init_arrays(self):
        """Inicializa arrays NumPy para simulação"""
        n = self.n_particles
        
        # Calcular tamanho inicial baseado no número de participantes
        # Menos participantes = bolas maiores para manter visibilidade
        if n <= 10:
            initial_radius = self.particle_radius * 4.0  # 4x maior para poucos participantes
        elif n <= 50:
            initial_radius = self.particle_radius * 3.0  # 3x maior
        elif n <= 100:
            initial_radius = self.particle_radius * 2.5  # 2.5x maior
        elif n <= 200:
            initial_radius = self.particle_radius * 2.0  # 2x maior
        elif n <= 500:
            initial_radius = self.particle_radius * 1.5  # 1.5x maior
        else:
            initial_radius = self.particle_radius  # Tamanho normal para muitos
        
        # Posições aleatórias
        self.positions = np.random.rand(n, 2) * [self.arena_width, self.arena_height]
        
        # Velocidades aleatórias (direção aleatória, velocidade constante)
        angles = np.random.rand(n) * 2 * np.pi
        speed = self.max_speed * 0.8  # Start at 80% of max speed
        self.velocities = np.column_stack([
            np.cos(angles) * speed,
            np.sin(angles) * speed
        ])
        
        # Vida
        self.hp = np.full(n, self.hp_default, dtype=np.float32)
        
        # Vivos
        self.alive = np.ones(n, dtype=bool)
        
        # Força (varia por seguidor)
        self.strength = np.random.uniform(0.8, 1.2, n)
        
        # Raio das bolas (usa tamanho inicial calculado)
        self.radius = np.full(n, initial_radius, dtype=np.float32)
        
        # Contador de kills
        self.kills = np.zeros(n, dtype=np.int32)
        
        print(f"⚙️  Simulação inicializada: {n} partículas")
        print(f"   Raio inicial: {initial_radius:.1f}px (base: {self.particle_radius}px)")
        print(f"   Com crescimento dinâmico e movimento contínuo")
    
    def run_simulation(self, max_frames=1800, fps=30):
        """Executa simulação completa"""
        print(f"🎮 Iniciando simulação ({max_frames} frames máx, {fps} FPS)")
        
        frames_data = []
        frame_count = 0
        alive_count = self.alive.sum()
        
        start_time = time.time()
        
        while alive_count > 1 and frame_count < max_frames:
            # Update físico
            self._update_physics()
            
            # Detectar e processar colisões
            self._process_collisions()
            
            # Atualizar contagem de vivos
            alive_count = self.alive.sum()
            
            # Verificar se atingiu threshold para crescimento global
            self._check_global_growth(alive_count)
            
            # Salvar frame data
            frames_data.append({
                'frame': frame_count,
                'positions': self.positions.copy(),
                'hp': self.hp.copy(),
                'alive': self.alive.copy(),
                'alive_count': alive_count,
                'radius': self.radius.copy(),  # Incluir raios
                'kills': self.kills.copy()      # Incluir kills
            })
            
            frame_count += 1
            
            # Progress
            if frame_count % 100 == 0:
                elapsed = time.time() - start_time
                fps_actual = frame_count / elapsed
                print(f"   Frame {frame_count}/{max_frames} | "
                      f"Vivos: {alive_count} | "
                      f"FPS: {fps_actual:.1f}")
            
            # Extra progress when close to end
            if alive_count <= 10 and frame_count % 30 == 0:
                print(f"   🎯 Final battle: {alive_count} restantes (Frame {frame_count})")
        
        elapsed = time.time() - start_time
        print(f"✅ Simulação concluída em {elapsed:.1f}s ({frame_count} frames)")
        print(f"   FPS médio: {frame_count/elapsed:.1f}")
        
        return frames_data
    
    def _update_physics(self):
        """Atualiza posições e velocidades - física simples de bouncing"""
        # Simplesmente mover as bolas baseado na velocidade
        self.positions += self.velocities
        
        # Bounce nas bordas
        self._apply_boundaries()
        
        # Aplicar limite de velocidade máxima e mínima baseado no tamanho
        for i in range(self.n_particles):
            if not self.alive[i]:
                self.velocities[i] = 0
                continue
            
            speed = np.linalg.norm(self.velocities[i])
            size_factor = self.radius[i] / self.particle_radius
            
            # Bolas maiores têm velocidade máxima maior (proporcional ao tamanho)
            max_allowed_speed = self.max_speed * 1.5 * size_factor
            min_allowed_speed = self.max_speed * 0.3  # Mínimo de 30% da velocidade base
            
            if speed > max_allowed_speed:
                self.velocities[i] = (self.velocities[i] / speed) * max_allowed_speed
            elif speed < min_allowed_speed and speed > 0:
                # Bola muito lenta: dar um pequeno impulso
                self.velocities[i] = (self.velocities[i] / speed) * min_allowed_speed
    
    def _apply_boundaries(self):
        """Aplica colisões com bordas da arena - bouncing perfeito"""
        # Parede esquerda/direita
        hit_left = self.positions[:, 0] < self.particle_radius
        hit_right = self.positions[:, 0] > self.arena_width - self.particle_radius
        
        self.positions[hit_left, 0] = self.particle_radius
        self.positions[hit_right, 0] = self.arena_width - self.particle_radius
        self.velocities[hit_left | hit_right, 0] *= -self.bounce_damping  # Perfect bounce
        
        # Parede superior/inferior
        hit_top = self.positions[:, 1] < self.particle_radius
        hit_bottom = self.positions[:, 1] > self.arena_height - self.particle_radius
        
        self.positions[hit_top, 1] = self.particle_radius
        self.positions[hit_bottom, 1] = self.arena_height - self.particle_radius
        self.velocities[hit_top | hit_bottom, 1] *= -self.bounce_damping  # Perfect bounce
    
    def _process_collisions(self):
        """Detecta e processa colisões entre partículas"""
        # Usar spatial grid para otimização
        collisions = self._detect_collisions_optimized()
        
        if len(collisions) > 0:
            self._apply_collision_damage(collisions)
    
    def _detect_collisions_optimized(self):
        """Detecção de colisões otimizada com spatial hashing"""
        alive_idx = np.where(self.alive)[0]
        
        if len(alive_idx) < 2:
            return []
        
        # Spatial grid
        grid = {}
        
        for idx in alive_idx:
            x, y = self.positions[idx]
            grid_x = int(x / self.grid_size)
            grid_y = int(y / self.grid_size)
            key = (grid_x, grid_y)
            
            if key not in grid:
                grid[key] = []
            grid[key].append(idx)
        
        # Detectar colisões apenas em células vizinhas
        collisions = []
        checked = set()
        
        for cell_key, particles in grid.items():
            # Verificar dentro da célula
            for i in range(len(particles)):
                for j in range(i + 1, len(particles)):
                    idx1, idx2 = particles[i], particles[j]
                    
                    if (idx1, idx2) in checked:
                        continue
                    checked.add((idx1, idx2))
                    
                    # Distância considerando raios diferentes
                    collision_distance = self.radius[idx1] + self.radius[idx2]
                    dist = np.linalg.norm(
                        self.positions[idx1] - self.positions[idx2]
                    )
                    
                    if dist < collision_distance:
                        collisions.append((idx1, idx2, dist))
            
            # Verificar células vizinhas
            cx, cy = cell_key
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    
                    neighbor_key = (cx + dx, cy + dy)
                    if neighbor_key not in grid:
                        continue
                    
                    for idx1 in particles:
                        for idx2 in grid[neighbor_key]:
                            if (idx1, idx2) in checked or (idx2, idx1) in checked:
                                continue
                            checked.add((idx1, idx2))
                            
                            collision_distance = self.radius[idx1] + self.radius[idx2]
                            dist = np.linalg.norm(
                                self.positions[idx1] - self.positions[idx2]
                            )
                            
                            if dist < collision_distance:
                                collisions.append((idx1, idx2, dist))
        
        return collisions
    
    def _apply_collision_damage(self, collisions):
        """Aplica dano por colisões e bounce simples"""
        deaths_this_frame = []
        
        # Aumentar dano quando há poucos sobreviventes
        alive_count = self.alive.sum()
        damage_multiplier = 0.5
        
        for idx1, idx2, dist in collisions:
            # Calcular direção e força do bounce
            direction = self.positions[idx1] - self.positions[idx2]
            direction_norm = np.linalg.norm(direction)
            
            if direction_norm > 0:
                direction = direction / direction_norm
            else:
                direction = np.array([1.0, 0.0])
            
            # Velocidades relativas
            relative_velocity = self.velocities[idx1] - self.velocities[idx2]
            speed = np.linalg.norm(relative_velocity)
            
            # Dano baseado na velocidade e tamanho
            size_factor1 = self.radius[idx1] / self.particle_radius
            size_factor2 = self.radius[idx2] / self.particle_radius
            
            # Dano simples: maior bola causa mais dano
            damage1 = self.damage_base * size_factor2 * (1 + speed / self.max_speed) * damage_multiplier
            damage2 = self.damage_base * size_factor1 * (1 + speed / self.max_speed) * damage_multiplier
            
            # Aplicar dano
            self.hp[idx1] -= damage1 * self.strength[idx2]
            self.hp[idx2] -= damage2 * self.strength[idx1]
            
            # Verificar mortes
            died1 = self.hp[idx1] <= 0 and self.alive[idx1]
            died2 = self.hp[idx2] <= 0 and self.alive[idx2]
            
            if died1:
                deaths_this_frame.append((idx1, idx2))
            if died2:
                deaths_this_frame.append((idx2, idx1))
            
            # Bounce elástico simples - trocar componentes de velocidade
            # Calcular as novas velocidades após colisão elástica
            overlap = (self.radius[idx1] + self.radius[idx2]) - direction_norm
            if overlap > 0:
                # Separar as bolas para evitar sobreposição
                separation = direction * (overlap / 2 + 0.5)
                self.positions[idx1] += separation
                self.positions[idx2] -= separation
            
            # Bounce: refletir velocidades na direção da colisão
            v1_parallel = np.dot(self.velocities[idx1], direction) * direction
            v2_parallel = np.dot(self.velocities[idx2], direction) * direction
            
            # Trocar componentes paralelas (bounce perfeitamente elástico)
            self.velocities[idx1] = self.velocities[idx1] - v1_parallel + v2_parallel
            self.velocities[idx2] = self.velocities[idx2] - v2_parallel + v1_parallel
            
            # Transferência de energia baseada no tamanho e velocidade
            # Bola maior e mais rápida ganha speed, menor e mais lenta perde
            speed1_before = np.linalg.norm(self.velocities[idx1])
            speed2_before = np.linalg.norm(self.velocities[idx2])
            
            size_factor1 = self.radius[idx1] / self.particle_radius
            size_factor2 = self.radius[idx2] / self.particle_radius
            
            # Determinar quem é mais "dominante" (maior e mais rápido)
            dominance1 = size_factor1 * speed1_before
            dominance2 = size_factor2 * speed2_before
            
            if dominance1 > dominance2:
                # idx1 é dominante: ganha speed, idx2 perde
                boost_factor = 1.08  # 8% boost para o dominante
                loss_factor = 0.95   # 5% loss para o submisso
                if speed1_before > 0:
                    self.velocities[idx1] *= boost_factor
                if speed2_before > 0:
                    self.velocities[idx2] *= loss_factor
            elif dominance2 > dominance1:
                # idx2 é dominante: ganha speed, idx1 perde
                boost_factor = 1.08
                loss_factor = 0.95
                if speed2_before > 0:
                    self.velocities[idx2] *= boost_factor
                if speed1_before > 0:
                    self.velocities[idx1] *= loss_factor
            else:
                # Empate: ambos ganham um pouco
                self.velocities[idx1] *= 1.02
                self.velocities[idx2] *= 1.02
        
        # Processar kills (sem crescimento individual)
        for dead_idx, killer_idx in deaths_this_frame:
            if self.alive[killer_idx]:  # Apenas se o matador ainda está vivo
                # Aumentar contador de kills
                self.kills[killer_idx] += 1
                
                # Pequeno HP bonus
                hp_bonus = 10
                self.hp[killer_idx] = min(
                    self.hp[killer_idx] + hp_bonus,
                    self.hp_default * 2  # Max 2x HP inicial
                )
                
                # Aumentar força levemente
                self.strength[killer_idx] *= 1.01
        
        # Marcar mortos
        self.alive = self.hp > 0
    
    def _check_global_growth(self, alive_count):
        """Aumenta todas as bolas quando atinge certos thresholds"""
        for threshold in self.growth_thresholds:
            if alive_count <= threshold < self.last_growth_threshold:
                # Atingiu um novo threshold!
                growth_factor = 1.3  # Cresce 30%
                
                # Aumentar todas as bolas vivas
                alive_mask = self.alive
                old_radius = self.radius[alive_mask].copy()
                self.radius[alive_mask] *= growth_factor
                
                # Aumentar velocidade proporcionalmente ao crescimento
                alive_indices = np.where(alive_mask)[0]
                for idx in alive_indices:
                    speed = np.linalg.norm(self.velocities[idx])
                    if speed > 0:
                        # Aumentar velocidade em proporção ao crescimento
                        self.velocities[idx] *= growth_factor
                
                # Limitar tamanho máximo
                max_radius = self.particle_radius * 8
                self.radius[alive_mask] = np.minimum(
                    self.radius[alive_mask], 
                    max_radius
                )
                
                print(f"   🎯 Threshold atingido! {alive_count} restantes → Todas as bolas cresceram {(growth_factor-1)*100:.0f}%")
                
                # Atualizar último threshold
                self.last_growth_threshold = threshold
                break
    
    def get_winner(self):
        """Retorna o vencedor com estatísticas"""
        alive_indices = np.where(self.alive)[0]
        
        if len(alive_indices) == 0:
            winner_idx = 0  # Fallback
        else:
            winner_idx = alive_indices[0]
        
        winner = self.followers[winner_idx].copy()
        winner['kills'] = int(self.kills[winner_idx])
        winner['final_size'] = float(self.radius[winner_idx])
        winner['size_multiplier'] = float(self.radius[winner_idx] / self.particle_radius)
        
        return winner