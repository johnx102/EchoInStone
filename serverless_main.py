# serverless_main.py

import os
import logging
from functools import lru_cache
from EchoInStone.utils import configure_logging
from EchoInStone.capture.downloader_factory import get_downloader
from EchoInStone.processing import AudioProcessingOrchestrator, WhisperAudioTranscriber, PyannoteDiarizer, SpeakerAligner
from EchoInStone.utils import DataSaver

# Global instances for reuse across invocations
_transcriber = None
_diarizer = None

@lru_cache(maxsize=1)
def get_transcriber():
    """Lazy-load and cache transcriber to avoid cold start penalties"""
    global _transcriber
    if _transcriber is None:
        logging.info("Loading Whisper model (cold start)...")
        _transcriber = WhisperAudioTranscriber()
    return _transcriber

@lru_cache(maxsize=1) 
def get_diarizer():
    """Lazy-load and cache diarizer to avoid cold start penalties"""
    global _diarizer
    if _diarizer is None:
        logging.info("Loading Pyannote model (cold start)...")
        _diarizer = PyannoteDiarizer()
    return _diarizer

def serverless_handler(event, context=None):
    """
    Serverless function handler - optimized for platforms like:
    - RunPod Serverless
    - Modal
    - AWS Lambda (with container support)
    - Google Cloud Run
    """
    configure_logging(logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Extract parameters from event
    echo_input = event.get('url') or event.get('echo_input')
    output_dir = event.get('output_dir', '/tmp/results')
    transcription_output = event.get('output_file', 'transcription.json')
    
    if not echo_input:
        return {"error": "Missing 'url' parameter"}
    
    try:
        # Initialize components (reuse cached models)
        downloader = get_downloader(echo_input, output_dir)
        transcriber = get_transcriber()  # Cached
        diarizer = get_diarizer()       # Cached
        aligner = SpeakerAligner()      # Lightweight
        data_saver = DataSaver(output_dir=output_dir)
        
        # Create orchestrator
        orchestrator = AudioProcessingOrchestrator(
            downloader, transcriber, diarizer, aligner, data_saver
        )
        
        # Process audio
        logger.info(f"Processing: {echo_input}")
        speaker_transcriptions = orchestrator.extract_and_transcribe(echo_input)
        
        if speaker_transcriptions:
            # Save results
            output_path = os.path.join(output_dir, transcription_output)
            data_saver.save_data(transcription_output, speaker_transcriptions)
            
            return {
                "success": True,
                "transcription": speaker_transcriptions,
                "output_file": output_path,
                "speaker_count": len(set(t[0] for t in speaker_transcriptions))
            }
        else:
            return {"error": "Transcription failed"}
            
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        return {"error": str(e)}

# Entry point for serverless platforms
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python serverless_main.py <url>")
        sys.exit(1)
    
    event = {"url": sys.argv[1]}
    result = serverless_handler(event)
    print(result)
