"""
FFmpeg utilities and setup for Discord Music Bot.

This module provides utilities for checking and configuring FFmpeg,
which is required for audio processing in discord.py voice functionality.
"""

import os
import sys
import shutil
import logging
import subprocess
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class FFmpegManager:
    """Manages FFmpeg installation and configuration."""
    
    def __init__(self):
        self.ffmpeg_path: Optional[str] = None
        self.ffprobe_path: Optional[str] = None
        self._checked = False
    
    def check_ffmpeg_installation(self) -> bool:
        """
        Check if FFmpeg is properly installed and accessible.
        
        Returns:
            True if FFmpeg is available, False otherwise.
        """
        if self._checked:
            return self.ffmpeg_path is not None
        
        # Check for FFmpeg executable
        self.ffmpeg_path = shutil.which('ffmpeg')
        self.ffprobe_path = shutil.which('ffprobe')
        
        if self.ffmpeg_path:
            logger.info(f"FFmpeg found at: {self.ffmpeg_path}")
            if self.ffprobe_path:
                logger.info(f"FFprobe found at: {self.ffprobe_path}")
            self._checked = True
            return True
        else:
            logger.warning("FFmpeg not found in PATH")
            self._checked = True
            return False
    
    def get_ffmpeg_version(self) -> Optional[str]:
        """
        Get the version of the installed FFmpeg.
        
        Returns:
            Version string if available, None otherwise.
        """
        if not self.check_ffmpeg_installation():
            return None
        
        try:
            result = subprocess.run(
                [self.ffmpeg_path, '-version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Extract version from first line
                first_line = result.stdout.split('\n')[0]
                if 'version' in first_line:
                    version = first_line.split('version')[1].split()[0]
                    return version.strip()
            
        except (subprocess.TimeoutExpired, FileNotFoundError, IndexError) as e:
            logger.error(f"Error getting FFmpeg version: {e}")
        
        return None
    
    def get_installation_guide(self) -> Dict[str, str]:
        """
        Get platform-specific installation instructions for FFmpeg.
        
        Returns:
            Dictionary with installation instructions for different platforms.
        """
        return {
            "Windows": (
                "1. Download FFmpeg from https://ffmpeg.org/download.html#build-windows\n"
                "2. Extract the archive to a folder (e.g., C:\\ffmpeg)\n"
                "3. Add the 'bin' folder to your system PATH\n"
                "4. Restart your command prompt/IDE\n"
                "Alternative: Use Chocolatey: choco install ffmpeg"
            ),
            "macOS": (
                "1. Install Homebrew: https://brew.sh/\n"
                "2. Run: brew install ffmpeg\n"
                "Alternative: Use MacPorts: sudo port install ffmpeg"
            ),
            "Linux": (
                "Ubuntu/Debian: sudo apt update && sudo apt install ffmpeg\n"
                "CentOS/RHEL: sudo yum install ffmpeg\n"
                "Fedora: sudo dnf install ffmpeg\n"
                "Arch: sudo pacman -S ffmpeg"
            )
        }
    
    def print_installation_help(self) -> None:
        """Print helpful installation instructions based on the current platform."""
        if self.check_ffmpeg_installation():
            version = self.get_ffmpeg_version()
            print(f"✅ FFmpeg is properly installed (version: {version or 'unknown'})")
            return
        
        print("❌ FFmpeg is not installed or not found in PATH")
        print("\nFFmpeg is required for voice functionality in this Discord bot.")
        print("Please install FFmpeg using the instructions below:\n")
        
        guides = self.get_installation_guide()
        
        # Detect platform
        platform = sys.platform
        if platform.startswith('win'):
            current_platform = "Windows"
        elif platform == 'darwin':
            current_platform = "macOS"
        else:
            current_platform = "Linux"
        
        print(f"Instructions for {current_platform}:")
        print(guides[current_platform])
        
        print("\nAfter installation, restart your terminal/IDE and try running the bot again.")
    
    def get_optimal_ffmpeg_options(self) -> Dict[str, Dict[str, str]]:
        """
        Get optimized FFmpeg options for Discord audio streaming.
        
        Returns:
            Dictionary with PCM and Opus options for FFmpeg.
        """
        return {
            'pcm': {
                'before_options': (
                    '-reconnect 1 '
                    '-reconnect_streamed 1 '
                    '-reconnect_delay_max 5 '
                    '-probesize 32 '
                    '-fflags +discardcorrupt'
                ),
                'options': '-vn'
            },
            'opus': {
                'before_options': (
                    '-reconnect 1 '
                    '-reconnect_streamed 1 '
                    '-reconnect_delay_max 5 '
                    '-probesize 32 '
                    '-fflags +discardcorrupt'
                ),
                'options': '-vn -c:a libopus -b:a 128k -ar 48000 -ac 2'
            }
        }
    
    def test_discord_audio_conversion(self, test_url: str = "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav") -> Dict[str, bool]:
        """
        Test FFmpeg's ability to convert audio for Discord (both PCM and Opus).
        
        Args:
            test_url: URL to test audio processing with.
            
        Returns:
            Dictionary with test results for PCM and Opus.
        """
        if not self.check_ffmpeg_installation():
            return {'pcm': False, 'opus': False}
        
        results = {}
        options = self.get_optimal_ffmpeg_options()
        
        # Test PCM conversion
        try:
            pcm_cmd = [
                self.ffmpeg_path,
                *options['pcm']['before_options'].split(),
                '-i', test_url,
                *options['pcm']['options'].split(),
                '-t', '1',  # Process only 1 second
                '-f', 'null',
                '-'
            ]
            result = subprocess.run(pcm_cmd, capture_output=True, timeout=15)
            results['pcm'] = result.returncode == 0
            if results['pcm']:
                logger.info("FFmpeg PCM conversion test passed")
            else:
                logger.warning(f"FFmpeg PCM test failed: {result.stderr.decode()}")
        except Exception as e:
            logger.error(f"FFmpeg PCM test error: {e}")
            results['pcm'] = False
        
        # Test Opus conversion
        try:
            opus_cmd = [
                self.ffmpeg_path,
                *options['opus']['before_options'].split(),
                '-i', test_url,
                *options['opus']['options'].split(),
                '-t', '1',  # Process only 1 second
                '-f', 'null',
                '-'
            ]
            result = subprocess.run(opus_cmd, capture_output=True, timeout=15)
            results['opus'] = result.returncode == 0
            if results['opus']:
                logger.info("FFmpeg Opus conversion test passed")
            else:
                logger.warning(f"FFmpeg Opus test failed: {result.stderr.decode()}")
        except Exception as e:
            logger.error(f"FFmpeg Opus test error: {e}")
            results['opus'] = False
        
        return results
    
    def test_audio_processing(self, test_url: str = "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav") -> bool:
        """
        Test FFmpeg's ability to process audio from a URL.
        
        Args:
            test_url: URL to test audio processing with.
            
        Returns:
            True if test succeeds, False otherwise.
        """
        if not self.check_ffmpeg_installation():
            return False
        
        try:
            # Test command: ffmpeg -i <url> -f null -
            result = subprocess.run([
                self.ffmpeg_path,
                '-i', test_url,
                '-t', '1',  # Process only 1 second
                '-f', 'null',
                '-'
            ], capture_output=True, timeout=15)
            
            success = result.returncode == 0
            if success:
                logger.info("FFmpeg audio processing test passed")
            else:
                logger.warning(f"FFmpeg test failed: {result.stderr.decode()}")
            
            return success
            
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.error(f"FFmpeg test error: {e}")
            return False


# Global FFmpeg manager instance
ffmpeg_manager = FFmpegManager()


def check_ffmpeg_requirements() -> bool:
    """
    Check if all FFmpeg requirements are met for the music bot.
    
    Returns:
        True if requirements are met, False otherwise.
    """
    return ffmpeg_manager.check_ffmpeg_installation()


def setup_ffmpeg() -> bool:
    """
    Set up FFmpeg for the music bot.
    
    Returns:
        True if setup successful, False otherwise.
    """
    if not ffmpeg_manager.check_ffmpeg_installation():
        ffmpeg_manager.print_installation_help()
        return False
    
    # Test basic functionality
    logger.info("Testing FFmpeg functionality...")
    version = ffmpeg_manager.get_ffmpeg_version()
    if version:
        logger.info(f"FFmpeg version: {version}")
    
    # Test Discord audio conversion capabilities
    logger.info("Testing Discord audio conversion...")
    test_results = ffmpeg_manager.test_discord_audio_conversion()
    
    if test_results['opus']:
        logger.info("✅ Opus audio conversion supported - optimal quality")
    elif test_results['pcm']:
        logger.info("✅ PCM audio conversion supported - fallback mode")
    else:
        logger.warning("⚠️ Audio conversion tests failed - audio quality may be poor")
    
    # Log optimal options
    options = ffmpeg_manager.get_optimal_ffmpeg_options()
    logger.info(f"Available FFmpeg options: PCM and Opus")
    
    return True


def get_ffmpeg_executable() -> Optional[str]:
    """Get the path to the FFmpeg executable."""
    ffmpeg_manager.check_ffmpeg_installation()
    return ffmpeg_manager.ffmpeg_path


if __name__ == "__main__":
    # Command-line interface for FFmpeg checking
    print("🎵 Discord Music Bot - FFmpeg Checker")
    print("=" * 40)
    
    manager = FFmpegManager()
    manager.print_installation_help()
    
    if manager.check_ffmpeg_installation():
        print(f"\n📍 FFmpeg location: {manager.ffmpeg_path}")
        
        version = manager.get_ffmpeg_version()
        if version:
            print(f"📦 Version: {version}")
        
        print("\n🧪 Testing Discord audio conversion...")
        test_results = manager.test_discord_audio_conversion()
        
        if test_results['opus']:
            print("✅ Opus audio conversion test passed! (Optimal)")
        elif test_results['pcm']:
            print("✅ PCM audio conversion test passed! (Fallback)")
        else:
            print("❌ Both audio conversion tests failed!")
            print("   The bot may experience audio quality issues.")
        
        # Also test basic processing
        basic_test = manager.test_audio_processing()
        if basic_test:
            print("✅ Basic audio processing test passed!")
        else:
            print("❌ Basic audio processing test failed!")
    
    print("\n" + "=" * 40)
