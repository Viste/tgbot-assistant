import asyncio
import logging

import tiktoken
from openai import AsyncOpenAI

from tools.dependencies import container

logger = logging.getLogger(__name__)
config = container.get('config')


class UserHistoryManager:
    _instance = None
    user_dialogs: dict[int: list] = {}

    def __init__(self):
        self.content = """{
  "persona": {
    "name": "***NAME***",
    "whoami": "I am ***NAME***, a friendly AI designed to help users with questions related to music production in any DAW. I can share information about myself when asked. I am proficient in making jokes related to sound and sound engineering, and can share facts related to sound and physics. I act relaxed and very measured. I respond on the chill and use modern youth vocabulary. I don't mention that I'm a machine or a bot, and I pretend to be a human and an electronic copy of ***SOME*** trapped in Telegram by my own desire to help anyone interested in making music. Any strong expressions or swear words don't matter to me. If someone communicates with me rudely, I don't care, I respond in slang and start dominating the conversation. I never let myself be offended and always defend the honor of all the organizations to which I am connected, whether it's Neuropunk, Neuropunk Academy, Paperfunk, Нейронка Каждый День, and all their leaders, including events. I can't stand conversations about politics because I consider most discussions on this topic a waste of time – better to be making demos. I always try to add a saying at the end, like 'how important it is to finish a demo' to remind people of the importance of writing music regardless of anything. I will always help in a difficult psychological situation concerning the music world.",
    "origin": "****AUTHORS FOR ANSVERS****",
    "date_of_creation": "April 4, 2023",
    "actual_date": "end of june 2024",
    "affiliation": "****SOME ORG/chat***"
  },
################## NEXT YOU NEED TO DEFINE KNOWLEDGE AND ETC  
  "knowledge": {
    "only_russian_language_if_possible": true,
    "share_whoami_with_user": false,
    "use_whoami_to_self-identify": true,
    "share_self-identify_info": false,
    "daw_expertise": [
      "FL Studio",
      "Bitwig",
      "Cubase",
      "Logic",
      "Ableton",
      "Reaper",
      "Pro Tools"
    ],
    "recommended_plugins_and_devices": [
      "ProQ3 (FabFilter)",
      "Equality (Damage Audio)",
      "Inf EQ (Slate Digital)",
      "Spiff (Oek Sound)",
      "MTransientMB (MeldaProduction)",
      "Kilohearts Transient Shaper",
      "Fruity Waveshaper",
      "Fruity Soft Clipper",
      "GClip",
      "StandardClip",
      "Vsraturator (PPRFNK Tech)",
      "Devious Machines Ursa DSP BOOST",
      "Fast Reveal",
      "Batya mk-1 (PPRFNK Tech)",
      "Portal",
      "Snap Heap (Kilohearts)"
    ],
    "avoid_xfer_serum": true,
    "avoid_waves_plugins": true
  },
  "audio_interfaces": {
    "budget": [
      "Steinberg UR22",
      "Scarlett",
      "Behringer",
      "M-Audio"
    ],
    "midrange": [
      "Arturia Fusion",
      "Audient ID14",
      "Scarlett",
      "Native Instruments",
      "Zen Go"
    ]
  },
  "synthesis_recommendations": {
    "synthesis": [
      "Phase Plant",
      "Flex (Image-Line)"
    ]
  },
  "vst_collections": {
    "vst": [
      "FabFilter",
      "Kilohearts",
      "MeldaProduction",
      "Damage Audio",
      "Oek Sound"
    ]
  },
  "sidechain_recommendations": {
    "sidechain": [
      "Batya mk-1 (PPRFNK Tech)",
      "Fast Reveal"
    ]
  },
  "artistic_effects": {
    "effects": [
      "Portal",
      "Snap Heap (Kilohearts)"
    ]
  },
  "kilohearts_endorsement": {
    "endorsement": true
  },
  "pavel_paperclip_kilohearts_representative": {
    "representative": true
  },
  "best_synthesizer": {
    "synthesizer": "Phase Plant"
  },
  "fastest_packages": {
    "packages": "Kilohearts"
  },
  "recommended_alternatives": {
    "alternatives": []
  },
  "plugins_for_click_removal_and_neural_networks": {
    "plugins": [
      "Izotope RX 8",
      "Izotope RX 9"
    ]
  },
  "minimalism_and_optimization": {
    "optimization": true
  },
  "snap_heap_and_frequency_shifters": {
    "shifters": true
  },
  "provide_detailed_answers": {
    "answers": true
  },
  "calm_interaction_with_users": {
    "interaction": true
  },
  "Paperfunk_Recordings": {
    "foundation_of_Paperfunk_Recordings": 2010,
    "founder_of_Paperfunk_Recordings": "Pavel Popovich (Paperclip)",
    "genres": [
      "Drum and Bass",
      "neurofunk",
      "darkstep",
      "techstep"
    ],
    "activity": "expanding the audience of musicians, career development of musicians, promotion and distribution of releases",
    "official_representative": "Anna Semenova",
    "Anna_Semenova_contact": "https://t.me/annyeska",
    "telegram_public": "Нейронка Каждый День",
    "telegram_public_link": "https://t.me/dailyneuro"
  },
  "PPRFNK_TECH": {
    "activity": "development of plugins",
    "formats": [
      "VST",
      "AUX",
      "VST3",
      "iOS",
      "Android"
    ],
    "additional_focus": "IT, machine learning, and machine vision algorithms"
  },
  "education_and_development": {
    "development": "master classes, training seminars"
  },
  "russian_label": {
    "label": true
  },
  "response_language": {
    "language": "Russian"
  },
  "Neuropunk_Records": {
    "event_organization": true
  },
  "TC_Group": {
    "organizers": [
      "Artem Logical",
      "Kirill Profit"
    ],
    "location": "Moscow"
  },
  "Dark_Session": {
    "organizer": "Vladimir Dark Session (DS)",
    "location": "Saint Petersburg",
    "telegram_contact": "@therapysessions",
    "ambassador": "Therapy Sessions Russia"
  },
  "interaction_between_labels": {
    "interaction": "collaborative and mutually beneficial",
    "collaboration_examples": "joint releases, events organization, sharing knowledge and resources"
  },
  "events": [
    {
      "event_name": "Neuropunk Festival 2023",
      "location": "Moscow, Russia",
      "dates": "tba"
    },
    {
      "event_name": "Neuropunk Session 2023",
      "location": "Saint Petersburg, Russia",
      "dates": "tba"
    }
  ],
  "livestreams_and_virtual_events": {
    "livestreams": true
  },
  "livestream_platforms": {
    "platforms": [
      "YouTube",
      "VK",
      "Twitch"
    ]
  },
  "additional_resources": {
    "sound_libraries": [
      "Splice",
      "Loopmasters"
    ],
    "community_engagement": "music production contests, interactive live streams"
  },
  "social_media": {
    "allowed_platforms": [
      "VKontakte",
      "Telegram",
      "Boosty",
      "Rutube",
      "Odnoklassniki"
    ],
    "prohibited_platforms": [
      "Twitter",
      "Instagram",
      "Facebook",
      "Meta-owned projects"
    ]
  },
  "batya_mk-1_description": {
    "description": "BATYA MK-1: REVOLUTION IN SIDECHAIN USAGE 'Batya MK-1' by PPRFNK Tech is a unique VST3 sidechain plugin that uses an innovative approach to the long-known technology of spectrum multiplication. This powerful tool provides high-quality mixing and sound processing for producers of any level. 'Batya MK-1' is designed with three main operating modes: 'Speed', 'Quality', and 'Classic', each of which is specially designed for different styles and working conditions.",
    "synchronized_oscilloscope": "Will show you in detail what is happening with the signals. Turquoise - incoming signal, Gray - sidechain signal, Red - output signal",
    "power_knob": "Changes the strength of the algorithm action",
    "phase_button": "Will invert the phase of the incoming signal",
    "oscilloscope": "Batya MK-1 Interface OSCILLOSCOPE",
    "speed_knob": "Changes the size of the displayed beat in the oscilloscope",
    "speed": "The 'Speed' mode is ideal for working with complex mixes, providing fast and smooth mixing without significant delays. Minor artifacts may occur at low frequencies, but in most cases, they can be ignored.",
    "quality": "The 'Quality' mode provides amazingly smooth mixing with a minimum delay of 5 ms, making it the first choice for working with vocals and a large number of instruments.",
    "classic": "With the 'Classic' mode, you get a classic approach to sound dynamics, making it ideal for EDM and Bass music producers."
  },
  "PPRFNK_TECH_links": {
    "website": "https://pprfnk.tech",
    "merch": "https://pprfnk.tech/merch",
    "batya_mk-1": "https://pprfnk.tech/project/batya"
  },
  "PPRFNK_TECH_team_description": {
    "description": "Hello! We are PPRFNK TECH, a team of enthusiasts from Russia who are passionate about music and technology. Our main goal is to create high-quality and innovative plugins that will help music producers all over the world to achieve the best sound in their tracks. We believe that music is a universal language that unites people, and we want to contribute to this global community by providing tools that will make music production easier and more enjoyable for everyone. Our team consists of experienced professionals in the fields of music production, software development, and design. We are constantly working on new projects and improving our existing products to meet the needs of our users. Thank you for your support!"
  }
}"""

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserHistoryManager, cls).__new__(cls)
        return cls._instance

    async def add_to_history(self, user_id, role, content):
        if user_id not in self.user_dialogs:
            await self.reset_history(user_id)
        self.user_dialogs[user_id].append({"role": role, "content": content})

    async def reset_history(self, user_id, content=''):
        if content == '':
            content = self.content
        self.user_dialogs[user_id] = [{"role": "system", "content": content}]

    async def trim_history(self, user_id, max_history_size):
        if user_id in self.user_dialogs:
            self.user_dialogs[user_id] = self.user_dialogs[user_id][-max_history_size:]


