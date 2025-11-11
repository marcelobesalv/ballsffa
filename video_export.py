"""
Módulo de exportação e pós-processamento de vídeo
"""

from moviepy.editor import VideoFileClip, concatenate_videoclips, TextClip, CompositeVideoClip
import os


class VideoExporter:
    """Gerencia exportação final do vídeo"""
    
    def __init__(self):
        pass
    
    def add_intro_outro(self, video_path, intro_text=None, outro_text=None, output_path=None):
        """Adiciona intro e outro ao vídeo"""
        
        if output_path is None:
            base, ext = os.path.splitext(video_path)
            output_path = f"{base}_final{ext}"
        
        print("🎞️  Processando vídeo com MoviePy...")
        
        clips = []
        
        # Intro
        if intro_text:
            intro_clip = TextClip(
                intro_text,
                fontsize=70,
                color='white',
                bg_color='black',
                size=(1080, 1920),
                method='caption'
            ).set_duration(2)
            clips.append(intro_clip)
        
        # Vídeo principal
        main_clip = VideoFileClip(video_path)
        clips.append(main_clip)
        
        # Outro
        if outro_text:
            outro_clip = TextClip(
                outro_text,
                fontsize=70,
                color='white',
                bg_color='black',
                size=(1080, 1920),
                method='caption'
            ).set_duration(2)
            clips.append(outro_clip)
        
        # Concatenar
        final_clip = concatenate_videoclips(clips, method="compose")
        
        # Exportar
        final_clip.write_videofile(
            output_path,
            codec='libx264',
            audio=False,
            fps=30,
            preset='medium',
            threads=4
        )
        
        # Cleanup
        main_clip.close()
        final_clip.close()
        
        print(f"✅ Vídeo final exportado: {output_path}")
        
        return output_path
    
    def compress_for_instagram(self, video_path, output_path=None):
        """Comprime vídeo para especificações do Instagram"""
        
        if output_path is None:
            base, ext = os.path.splitext(video_path)
            output_path = f"{base}_compressed{ext}"
        
        print("📦 Comprimindo vídeo para Instagram...")
        
        clip = VideoFileClip(video_path)
        
        # Garantir duração máxima (60s para Reels)
        if clip.duration > 60:
            clip = clip.subclip(0, 60)
        
        # Exportar com configurações do Instagram
        clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac' if clip.audio else None,
            fps=30,
            bitrate='5000k',
            preset='medium',
            threads=4
        )
        
        clip.close()
        
        print(f"✅ Vídeo comprimido: {output_path}")
        
        return output_path
    
    def get_video_info(self, video_path):
        """Retorna informações do vídeo"""
        clip = VideoFileClip(video_path)
        
        info = {
            'duration': clip.duration,
            'fps': clip.fps,
            'size': clip.size,
            'has_audio': clip.audio is not None
        }
        
        clip.close()
        
        return info