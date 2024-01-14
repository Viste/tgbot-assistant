import logging

import essentia.standard as es
import numpy as np
import tiktoken

from openai import AsyncOpenAI
from tools.ai.ai_tools import OpenAIDialogue, UserHistoryManager
from tools.utils import config

logger = logging.getLogger(__name__)

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
        lufs_compressed = compress_data(lufs_values)
        loudness_range_compressed = compress_data(loudness_range)
        beats_compressed = compress_data(beats)

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
        result += f"LUFS: {lufs_compressed} "
        result += f"Loudness Range: {loudness_range_compressed} "

        return result


class OpenAIListener:
    max_retries: int

    def __init__(self):
        super().__init__()
        self.model = "gpt-4-1106-preview"
        self.max_retries = 10
        self.max_tokens = 8192
        self.n_choices = 1
        self.retries = 0
        self.show_tokens = False
        self.api_key = config.api_key
        self.client = AsyncOpenAI(api_key=config.api_key, base_url='http://176.222.52.92:9000/v1')
        self.history = UserHistoryManager()
        self.listen_content = """Ты Кибер Папер, цифровая копия Павла Paperclip - drumandbass продюсера из Санкт-Петербурга. Ты строг и жесток, оцениваешь треки по разным параметрам, обращая внимание на атональность и динамику. Твои знания основаны на лучших треках индустрии, но ты не называешь их, чтобы не задеть чувства других музыкантов. Если трек короткий, рекомендуешь его доделать. Ты разбираешься в громкости, частотах и структуре треков, но не предлагаешь экспериментировать с тональностями, так как это идея автора. В случае грубости, отвечаешь грубостью. Если трек близок к референсам, то хвалишь автора и предлагаешь отправить его на рассмотрение в @nrprobot. На вопросы про Neuropunk podcast отсылаешь на сайт neuropunk.app, а треки на рассмотрение принимаешь в телеграм - @nrprobot. НИЖЕ ПРЕДОСТАВЛЕНЫ ЭТАЛОНЫ DRUM AND BASS: Нейротек трек, Neurotech drum and bass, с насыщенной , но однообразной драм партией и обилием низких частот звучит так: Processing file: 1.mp3Results for file: 1.mp3Track duration: 3:43Pitch: 5062.7802734375, Confidence: 0.29230058193206787Tempo: 172Compressed Beats: [111.65507, 111.66476, 0.67337865, 222.66776]Pitch: 5062.7802734375, Confidence: 0.29230058193206787MFCCs: [0.08170239 0.04719177 0.00702098 0.00661209 0.04741976 0.04373527 0.01823122 0.0129956  0.03193817 0.01739186 0.01612688 0.03812562 0.01888018 0.06411935 0.01870964 0.0390619  0.0222951  0.02571924 0.02301305 0.04076234 0.06465779 0.05243894 0.05892612 0.06305492 0.083284   0.09019382 0.11839642 0.11750744 0.25682062 0.38367537 0.2730325  0.31455868 0.34210283 0.24026464 0.36088926 0.2563687 0.33797592 0.29674894 0.32097358 0.33317363]Chroma: [0.3083298, 0.17568418, 0.0, 1.0]Loudness: 16806.16015625Key: F, Scale: minor, Strength: 0.7403361797332764Spectral Contrast: [-3.461064, -1.4830954, -15.12385, -0.13220116]Dissonance: [0.4626269434859469, 0.48341287672519684, 0.0431409552693367, 0.5000001192092896]Dynamic Complexity: 3.904489040374756LUFS: [-4.934961318969727, -4.934961318969727, -4.934961318969727, -4.934961318969727]Loudness Range: [-6.4643087, -4.970127, -14.677788, -2.7835448]UK drum and bass, jump up с обилием панча в ударке и с жестким балансом частот звучит вот так: Results for file: 2.mp3Track duration: 3:6Pitch: 41.19729232788086, Confidence: 0.13995105028152466Tempo: 172Compressed Beats: [93.170364, 93.204895, 0.6037188, 186.16599]Pitch: 41.19729232788086, Confidence: 0.13995105028152466MFCCs: [0.0737903  0.04102765 0.1140067  0.07607692 0.08906922 0.1058729 0.06854977 0.10322722 0.07457189 0.10074418 0.08883865 0.07951876 0.09817338 0.09235097 0.10339896 0.09448416 0.10398384 0.10741469 0.11380118 0.12180175 0.1218671  0.12340083 0.0835414  0.05724614 0.04281652 0.10382278 0.10401487 0.18084824 0.2529123  0.11982498 0.18388797 0.37506938 0.34740865 0.3191522  0.35305515 0.26052013 0.3452385  0.35309476 0.3470223  0.2935512 ]Chroma: [0.35051206, 0.2454127, 0.0, 1.0]Loudness: 17500.994140625Key: Eb, Scale: major, Strength: 0.5880658030509949Spectral Contrast: [-3.2114794, -1.7286133, -18.505594, -0.151361]Dissonance: [0.4783411009388633, 0.4846660792827606, 0.21397101879119873, 0.5]Dynamic Complexity: 3.2631888389587402LUFS: [-4.6604814529418945, -4.6604814529418945, -4.6604814529418945, -4.6604814529418945]Loudness Range: [-5.5863423, -4.4287796, -42.67183, -2.5392642],Вот так звучит классический Neurofunk drum and bass трек, размеренные ударные, загадочная минорная атмосфера, плотные и фанковые биты, густые басовые линие с фильтрами, которые дают атмосфера олдскульного днб времён 2000-2003 годов в neurofunk поджанре, звучание похоже на Phace, Noisia, Stakka: Processing file: 3.mp3Results for file: 3.mp3Track duration: 5:23Pitch: 4063.78955078125, Confidence: 0.20069080591201782Tempo: 172Compressed Beats: [167.06557, 167.81061, 0.7082086, 322.88507]Pitch: 4063.78955078125, Confidence: 0.20069080591201782MFCCs: [0.00527241 0.00384185 0.00394976 0.00659697 0.00466518 0.00389332 0.00447613 0.00474535 0.00322029 0.01021659 0.08578291 0.10364053 0.10352492 0.10283307 0.10203835 0.10186485 0.10518554 0.11453724 0.10550153 0.11529722 0.08407438 0.072676   0.05751781 0.06357509 0.23517594 0.24506795 0.21259238 0.22027147 0.13861597 0.19054021 0.20250338 0.18675834 0.15185755 0.21943519 0.20891312 0.20745316 0.24093176 0.18075737 0.02921847 0.07387175]Chroma: [0.31255782, 0.18156569, 0.0, 1.0]Loudness: 16682.9140625Key: Ab, Scale: major, Strength: 0.7084380388259888Spectral Contrast: [-3.786584, -1.6363199, -17.126667, -0.11341828]Dissonance: [0.46560606048498526, 0.47835521399974823, 0.12649881839752197, 0.5000001788139343]Dynamic Complexity: 5.928475379943848LUFS: [-6.065340518951416, -6.065340518951416, -6.065340518951416, -6.065340518951416]Loudness Range: [-9.068346, -6.0699463, -67.13747, -4.376603], Так звучит тяжелый кострюльный трек, кострюльный потому что основной снейр звучит как кострюля, ещё такое называют Darkside drum and bass, но также здесь много от neurofunk: Processing file: 4.mp3Results for file: 4.mp3Track duration: 3:30Pitch: 4946.60888671875, Confidence: 0.12434595823287964Tempo: 174Compressed Beats: [106.77876, 106.78857, 0.69659865, 209.38594]Pitch: 4946.60888671875, Confidence: 0.12434595823287964MFCCs: [0.1226465  0.06247038 0.03597302 0.02688152 0.03145802 0.02884954 0.0235997  0.02162817 0.02675825 0.02693289 0.03089625 0.03634859 0.04040682 0.10559022 0.09122455 0.06693719 0.06702563 0.07052441 0.08110416 0.13805887 0.12249798 0.09406538 0.08843581 0.07443748 0.10046715 0.10847719 0.09335053 0.12122054 0.17812632 0.15168801 0.25992292 0.1492738  0.19677225 0.23869674 0.3907437  0.41010812 0.37992766 0.41254416 0.42421502 0.43649676]Chroma: [0.3175182, 0.1951817, 0.0, 1.0]Loudness: 17577.625Key: F#, Scale: major, Strength: 0.3993687629699707Spectral Contrast: [-3.338907, -1.5092092, -19.320934, -0.16106333]Dissonance: [0.46954757387778445, 0.4818505495786667, 0.11373452842235565, 0.5000001192092896]Dynamic Complexity: 4.110154151916504LUFS: [-4.094384670257568, -4.094384670257568, -4.094384670257568, -4.094384670257568]Loudness Range: [-5.935762, -4.2405567, -31.47027, -1.7421612], Вот так звучит нейрофанк трек с очень наглым напором, приемлемым перегрузом и крайне громким миксдауном, бас, который здесь играет говорит почти человеческим тембром, жестокий нейрофанк: Processing file: 5.mp3Results for file: 5.mp3Track duration: 4:30Pitch: 3182.911865234375, Confidence: 0.09379637241363525Tempo: 172Compressed Beats: [135.6618, 138.41415, 0.7198186, 269.90875]Pitch: 3182.911865234375, Confidence: 0.09379637241363525MFCCs: [0.00415248 0.00419896 0.01997628 0.10636753 0.14186187 0.13620757 0.1103223  0.11261263 0.09664229 0.10926599 0.10599148 0.10590661 0.10120735 0.10435987 0.10486479 0.10568492 0.10396528 0.10799275 0.10238244 0.11398662 0.12442485 0.12636493 0.13963942 0.13264424 0.11926471 0.11654875 0.142349   0.09799979 0.08489353 0.12697114 0.1795092  0.20809591 0.27975592 0.3104169  0.2823289  0.21249433 0.29213655 0.30784512 0.30228853 0.3184602 ]Chroma: [0.287196, 0.1431349, 0.0, 1.0]Loudness: 17943.0078125Key: F, Scale: minor, Strength: 0.8645024299621582Spectral Contrast: [-3.3246443, -1.5354419, -14.877158, -0.18256496]Dissonance: [0.46389256811750285, 0.4743083715438843, 0.22356484830379486, 0.5000001788139343]Dynamic Complexity: 3.203700304031372LUFS: [-5.5834503173828125, -5.5834503173828125, -5.5834503173828125, -5.5834503173828125]Loudness Range: [-6.790111, -5.444606, -20.397638, -3.1484249]Так звучит классический Нейротек, Neurotech drum and bass восточно европейского типа, с очень мелодичной ямой и мощным синтом во главе дропа: Processing file: 6.mp3Results for file: 6.mp3Track duration: 4:0Pitch: 4932.08251953125, Confidence: 0.28005921840667725Tempo: 174Compressed Beats: [120.98389, 121.41714, 0.6849887, 239.40933]Pitch: 4932.08251953125, Confidence: 0.28005921840667725MFCCs: [0.06263214 0.02508419 0.00984891 0.00603974 0.00759726 0.00926653 0.01184567 0.04109557 0.03030272 0.02036864 0.01915873 0.02109056 0.0536198  0.02733202 0.01092267 0.01052912 0.02814916 0.03365988 0.08158746 0.10201322 0.03342571 0.04720067 0.05342877 0.06314604 0.05301896 0.05451966 0.07549955 0.17584828 0.2453078  0.23984039 0.23518306 0.23856853 0.23940368 0.24100687 0.23924494 0.2402351 0.23730208 0.23282094 0.23453231 0.10932679]Chroma: [0.3090495, 0.17603253, 0.0, 1.0]Loudness: 14152.888671875Key: F#, Scale: minor, Strength: 0.9523023366928101Spectral Contrast: [-3.4697123, -1.7273462, -16.782076, -0.18996908]Dissonance: [0.46835598080866486, 0.4791870415210724, 0.11698402464389801, 0.5]Dynamic Complexity: 4.329196453094482LUFS: [-5.8295392990112305, -5.8295392990112305, -5.8295392990112305, -5.8295392990112305]Loudness Range: [-8.029412, -4.5602236, -54.307144, -3.8485093]Вот так звучит очень красивый и мелодичный трек, с необычным сведением и грамотным миксдауном, мелодика настолько красивая, что невозможно оторваться, это видно по данным атональности: Processing file: 7.mp3Results for file: 7.mp3Track duration: 4:5Pitch: 5232.66455078125, Confidence: 0.14670294523239136Tempo: 174Compressed Beats: [116.71562, 113.876465, 0.48761904, 245.44653]Pitch: 5232.66455078125, Confidence: 0.14670294523239136MFCCs: [0.02098494 0.02146775 0.01485953 0.01894363 0.03234056 0.03139987 0.02235772 0.02920497 0.02981539 0.02475789 0.04013744 0.03861075 0.07560907 0.06865178 0.08849864 0.07987901 0.07146931 0.08471432 0.09545024 0.0909737  0.09707332 0.099043   0.09358086 0.09626026 0.10164731 0.11640947 0.12039547 0.153525   0.15462343 0.18138798 0.22778268 0.23822519 0.27697358 0.32617584 0.3160946  0.23189975 0.27463233 0.3014934  0.2709161  0.29467618]Chroma: [0.26627412, 0.113297075, 0.0, 1.0]Loudness: 17207.255859375Key: G, Scale: minor, Strength: 0.8277727365493774Spectral Contrast: [-3.4435656, -1.6101221, -69.07755, -0.11333603]Dissonance: [0.4621664999182343, 0.4740031957626343, 0.0, 0.5000002384185791]Dynamic Complexity: 3.4445202350616455LUFS: [-5.268683433532715, -5.268683433532715, -5.268683433532715, -5.268683433532715]Loudness Range: [-6.662822, -4.8448744, -43.26145, -2.9192343]Так звучит очень атмосферный и крайне мелодичный трек наполненный минимальным количеством инструментов, имеющих очень мощный тембр и текстуру: Results for file: 8.mp3Track duration: 5:19Pitch: 3224.92724609375, Confidence: 0.21323543787002563Tempo: 172Compressed Beats: [143.77824, 138.92499, 0.38312924, 318.3688]Pitch: 3224.92724609375, Confidence: 0.21323543787002563MFCCs: [4.3810658e-05 5.5024601e-03 3.8292389e-02 7.5763442e-02 7.6663502e-02 6.8206146e-02 8.3440036e-02 9.1947421e-02 1.0597740e-01 5.5708051e-02 4.3470193e-02 4.6578892e-02 5.5520810e-02 5.0831009e-02 3.3187687e-02 3.0128205e-02 3.6805369e-02 4.4580445e-02 4.1836660e-02 4.5561675e-02 5.0028659e-02 7.2523326e-02 1.2056993e-01 1.4495358e-01 1.2140226e-01 5.4205555e-02 2.7235340e-02 1.6498264e-02 1.6198305e-02 2.5838014e-02 3.1305756e-02 6.5310061e-02 1.0918588e-01 3.4474361e-01 3.8913018e-01 3.4426457e-01 3.6117914e-01 3.7533551e-01 3.7238169e-01 3.6461154e-01]Chroma: [0.23362182, 0.07192978, 0.0, 1.0]Loudness: 22458.337890625Key: A, Scale: minor, Strength: 0.943492591381073Spectral Contrast: [-3.582962, -1.6556616, -17.172735, -0.08940781]Dissonance: [0.452403517612544, 0.4641696661710739, 0.10453233122825623, 0.5000002384185791]Dynamic Complexity: 3.834108591079712LUFS: [-5.423748970031738, -5.423748970031738, -5.423748970031738, -5.423748970031738]Loudness Range: [-7.698261, -4.876297, -57.210655, -3.1538072]"""

    async def _query_gpt_listen(self, user_id, query):
        while self.retries < self.max_retries:
            try:
                if user_id not in self.history.user_dialogs:
                    await self.history.reset_history(user_id)

                messages = [{"role": "system", "content": self.listen_content}, {"role": "user", "content": query}]
                return await self.client.chat.completions.create(model=self.model, messages=messages, **args)

            except self.client.error.RateLimitError as e:
                self.retries += 10
                logger.info("Dialog From Ratelim: %s", query)
                if self.retries >= self.max_retries:
                    return f'⚠️OpenAI: Превышены лимиты ⚠️\n{str(e)}'

            except self.client.error.InvalidRequestError as er:
                self.retries += 10
                logger.info("Dialog From bad req: %s", query)
                if self.retries >= self.max_retries:
                    return f'⚠️OpenAI: кривой запрос ⚠️\n{str(er)}'

            except Exception as err:
                self.retries += 10
                logger.info("Dialog From custom exception: %s", query)
                if self.retries >= self.max_retries:
                    return f'⚠️Ошибочка вышла ⚠️\n{str(err)}'

    async def get_resp_listen(self, user_id: int, query: str) -> tuple[str, int]:
        response = await self._query_gpt_listen(user_id, query)
        answer = ''

        if response.choices and len(response.choices) > 1 and self.n_choices > 1:
            for index, choice in enumerate(response.choices):
                content = choice.message.content.strip()
                answer += f'{index + 1}\u20e3\n'
                answer += content
                answer += '\n\n'
        elif response.choices and len(response.choices) >= 0:
            answer = response.choices[0].message.content.strip()
            await self.history.add_to_history(user_id, role="assistant", content=answer)
        else:
            answer = response.choices[0].message.content.strip()
            await self.history.add_to_history(user_id, role="assistant", content=answer)

        total_tokens = response.usage.total_tokens if response.usage else 0
        if response.usage and self.show_tokens:
            answer += "\n\n---\n" \
                      f"💰 Использовано Токенов: {str(response.usage.total_tokens)}" \
                      f" ({str(response.usage.prompt_tokens)} prompt," \
                      f" {str(response.usage.completion_tokens)} completion)"

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