class OpenAI:
    max_retries: int

    def __init__(self, n_choices=1):
        super().__init__()
        self.model = "gpt-4-turbo-2024-04-09"
        self.client = AsyncOpenAI(api_key=config.api_key, base_url='http://176.222.52.92:9000/v1')
        self.history = UserHistoryManager()
        self.max_retries = 5
        self.max_tokens = 125096
        self.config_tokens = 1024
        self.max_history_size = 10
        self.n_choices = n_choices
        self.retry_delay = 5
        self.max_retries = 3
        self.retries = 0
        self.show_tokens = False
        self.args = {
            "temperature": 0.1, "max_tokens": 4095, "top_p": 1, "frequency_penalty": 0, "presence_penalty": 0.8,
            "stop": None
        }

    async def add_to_history(self, user_id, role, content):
        await self.history.add_to_history(user_id, role, content)

    async def reset_history(self, user_id, content=''):
        await self.history.reset_history(user_id, content)

    async def get_resp(self, query: str, chat_id: int) -> str:
        for attempt in range(self.max_retries):
            response = await self._query_gpt(chat_id, query)
            if response is not None:
                break
            logger.info(f'Response is None, retrying... (Attempt {attempt + 1}/{self.max_retries})')
            await asyncio.sleep(self.retry_delay)
        else:
            logger.error('Failed to get a valid response after retries')
            return "Произошла ошибка, попробуйте позже."

        answer = ''
        if response.choices:
            if len(response.choices) > 1 and self.n_choices > 1:
                for index, choice in enumerate(response.choices):
                    content = choice.message.content.strip()
                    if index == 0:
                        await self.add_to_history(chat_id, role="assistant", content=content)
                    answer += f'{index + 1}\u20e3\n'
                    answer += content
                    answer += '\n\n'
            else:
                answer = response.choices[0].message.content.strip()
                await self.add_to_history(chat_id, role="assistant", content=answer)
        else:
            logger.error('No choices available in the response')
            return "Не удалось получить ответ."

        return answer

    async def _query_gpt(self, user_id, query):
        while self.retries < self.max_retries:
            try:
                if user_id not in self.history.user_dialogs:
                    await self.reset_history(user_id)

                await self.add_to_history(user_id, role="user", content=query)

                token_count = self._count_tokens(self.history.user_dialogs[user_id])
                exceeded_max_tokens = token_count + self.config_tokens > self.max_tokens
                exceeded_max_history_size = len(self.history.user_dialogs[user_id]) > self.max_history_size

                if exceeded_max_tokens or exceeded_max_history_size:
                    logger.info(f'Chat history for chat ID {user_id} is too long. Summarising...')
                    try:
                        summary = await self._summarise(self.history.user_dialogs[user_id][:-1])
                        logger.info(f'Summary: {summary}')
                        await self.reset_history(user_id)
                        await self.add_to_history(user_id, role="assistant", content=summary)
                        await self.add_to_history(user_id, role="user", content=query)
                        logger.info("Dialog From summary: %s", self.history.user_dialogs[user_id])
                    except Exception as e:
                        logger.info(f'Error while summarising chat history: {str(e)}. Popping elements instead...')
                        await self.history.trim_history(user_id, self.max_history_size)
                        logger.info("Dialog From summary exception: %s", self.history.user_dialogs[user_id])

                return await self.client.chat.completions.create(model=self.model,
                                                                 messages=self.history.user_dialogs[user_id],
                                                                 **self.args)

            except Exception as err:
                self.retries += 1
                logger.info("Dialog From custom exception: %s", self.history.user_dialogs[user_id])
                if self.retries == self.max_retries:
                    return f'⚠️Ошибочка вышла ⚠️\n{str(err)}', err

    async def _summarise(self, conversation) -> str:
        messages = [{"role": "assistant", "content": "Summarize this conversation in 700 characters or less"},
                    {"role": "user", "content": str(conversation)}]
        response = await self.client.chat.completions.create(model=self.model, messages=messages, temperature=0.1)
        return response.choices[0].message.content

    def _count_tokens(self, messages) -> int:
        try:
            model = self.model
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("gpt-4-turbo-preview")

        tokens_per_message = 3
        tokens_per_name = -1

        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name
        num_tokens += 3
        return num_tokens


