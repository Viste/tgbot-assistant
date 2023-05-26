import logging
import os

import aiofiles
import essentia.standard as es
import numpy as np
from aiogram import types, F, Router, flags

from main import paper
from tools.ai_tools import OpenAI
from tools.utils import config

logger = logging.getLogger("__name__")

router = Router()
router.message.filter(F.chat.type.in_({'private'}))
openai = OpenAI()


async def process_audio_file(file_path):
    # Load the audio file
    loader = es.MonoLoader(filename=file_path)
    audio = loader()

    # Convert mono signal to stereo
    audio_stereo = np.array([audio, audio]).T

    # Functions for converting seconds to time format and adjusting BPM
    def seconds_to_time(seconds):
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f'{minutes}:{seconds}'

    def adjust_bpm(bitrate):
        if 85 <= bitrate <= 90:
            bitrate = round(bitrate)
            bitrate *= 2
        return bitrate

    # Calculate track duration
    track_duration = len(audio) / loader.paramValue('sampleRate')
    track_duration_str = seconds_to_time(track_duration)

    # Initialize algorithms
    window_algo = es.Windowing(type='hann')
    spectrum_algo = es.Spectrum()
    peaks_algo = es.SpectralPeaks()

    pitch_algo = es.PitchYinFFT(frameSize=2048)
    tempo_algo = es.RhythmExtractor2013()
    mfcc_algo = es.MFCC()
    chroma_algo = es.HPCP()
    loudness_algo = es.Loudness()
    key_algo = es.KeyExtractor()
    spectral_contrast_algo = es.SpectralContrast(frameSize=2048)
    dissonance_algo = es.Dissonance()
    dynamic_complexity_algo = es.DynamicComplexity()
    lufs_algo = es.LoudnessEBUR128()

    # Calculate features
    pitch, pitch_confidence = pitch_algo(audio)
    bpm, beats, beats_confidence, _, _ = tempo_algo(audio)
    bpm = adjust_bpm(bpm)
    mfccs, _ = mfcc_algo(audio)

    chroma_values = []
    spectral_contrast_values = []
    dissonance_values = []
    for frame in es.FrameGenerator(audio, frameSize=2048, hopSize=1024):
        windowed_frame = window_algo(frame)
        spectrum = spectrum_algo(windowed_frame)
        frequencies, magnitudes = peaks_algo(spectrum)
        chroma = chroma_algo(frequencies, magnitudes)
        spectral_contrast = spectral_contrast_algo(spectrum)
        dissonance = dissonance_algo(frequencies, magnitudes)
        chroma_values.append(chroma)
        spectral_contrast_values.append(spectral_contrast)
        dissonance_values.append(dissonance)

    loudness = loudness_algo(audio)
    key, scale, key_strength = key_algo(audio)
    dynamic_complexity, loudness_range = dynamic_complexity_algo(audio)
    integrated_loudness, loudness_range, momentary_loudness, short_term_loudness = lufs_algo(audio_stereo)
    lufs_values = momentary_loudness

    # Compress data
    def compress_data(data):
        return [np.mean(data), np.median(data), np.min(data), np.max(data)]

    chroma_values = compress_data(chroma_values)
    spectral_contrast_values = compress_data(spectral_contrast_values)
    dissonance_values = compress_data(dissonance_values)
    lufs_compressed = compress_data(lufs_values)
    loudness_range_compressed = compress_data(loudness_range)

    # Store the results in a string
    result = f"Results for file: {file_path}\n"
    result += f"Track duration: {track_duration_str}\n"
    result += f"Pitch: {pitch}, Confidence: {pitch_confidence}\n"
    result += f"Tempo: {bpm}, Beats: {beats}\n"
    result += f"MFCCs: {mfccs}\n"
    result += f"Chroma: {chroma_values}\n"
    result += f"Loudness: {loudness}\n"
    result += f"Key: {key}, Scale: {scale}, Strength: {key_strength}\n"
    result += f"Spectral Contrast: {spectral_contrast_values}\n"
    result += f"Dissonance: {dissonance_values}\n"
    result += f"Dynamic Complexity: {dynamic_complexity}\n"
    result += f"LUFS: {lufs_compressed}\n"
    result += f"Loudness Range: {loudness_range_compressed}\n"

    return result


@flags.chat_action("typing")
@router.message(F.from_user.id.in_({config.test_users}), F.content_type.in_({'audio'}))
async def handle_audio(message: types.Message):
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        audio_file = await paper.download_file_by_id(message.audio.file_id)
        file_path = f"{message.audio.file_id}.ogg"
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(await audio_file.read())

        result = await process_audio_file(file_path)
        os.remove(file_path)
        replay_text, total_tokens = await openai.get_resp_listen(result, uid)
