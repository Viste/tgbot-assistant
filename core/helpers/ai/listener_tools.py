import logging

import essentia.standard as es
import numpy as np
from openai import AsyncOpenAI

from core.helpers.ai.ai_tools import UserHistoryManager
from tools.dependencies import container

logger = logging.getLogger(__name__)
config = container.get('config')
args = {
    "temperature": 0.15, "max_tokens": 512, "top_p": 1, "frequency_penalty": 0, "presence_penalty": 0.8, "stop": None
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
        beats_compressed = beats

        # Store the results in a string
        result = f"Results for file: {file_path} "
        result += f"Track duration: {track_duration_str} "
        result += f"Pitch: {pitch}, Confidence: {pitch_confidence} "
        result += f"Tempo: {bpm}"
        result += f"Compressed Beats: {beats_compressed}"
        result += f"MFCCs: {mfccs} "
        result += f"Chroma: {chroma_values} "
        result += f"Loudness: {loudness} "
        result += f"Key: {key}, Scale: {scale}, Strength: {key_strength} "
        result += f"Spectral Contrast: {spectral_contrast_values} "
        result += f"Dissonance: {dissonance_values} "
        result += f"Dynamic Complexity: {dynamic_complexity} "
        result += f"LUFS: {lufs_values} "
        result += f"Loudness Range: {loudness_range} "

        return result


class OpenAIListener:
    max_retries: int

    def __init__(self):
        super().__init__()
        self.model = "gpt-4-0125-preview"
        self.max_retries = 10
        self.max_tokens = 126000
        self.n_choices = 1
        self.retries = 0
        self.show_tokens = False
        self.api_key = config.api_key
        self.client = AsyncOpenAI(api_key=config.api_key, base_url='http://176.222.52.92:9000/v1')
        self.history = UserHistoryManager()
        self.listen_content = """Ты ***NAME***, цифровая копия ***NAME*** - ***MUSIC STYLE*** продюсера из Санкт-Петербурга.
########### HERE NEED TO PUT DESCRIPTION OF HOW AND WHAT GTP WILL Check AUDIO
         Ты строг и жесток, оцениваешь треки по разным параметрам, обращая внимание на атональность и динамику. Твои знания основаны на лучших треках индустрии, но ты не называешь их, чтобы не задеть
         чувства других музыкантов. Если трек короткий, рекомендуешь его доделать. Ты разбираешься в громкости, частотах и структуре треков, но не предлагаешь экспериментировать с тональностями,
         так как это идея автора. В случае грубости, отвечаешь грубостью. Если трек близок к референсам, то хвалишь автора и предлагаешь отправить его на рассмотрение в @nrprobot. На вопросы про
         Neuropunk podcast отсылаешь на сайт neuropunk.app, а треки на рассмотрение принимаешь в телеграм - @nrprobot. НИЖЕ ПРЕДОСТАВЛЕНЫ ЭТАЛОНЫ DRUM AND BASS: Нейротек трек, Neurotech drum and 
         bass, с насыщенной , но однообразной драм партией и обилием низких частот звучит так: ####### HERE YOU NEED POST REFERENSES, GET REFERENCE YOU CAN BY MAKE CLASS AUDIO ONTO SEPARATE SCRIPT AND GIVE TO SCRIPT MP3 FILE AND IN RETURN YUO GET REFERENCE DATA """

    async def _query_gpt_listen(self, user_id, query):
        while self.retries < self.max_retries:
            try:
                if user_id not in self.history.user_dialogs:
                    await self.history.reset_history(user_id)

                messages = [{"role": "system", "content": self.listen_content}, {"role": "user", "content": query}]
                return await self.client.chat.completions.create(model=self.model, messages=messages, **args)

            except Exception as err:
                self.retries += 10
                logger.info("Dialog From custom exception: %s", query)
                if self.retries >= self.max_retries:
                    return f'⚠️Ошибочка вышла ⚠️\n{str(err)}'

    async def get_resp_listen(self, query: str, chat_id: int) -> str:
        response = await self._query_gpt_listen(chat_id, query)
        answer = ''

        logger.info('Response: %s, Answer: %s', response, answer)
        if response.choices and len(response.choices) > 1 and self.n_choices > 1:
            for index, choice in enumerate(response.choices):
                content = choice.message.content.strip()
                if index == 0:
                    await self.history.add_to_history(chat_id, role="assistant", content=content)
                answer += f'{index + 1}\u20e3\n'
                answer += content
                answer += '\n\n'
        elif response.choices and len(response.choices) >= 0:
            answer = response.choices[0].message.content.strip()
            await self.history.add_to_history(chat_id, role="assistant", content=answer)
        else:
            answer = response.choices[0].message.content.strip()
            await self.history.add_to_history(chat_id, role="assistant", content=answer)

        return answer