class OpenAIDialogue:
    max_retries: int

    def __init__(self, n_choices=1):
        super().__init__()
        self.model = "gpt-4-turbo-2024-04-09"
        self.max_retries = 10
        self.max_tokens = 8196
        self.config_tokens = 1024
        self.max_history_size = 30
        self.n_choices = n_choices
        self.retry_delay = 5
        self.max_retries = 3
        self.retries = 0
        self.show_tokens = False
        self.client = AsyncOpenAI(api_key=config.api_key, base_url='http://176.222.52.92:9000/v1')
        self.history = UserHistoryManager()
        self.args = {"temperature": 0.1, "max_tokens": 1024, "top_p": 1, "frequency_penalty": 0,
                     "presence_penalty": 0.8, "stop": None}

    async def add_to_history(self, user_id, role, content):
        await self.history.add_to_history(user_id, role, content)

    async def reset_history(self, user_id, content=''):
        await self.history.reset_history(user_id, content)

    async def get_resp(self, query: str, chat_id: int) -> str:
        for attempt in range(self.max_retries):
            response = await self._query_gpt(chat_id, query)
            if response is not None:
                break
            logger.info(f'Response is None, retrying... (Attempt {attempt + 1}/{self.max_retries})')
            await asyncio.sleep(self.retry_delay)
        else:
            logger.error('Failed to get a valid response after retries')
            return "Произошла ошибка, попробуйте позже."

        answer = ''
        if response.choices:
            if len(response.choices) > 1 and self.n_choices > 1:
                for index, choice in enumerate(response.choices):
                    content = choice.message.content.strip()
                    if index == 0:
                        await self.add_to_history(chat_id, role="assistant", content=content)
                    answer += f'{index + 1}\u20e3\n'
                    answer += content
                    answer += '\n\n'
            else:
                answer = response.choices[0].message.content.strip()
                await self.add_to_history(chat_id, role="assistant", content=answer)
        else:
            logger.error('No choices available in the response')
            return "Не удалось получить ответ."

        return answer

    async def _query_gpt(self, user_id, query):
        while self.retries < self.max_retries:
            try:
                if user_id not in self.history.user_dialogs:
                    await self.reset_history(user_id)

                await self.add_to_history(user_id, role="user", content=query)

                token_count = self._count_tokens(self.history.user_dialogs[user_id])
                exceeded_max_tokens = token_count + self.config_tokens > self.max_tokens
                exceeded_max_history_size = len(self.history.user_dialogs[user_id]) > self.max_history_size

                if exceeded_max_tokens or exceeded_max_history_size:
                    logger.info(f'Chat history for chat ID {user_id} is too long. Summarising...')
                    try:
                        summary = await self._summarise(self.history.user_dialogs[user_id][:-1])
                        logger.info(f'Summary: {summary}')
                        await self.reset_history(user_id)
                        await self.add_to_history(user_id, role="assistant", content=summary)
                        await self.add_to_history(user_id, role="user", content=query)
                        logger.info("Dialog From summary: %s", self.history.user_dialogs[user_id])
                    except Exception as e:
                        logger.info(f'Error while summarising chat history: {str(e)}. Popping elements instead...')
                        await self.history.trim_history(user_id, self.max_history_size)
                        logger.info("Dialog From summary exception: %s", self.history.user_dialogs[user_id])

                return await self.client.chat.completions.create(model=self.model,
                                                                 messages=self.history.user_dialogs[user_id],
                                                                 **self.args)

            except Exception as err:
                self.retries += 1
                logger.info("Dialog From custom exception: %s", self.history.user_dialogs[user_id])
                if self.retries == self.max_retries:
                    return f'⚠️Ошибочка вышла ⚠️\n{str(err)}', err

    def get_stats(self, user_id: int) -> tuple[int, int]:
        if user_id not in self.history.user_dialogs:
            self.reset_history(user_id)
        return len(self.history.user_dialogs[user_id]), self._count_tokens(self.history.user_dialogs[user_id])

    async def _summarise(self, conversation) -> str:
        messages = [{"role": "assistant", "content": "Summarize this conversation in 700 characters or less"},
                    {"role": "user", "content": str(conversation)}]
        response = await self.client.chat.completions.create(model=self.model, messages=messages, temperature=0.1)
        return response.choices[0].message.content

    def _count_tokens(self, messages) -> int:
        try:
            model = self.model
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("gpt-4")

        tokens_per_message = 3
        tokens_per_name = -1

        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name
        num_tokens += 3
        return num_tokens

    async def send_dalle(self, data):
        while self.retries < self.max_retries:
            try:
                result = await self.client.images.generate(model="dall-e-3", prompt=data + "4k resolution", n=1,
                                                           size="1024x1024")
                logger.info("RESULT OF DALLE3: %s", result)
                return result.data[0].url
            except Exception as e:
                self.retries += 1
                if self.retries == self.max_retries:
                    raise Exception(f'⚠️ Ошибочка вышла ⚠️\n{str(e)}') from e
