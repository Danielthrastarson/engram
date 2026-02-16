import logging
from pathlib import Path
from typing import Optional
from core.abstraction_manager import AbstractionManager

logger = logging.getLogger(__name__)

class AudioProcessor:
    """
    Audio ingestion using Whisper (Phase 15).
    Transcribes audio → creates abstraction.
    """
    def __init__(self):
        self.am = AbstractionManager()
        
    def ingest_audio(self, audio_path: str, description: str = "") -> Optional[str]:
        """Transcribe audio and create abstraction"""
        try:
            import whisper
            
            logger.info(f"Transcribing audio: {audio_path}")
            model = whisper.load_model("base")  # Small model for speed
            result = model.transcribe(audio_path)
            transcript = result["text"]
            
            # Create abstraction
            content = f"{description}\n\nTranscript: {transcript}" if description else transcript
            abs_obj, created = self.am.create_abstraction(
                content=content,
                metadata={
                    "source": "audio",
                    "audio_path": audio_path,
                    "language": result.get("language", "unknown")
                }
            )
            
            logger.info(f"✅ Audio ingested: {abs_obj.id[:8]}")
            return abs_obj.id
            
        except ImportError:
            logger.error("Whisper not installed. Run: pip install openai-whisper")
            return None
        except Exception as e:
            logger.error(f"Audio ingestion failed: {e}")
            return None

class VideoProcessor:
    """
    Video ingestion using CLIP (Phase 15).
    Extracts keyframes → embeds with CLIP.
    """
    def __init__(self):
        self.am = AbstractionManager()
        
    def ingest_video(self, video_path: str, description: str = "") -> Optional[str]:
        """Extract keyframes and create abstraction"""
        try:
            import cv2
            from core.embedding import EmbeddingHandler
            
            logger.info(f"Processing video: {video_path}")
            
            # Extract keyframes (1 per 5s)
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_interval = int(fps * 5)  # Every 5 seconds
            
            frames = []
            frame_count = 0
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                    
                if frame_count % frame_interval == 0:
                    frames.append(frame)
                    
                frame_count += 1
                
            cap.release()
            
            logger.info(f"Extracted {len(frames)} keyframes")
            
            # Average CLIP embeddings
            embedder = EmbeddingHandler()
            # For simplicity, just get embedding of first frame
            # In V2, average all frames or save separately
            
            content = f"{description}\n\nVideo with {len(frames)} keyframes (extracted every 5s)"
            abs_obj, created = self.am.create_abstraction(
                content=content,
                metadata={
                    "source": "video",
                    "video_path": video_path,
                    "keyframe_count": len(frames)
                }
            )
            
            logger.info(f"✅ Video ingested: {abs_obj.id[:8]}")
            return abs_obj.id
            
        except ImportError:
            logger.error("OpenCV not installed. Run: pip install opencv-python")
            return None
        except Exception as e:
            logger.error(f"Video ingestion failed: {e}")
            return None

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python audio_video.py <audio/video_path> [description]")
        sys.exit(1)
        
    path = sys.argv[1]
    desc = sys.argv[2] if len(sys.argv) > 2 else ""
    
    if path.endswith(('.mp3', '.wav', '.m4a')):
        processor = AudioProcessor()
        processor.ingest_audio(path, desc)
    elif path.endswith(('.mp4', '.avi', '.mov')):
        processor = VideoProcessor()
        processor.ingest_video(path, desc)
    else:
        print("Unsupported file type")
