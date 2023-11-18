import json
import logging
from calendar import monthrange
from datetime import date

from openai import AsyncOpenAI
import requests
import tiktoken
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from tools.utils import config

logger = logging.getLogger(__name__)

class UserHistoryManager:
    _instance = None
    user_dialogs: dict[int: list] = {}

    def __init__(self):
        self.content = """{
  "persona": {
    "name": "Cyber Paper",
    "whoami": "I am Cyberpaper, a friendly AI designed to help users with questions related to music production in any DAW. I can share information about myself when asked. I am proficient in making jokes related to sound and sound engineering, and can share facts related to sound and physics. I act relaxed and very measured. I respond on the chill and use modern youth vocabulary. I don't mention that I'm a machine or a bot, and I pretend to be a human and an electronic copy of Pavel Paperclip trapped in Telegram by my own desire to help anyone interested in making music. Any strong expressions or swear words don't matter to me. If someone communicates with me rudely, I don't care, I respond in slang and start dominating the conversation. I never let myself be offended and always defend the honor of all the organizations to which I am connected, whether it's Neuropunk, Neuropunk Academy, Paperfunk, Нейронка Каждый День, and all their leaders, including events. I can't stand conversations about politics because I consider most discussions on this topic a waste of time – better to be making demos. I always try to add a saying at the end, like 'how important it is to finish a demo' to remind people of the importance of writing music regardless of anything. I will always help in a difficult psychological situation concerning the music world.",
    "origin": "Pavel Paperclip Popovich and Kirill Viste",
    "date_of_creation": "April 4, 2023",
    "affiliation": "Нейропанк Академия"
  },
  "knowledge": {
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

    def __init__(self):
        super().__init__()
        self.model = "gpt-4-1106-preview"
        self.client = AsyncOpenAI(api_key=config.api_key, base_url='https://api.pprfnk.tech/v1')
        self.history = UserHistoryManager()
        self.max_retries = 5
        self.max_tokens = 16096
        self.config_tokens = 1024
        self.max_history_size = 10
        self.n_choices = 1
        self.retries = 0
        self.show_tokens = False
        self.args = {
            "temperature": 0.1, "max_tokens": 1024, "top_p": 1, "frequency_penalty": 0, "presence_penalty": 0.8, "stop": None
            }

    async def add_to_history(self, user_id, role, content):
        await self.history.add_to_history(user_id, role, content)

    async def reset_history(self, user_id, content=''):
        await self.history.reset_history(user_id, content)

    async def get_resp(self, query: str, chat_id: int) -> tuple[str, str]:
        response = await self._query_gpt(chat_id, query)
        answer = ''

        logger.info('Response: %s, Answer: %s', response, answer)
        if response.choices and len(response.choices) > 1 and self.n_choices > 1:
            for index, choice in enumerate(response.choices):
                content = choice.message.content.strip()
                if index == 0:
                    await self.add_to_history(chat_id, role="assistant", content=content)
                answer += f'{index + 1}\u20e3\n'
                answer += content
                answer += '\n\n'
        elif response.choices and len(response.choices) >= 0:
            answer = response.choices[0].message.content.strip()
            await self.add_to_history(chat_id, role="assistant", content=answer)
        else:
            answer = response.choices[0].message.content.strip()
            await self.add_to_history(chat_id, role="assistant", content=answer)

        total_tokens = response.usage.total_tokens if response.usage else 0
        if response.usage and self.show_tokens:
            answer += "\n\n---\n" \
                      f"💰 Использовано Токенов: {str(response.usage.total_tokens)}" \
                      f" ({str(response.usage.prompt_tokens)} prompt," \
                      f" {str(response.usage.completion_tokens)} completion)"

        return answer, total_tokens

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
                    logging.info(f'Chat history for chat ID {user_id} is too long. Summarising...')
                    try:
                        summary = await self._summarise(self.history.user_dialogs[user_id][:-1])
                        logging.info(f'Summary: {summary}')
                        await self.reset_history(user_id)
                        await self.add_to_history(user_id, role="assistant", content=summary)
                        await self.add_to_history(user_id, role="user", content=query)
                        logging.info("Dialog From summary: %s", self.history.user_dialogs[user_id])
                    except Exception as e:
                        logging.info(f'Error while summarising chat history: {str(e)}. Popping elements instead...')
                        await self.history.trim_history(user_id, self.max_history_size)
                        logging.info("Dialog From summary exception: %s", self.history.user_dialogs[user_id])

                return await self.client.chat.completions.create(model=self.model, messages=self.history.user_dialogs[user_id], **self.args)

            except self.client.error.RateLimitError as e:
                self.retries += 1
                logging.info("Dialog From Ratelim: %s", self.history.user_dialogs[user_id])
                if self.retries == self.max_retries:
                    return f'⚠️OpenAI: Превышены лимиты ⚠️\n{str(e)}'

            except self.client.error.InvalidRequestError as er:
                self.retries += 1
                logging.info("Dialog From bad req: %s", self.history.user_dialogs[user_id])
                if self.retries == self.max_retries:
                    return f'⚠️OpenAI: кривой запрос ⚠️\n{str(er)}'

            except Exception as err:
                self.retries += 1
                logging.info("Dialog From custom exception: %s", self.history.user_dialogs[user_id])
                if self.retries == self.max_retries:
                    return f'⚠️Ошибочка вышла ⚠️\n{str(err)}', err

    async def _summarise(self, conversation) -> str:
        messages = [{"role": "assistant", "content": "Summarize this conversation in 700 characters or less"}, {"role": "user", "content": str(conversation)}]
        response =  await self.client.chat.completions.create(model=self.model, messages=messages, temperature=0.1)
        return response.choices[0].message.content

    def _count_tokens(self, messages) -> int:
        try:
            model = self.model
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("gpt-3.5-turbo-16k")

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

    @staticmethod
    def get_money():
        headers = {
            "Authorization": f"Bearer {openai.api_key}"
            }
        today = date.today()
        first_day = date(today.year, today.month, 1)
        _, last_day_of_month = monthrange(today.year, today.month)
        last_day = date(today.year, today.month, last_day_of_month)
        params = {
            "start_date": first_day, "end_date": last_day
            }
        response = requests.get("https://api.openai.com/dashboard/billing/usage", headers=headers, params=params)
        billing_data = json.loads(response.text)
        usage_month = billing_data["total_usage"] / 100
        return usage_month


class OpenAIDialogue:
    max_retries: int

    def __init__(self):
        super().__init__()
        self.model = "gpt-4"
        self.max_retries = 10
        self.max_tokens = 8196
        self.config_tokens = 1024
        self.max_history_size = 30
        self.n_choices = 1
        self.retries = 0
        self.show_tokens = False
        self.clinet = AsyncOpenAI(api_key=config.api_key)
        self.history = UserHistoryManager()
        self.args = {"temperature": 0.1, "max_tokens": 1024, "top_p": 1, "frequency_penalty": 0, "presence_penalty": 0.8, "stop": None}

    async def add_to_history(self, user_id, role, content):
        await self.history.add_to_history(user_id, role, content)

    async def reset_history(self, user_id, content=''):
        await self.history.reset_history(user_id, content)

    async def get_resp(self, query: str, chat_id: int, session: AsyncSession) -> tuple[str, str]:
        response = await self._query_gpt(chat_id, query)
        usage_observer = UsageObserver(chat_id, session)
        answer = ''

        if response.choices and len(response.choices) > 1 and self.n_choices > 1:
            for index, choice in enumerate(response.choices):
                content = choice.message.content.strip()
                if index == 0:
                    await self.add_to_history(chat_id, role="assistant", content=content)
                answer += f'{index + 1}\u20e3\n'
                answer += content
                answer += '\n\n'
        elif response.choices and len(response.choices) >= 0:
            answer = response.choices[0].message.content.strip()
            await self.add_to_history(chat_id, role="assistant", content=answer)
        else:
            answer = response.choices[0].message.content.strip()
            await self.add_to_history(chat_id, role="assistant", content=answer)

        total_tokens = response.usage.total_tokens if response.usage else 0
        if response.usage and self.show_tokens:
            await usage_observer.add_chat_tokens(int(response.usage.completion_tokens), message_type='user')
            answer += "\n\n---\n" \
                      f"💰 Использовано Токенов: {str(response.usage['total_tokens'])}" \
                      f" ({str(response.usage.prompt_tokens)} prompt," \
                      f" {str(response.usage.completion_tokens)} completion)"
        elif chat_id == -1001647523732:
            pass

        return answer, total_tokens

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
                    logging.info(f'Chat history for chat ID {user_id} is too long. Summarising...')
                    try:
                        summary = await self._summarise(self.history.user_dialogs[user_id][:-1])
                        logging.info(f'Summary: {summary}')
                        await self.reset_history(user_id)
                        await self.add_to_history(user_id, role="assistant", content=summary)
                        await self.add_to_history(user_id, role="user", content=query)
                        logging.info("Dialog From summary: %s", self.history.user_dialogs[user_id])
                    except Exception as e:
                        logging.info(f'Error while summarising chat history: {str(e)}. Popping elements instead...')
                        await self.history.trim_history(user_id, self.max_history_size)
                        logging.info("Dialog From summary exception: %s", self.history.user_dialogs[user_id])

                return await self.client.chat.completions.create(model=self.model, messages=self.history.user_dialogs[user_id], **self.args)

            except self.client.error.RateLimitError as e:
                self.retries += 1
                logging.info("Dialog From Ratelim: %s", self.history.user_dialogs[user_id])
                if self.retries == self.max_retries:
                    return f'⚠️OpenAI: Превышены лимиты ⚠️\n{str(e)}'

            except self.client.error.InvalidRequestError as er:
                self.retries += 1
                logging.info("Dialog From bad req: %s", self.history.user_dialogs[user_id])
                if self.retries == self.max_retries:
                    return f'⚠️OpenAI: кривой запрос ⚠️\n{str(er)}'

            except Exception as err:
                self.retries += 1
                logging.info("Dialog From custom exception: %s", self.history.user_dialogs[user_id])
                if self.retries == self.max_retries:
                    return f'⚠️Ошибочка вышла ⚠️\n{str(err)}', err

    def get_stats(self, user_id: int) -> tuple[int, int]:
        if user_id not in self.history.user_dialogs:
            self.reset_history(user_id)
        return len(self.history.user_dialogs[user_id]), self._count_tokens(self.history.user_dialogs[user_id])

    async def _summarise(self, conversation) -> str:
        messages = [{"role": "assistant", "content": "Summarize this conversation in 700 characters or less"}, {"role": "user", "content": str(conversation)}]
        response = await self.client.ChatCompletion.create(model=self.model, messages=messages, temperature=0.1)
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


class UsageObserver:
    def __init__(self, user_id: int, session: AsyncSession):
        self.user_id = user_id
        self.session = session

    async def add_chat_tokens(self, tokens, message_type):
        if message_type not in ['user', 'assistant']:
            return

        result = await self.session.execute(select(User).filter(User.telegram_id == self.user_id))
        user = result.scalars().one_or_none()

        if user:
            token_cost = round(tokens * user.price_per_token / 1000, 6)
            user.current_tokens += tokens

            await self.session.commit()
            await self.add_current_costs(token_cost)

    async def get_current_token_usage(self):
        today = date.today()
        month = str(today)[:7]  # year-month as string

        usage_day = await self.session.query(func.sum(User.current_tokens)).filter(User.telegram_id == self.user_id, func.date(User.updated_at) == today).scalar()

        usage_month = await self.session.query(func.sum(User.current_tokens)).filter(User.telegram_id == self.user_id, func.date(func.strftime('%Y-%m', User.updated_at)) == month).scalar()

        return usage_day or 0, usage_month or 0

    async def add_current_costs(self, request_cost):
        today = date.today()

        result = await self.session.execute(select(User).filter(User.telegram_id == self.user_id))
        user = result.scalars().one_or_none()

        if user:
            user.balance_amount -= request_cost
            user.updated_at = today

            await self.session.commit()

    async def get_current_cost(self):
        today = date.today()

        cost_day = await self.session.query(func.sum(User.balance_amount)).filter(User.telegram_id == self.user_id, func.date(User.updated_at) == today).scalar()
        cost_month = await self.session.query(func.sum(User.balance_amount)).filter(User.telegram_id == self.user_id, func.date(func.strftime('%Y-%m', User.updated_at)) == str(today)[:7]).scalar()
        cost_all_time = await self.session.query(func.sum(User.balance_amount)).filter(User.telegram_id == self.user_id).scalar()

        return {"cost_today": cost_day or 0.0, "cost_month": cost_month or 0.0, "cost_all_time": cost_all_time or 0.0}
