"""Audio input/output handler for voice interaction"""

import pyaudio
import numpy as np
import wave
import tempfile
import os
from typing import Optional, Callable
import threading
import queue
import time

from config.settings import (
    SAMPLE_RATE, CHUNK_SIZE, AUDIO_TIMEOUT, 
    SILENCE_THRESHOLD, DEBUG
)


class AudioHandler:
    """Handles microphone input and audio playback"""
    
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.recording = False
        self.audio_queue = queue.Queue()
        self.silence_counter = 0
        
    def list_devices(self):
        """List available audio input devices"""
        devices = []
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                devices.append({
                    'index': i,
                    'name': info['name'],
                    'channels': info['maxInputChannels']
                })
        return devices
    
    def start_stream(self, device_index: Optional[int] = None):
        """Start audio input stream"""
        if self.stream:
            self.stop_stream()
            
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=SAMPLE_RATE,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=CHUNK_SIZE,
            stream_callback=self._audio_callback
        )
        self.stream.start_stream()
        
    def stop_stream(self):
        """Stop audio input stream"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio stream"""
        if self.recording:
            self.audio_queue.put(in_data)
        return (in_data, pyaudio.paContinue)
    
    def record_until_silence(self, timeout: int = AUDIO_TIMEOUT) -> Optional[bytes]:
        """Record audio until silence is detected or timeout"""
        self.recording = True
        self.audio_queue = queue.Queue()
        frames = []
        silence_frames = 0
        max_silence_frames = int(SAMPLE_RATE / CHUNK_SIZE * 1.5)  # 1.5 seconds of silence
        start_time = time.time()
        
        try:
            while self.recording and (time.time() - start_time) < timeout:
                try:
                    data = self.audio_queue.get(timeout=0.1)
                    frames.append(data)
                    
                    # Check for silence
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    volume = np.abs(audio_data).mean()
                    
                    if volume < SILENCE_THRESHOLD:
                        silence_frames += 1
                        if silence_frames > max_silence_frames and len(frames) > 10:
                            break
                    else:
                        silence_frames = 0
                        
                except queue.Empty:
                    continue
                    
        finally:
            self.recording = False
            
        if frames:
            return b''.join(frames)
        return None
    
    def play_audio_file(self, filename: str):
        """Play an audio file"""
        wf = wave.open(filename, 'rb')
        
        stream = self.audio.open(
            format=self.audio.get_format_from_width(wf.getsampwidth()),
            channels=wf.getnchannels(),
            rate=wf.getframerate(),
            output=True
        )
        
        data = wf.readframes(CHUNK_SIZE)
        while data:
            stream.write(data)
            data = wf.readframes(CHUNK_SIZE)
            
        stream.stop_stream()
        stream.close()
        wf.close()
    
    def save_audio(self, audio_data: bytes, filename: Optional[str] = None) -> str:
        """Save audio data to WAV file"""
        if not filename:
            fd, filename = tempfile.mkstemp(suffix='.wav')
            os.close(fd)
            
        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_data)
        wf.close()
        
        return filename
    
    def cleanup(self):
        """Clean up audio resources"""
        self.stop_stream()
        self.audio.terminate()


class ContinuousAudioRecorder:
    """Continuous audio recording with callback support"""
    
    def __init__(self, callback: Callable[[bytes], None]):
        self.callback = callback
        self.audio_handler = AudioHandler()
        self.running = False
        self.thread = None
        
    def start(self, device_index: Optional[int] = None):
        """Start continuous recording"""
        self.running = True
        self.audio_handler.start_stream(device_index)
        self.thread = threading.Thread(target=self._recording_loop)
        self.thread.start()
        
    def stop(self):
        """Stop continuous recording"""
        self.running = False
        if self.thread:
            self.thread.join()
        self.audio_handler.cleanup()
        
    def _recording_loop(self):
        """Main recording loop"""
        while self.running:
            audio_data = self.audio_handler.record_until_silence()
            if audio_data and len(audio_data) > CHUNK_SIZE * 5:  # Minimum length
                self.callback(audio_data)