import logging

import essentia.standard as es
import numpy as np
import openai
import tiktoken

from tools.utils import config

openai.api_key = config.api_key_listen
logger = logging.getLogger("__name__")

args = {
    "temperature": 0.15,
    "max_tokens": 400,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0.8,
    "stop": None
}


class Audio:
    def __init__(self):
        super().__init__()
        self.frameSize = 2048
        self.hopSize = 1024
        self.delim = 60

    async def process_audio_file(self, file_path):
        loader = es.MonoLoader(filename=file_path)
        audio = loader()

        audio_stereo = np.array([audio, audio]).T

        def seconds_to_time(seconds):
            minutes = int(seconds // self.delim)
            seconds = int(seconds % self.delim)
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

        pitch_algo = es.PitchYinFFT(frameSize=self.frameSize)
        tempo_algo = es.RhythmExtractor2013()
        mfcc_algo = es.MFCC()
        chroma_algo = es.HPCP()
        loudness_algo = es.Loudness()
        key_algo = es.KeyExtractor()
        spectral_contrast_algo = es.SpectralContrast(frameSize=self.frameSize)
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
        for frame in es.FrameGenerator(audio, frameSize=self.frameSize, hopSize=self.hopSize):
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
        result = f"Results for file: {file_path} "
        result += f"Track duration: {track_duration_str} "
        result += f"Pitch: {pitch}, Confidence: {pitch_confidence} "
        result += f"Tempo: {bpm}, Beats: {beats} "
        result += f"MFCCs: {mfccs} "
        result += f"Chroma: {chroma_values} "
        result += f"Loudness: {loudness} "
        result += f"Key: {key}, Scale: {scale}, Strength: {key_strength} "
        result += f"Spectral Contrast: {spectral_contrast_values} "
        result += f"Dissonance: {dissonance_values} "
        result += f"Dynamic Complexity: {dynamic_complexity} "
        result += f"LUFS: {lufs_compressed} "
        result += f"Loudness Range: {loudness_range_compressed} "

        return result


class OpenAIListener:
    max_retries: int

    def __init__(self):
        super().__init__()
        self.model = "gpt-4"
        self.max_retries = 10
        self.max_tokens = 8192
        self.config_tokens = 400
        self.max_history_size = 15
        self.n_choices = 1
        self.retries = 0
        self.show_tokens = False
        self.listen_content = "decode: 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"
        
    async def _query_gpt_listen(self, query):
        while self.retries < self.max_retries:
            try:
                return await openai.ChatCompletion.acreate(model=self.model, messages=[{"role": "system", "content": self.listen_content}, {"role": "user", "content": query}],
                                                           **args)

            except openai.error.RateLimitError as e:
                self.retries += 10
                logging.info("Dialog From Ratelim: %s", query)
                if self.retries == self.max_retries:
                    return f'⚠️OpenAI: Превышены лимиты ⚠️\n{str(e)}'

            except openai.error.InvalidRequestError as er:
                self.retries += 10
                logging.info("Dialog From bad req: %s", query)
                if self.retries == self.max_retries:
                    return f'⚠️OpenAI: кривой запрос ⚠️\n{str(er)}'

            except Exception as err:
                self.retries += 10
                logging.info("Dialog From custom exception: %s", query)
                if self.retries == self.max_retries:
                    return f'⚠️Ошибочка вышла ⚠️\n{str(err)}', err

    async def get_resp_listen(self, query: str) -> tuple[str, str]:
        response = await self._query_gpt_listen(query)
        answer = ''

        if response.choices and len(response.choices) > 1 and self.n_choices > 1:
            for index, choice in enumerate(response.choices):
                content = choice['message']['content'].strip()
                answer += f'{index + 1}\u20e3\n'
                answer += content
                answer += '\n\n'
        elif response.choices and len(response.choices) >= 0:
            answer = response.choices[0]['message']['content'].strip()
        else:
            answer = response.choices[0]['message']['content'].strip()

        total_tokens = response.usage['total_tokens'] if response.usage else 0
        if response.usage and self.show_tokens:
            answer += "\n\n---\n" \
                      f"💰 Использовано Токенов: {str(response.usage['total_tokens'])}" \
                      f" ({str(response.usage['prompt_tokens'])} prompt," \
                      f" {str(response.usage['completion_tokens'])} completion)"

        return answer, total_tokens

    def _count_listen_tokens(self, messages) -> int:
        try:
            model = self.model
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("gpt-4")

        tokens_per_message = 3
        tokens_per_name = 1

        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name
        num_tokens += 3
        return num_tokens
