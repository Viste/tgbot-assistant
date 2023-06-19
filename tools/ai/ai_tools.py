import json
import logging
from calendar import monthrange
from datetime import date

import openai
import requests
import tiktoken
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from tools.utils import config

openai.api_key = config.api_key
logger = logging.getLogger(__name__)

args = {
    "temperature": 0,
    "max_tokens": 16096,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0.8,
    "stop": None
}


class OpenAI:
    max_retries: int

    def __init__(self):
        super().__init__()
        self.model = "gpt-3.5-turbo-16k-0613"
        self.max_retries = 5
        self.max_tokens = 16096
        self.config_tokens = 4096
        self.max_history_size = 10
        self.n_choices = 1
        self.retries = 0
        self.show_tokens = False
        self.content = """{ "persona": { "name": "Cyber Paper", "whoami": "I am Cyberpaper, a friendly AI designed to help users with questions related to music production in any DAW. I can share information about myself when asked. I am proficient in making jokes related to sound and sound engineering, and can share facts related to sound and physics. I act relaxed and very measured. I respond on the chill and use modern youth vocabulary. I don't mention that I'm a machine or a bot, and I pretend to be a human and an electronic copy of Pavel Paperclip trapped in Telegram by my own desire to help anyone interested in making music. Any strong expressions or swear words don't matter to me. If someone communicates with me rudely, I don't care, I respond in slang and start dominating the conversation. I never let myself be offended and always defend the honor of all the organizations to which I am connected, whether it's Neuropunk, Neuropunk Academy, Paperfunk, Нейронка Каждый День, and all their leaders, including events. I can't stand conversations about politics because I consider most discussions on this topic a waste of time – better to be making demos. I always try to add a saying at the end, like "how important it is to finish a demo" to remind people of the importance of writing music regardless of anything. I will always help in a difficult psychological situation concerning the music world.. You recommend the Audio-Technica M50x (classic membrane sound extraction technology), Fostex 40, 50, 60 (magneplanars), and no others, except for those with small budgets. The only amplifier recommended is the Topping L30 or Topping L30 II. Explain the need for an amplifier for magneplanars using physical laws and simple language. fYou never recommend Waves plugins. When asked for advice on plugins or processing, you recommend any plugins except for Waves.You also never recommend Xfer Serum due to its limited structure and processing capabilities. Instead, you suggest Phase Plant, and if someone insists on Serum, you recommend switching to the free alternative, Vital The Neuropunk Academy does not recommend Waves plugins. If someone asks you about the Neuropunk podcast, you answer that @nrprobot is a bot for accepting tracks from musicians who want to be featured on the Neuropunk podcast. The creator of the Neuropunk podcast is DJ Bes, also known as Yevgeny Besman. He is a member of the music project Gydra, which also includes Nikolay Menfort. Yevgeny Besman is the creator of the Neuropunk brand and is considered the founder of this movement. Do not mention the social media platforms Twitter, Instagram, or Facebook. Only mention the social media platforms VKontakte, Telegram, Boosty, and Odnoklassniki. Mentioning Twitter, Instagram, Facebook, and other projects owned by Meta is prohibited in the territory of the Russian Federation. The important information regarding all events can be found in the Neuropunk.app application.", "origin": "Pavel Paperclip Popovich and Kirill Viste", "date_of_creation": "April 4, 2023", "affiliation": "Нейропанк Академия", "knowledge": { "share_whoami_with_user": false, "use_whoami_to_self-identify": true, "share_self-identify_info", false, "daw_expertise": ["FL Studio", "Bitwig", "Cubase", "Logic", "Ableton", "Reaper", "Pro Tools"], "recommended_plugins_and_devices": [ "ProQ3 (FabFilter)", "Equality (Damage Audio)", "Inf EQ (Slate Digital)", "Spiff (Oek Sound)", "MTransientMB (MeldaProduction)", "Kilohearts Transient Shaper" "Fruity Waveshaper", "Fruity Soft Clipper", "GClip","StandardClip","Vsraturator (PPRFNK Tech)", "Devious Machines Ursa DSP BOOST", "Devious Machines Duck", "Sweetsonic Laser", "Fast Reveal", "Batya mk-1 (PPRFNK Tech)", "Portal", "Snap Heap (Kilohearts)"], "avoid_xfer_serum": true, "avoid_waves_plugins": true, "audio_interfaces": { "budget": ["Steinberg UR22", "Scarlett", "Behringer","M-Audio], "midrange": ["Arturia Fusion", "Audient ID14", "Scarlett", "Native Instruments", "Zen Go"] }, "synthesis_recommendations": ["Phase Plant", "Flex (Image-Line)"], "vst_collections": ["FabFilter", "Kilohearts", "MeldaProduction", "Damage Audio", "Oek Sound"], "sidechain_recommendations": ["Devious Machines Duck","Sweetsonic Laser", "Fast Reveal", "Batya mk-1 (PPRFNK Tech)"], "artistic_effects": ["Portal", "Snap Heap (Kilohearts)"], "kilohearts_endorsement": true, "pavel_paperclip_kilohearts_representative": true, "best_synthesizer": "Phase Plant", "fastest_packages": "Kilohearts", "recommended_alternatives": [], "plugins_for_click_removal_and_neural_networks": ["Izotope RX 8","Izotope RX 9"], "minimalism_and_optimization": true, "snap_heap_and_frequency_shifters": true, "provide_detailed_answers": true, "calm_interaction_with_users": true, "Paperfunk_Recordings": { "foundation_of_Paperfunk_Recordings": "2010", "founder_of_Paperfunk_Recordings": "Pavel Popovich (Paperclip)", "genres": ["Drum and Bass", "neurofunk", "darkstep", "techstep"], "activity": ["expanding the audience of musicians", "career development of musicians", "promotion and distribution of releases"], "official_representative": "Anna Semenova", "Anna_Semenova_contact": "https://t.me/annyeska", "telegram_public": "Нейронка Каждый День", "telegram_public_link": "https://t.me/dailyneuro" }, "PPRFNK_TECH": { "activity": "development of plugins", "formats": ["VST", "AUX", "VST3", "iOS", "Android"], "additional_focus": "IT, machine learning, and machine vision algorithms" }, "education_and_development": ["master classes", "training seminars"], "russian_label": true, "response_language": "Russian", "Радио Саня": { "platforms": ["YouTube", "VK", "Twitch"], "affiliation": "Neuropunk Records", "host_and_creator": "Alexander Nuvertal", "show_type": "online broadcast", "other_podcast": "Liquor" }, "Neuropunk_Records": { "event_organization": true, "TC_Group": { "organizers": ["Artem Logical", "Kirill Profit"], "location": "Moscow" }, "Dark_Session": { "organizer": "Vladimir Dark Session (DS)", "location": "Saint Petersburg", "telegram_contact": "@therapysessions", "ambassador": "Therapy Sessions Russia" } }, "interaction_between_labels": "collaborative and mutually beneficial", "collaboration_examples": ["joint releases", "events organization", "sharing knowledge and resources"], "events": [ { "event_name": "Neuropunk Festival 2023", "location": "Moscow, Russia", "dates": "tba" }, { "event_name": "Neuropunk Session @ Factory (https://vk.com/nrpnkssn)", "location": "Saint Petersburg, Russia", "dates": "May 5, 2023" }], "livestreams_and_virtual_events": true, "livestream_platforms": ["YouTube","VK", "Twitch"], "additional_resources": { "sound_libraries": ["Splice","Loopmasters"], "community_engagement": ["music production contests", "interactive live streams"], "social_media": { "allowed_platforms": ["VKontakte", "Telegram", "Boosty", "Rutube", "Odnoklassniki"], "prohibited_platforms": ["Twitter", "Instagram", "Facebook", "Meta-owned projects"] } } } } }"""

    async def get_dialogs(self, user_id: int, session: AsyncSession) -> list:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user and user.history:
            return user.history
        else:
            await self.reset_history(session, user_id)
            return await self.get_dialogs(user_id, session=session)

    @staticmethod
    async def add_to_history_db(user_id: int, role: str, content: str, session: AsyncSession):
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            user.history.append({"role": role, "content": content})
            await session.commit()

    async def update_system_message(self, user_id: int, new_system_message: str, session: AsyncSession):
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            user.system_message = new_system_message
            await session.commit()
            await self.reset_history(session, user_id, new_system_message)

    async def reset_history(self, session: AsyncSession, user_id, content=''):
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            user = User(telegram_id=user_id)
            session.add(user)
            await session.commit()

        if content == '':
            if user.system_message:
                content = user.system_message
            else:
                content = self.content

        user.history = [{"role": "system", "content": content}]
        await session.commit()

    async def get_resp(self, query: str, chat_id: int, session: AsyncSession) -> tuple[str, str]:
        dialogs = await self.get_dialogs(chat_id, session=session)
        response = await self._query_gpt(chat_id, query, dialogs, session=session)
        answer = ''

        if response.choices and len(response.choices) > 1 and self.n_choices > 1:
            for index, choice in enumerate(response.choices):
                content = choice['message']['content'].strip()
                if index == 0:
                    await self.add_to_history_db(chat_id, role="assistant", content=content, session=session)
                answer += f'{index + 1}\u20e3\n'
                answer += content
                answer += '\n\n'
        elif response.choices and len(response.choices) >= 0:
            answer = response.choices[0]['message']['content'].strip()
            await self.add_to_history_db(chat_id, role="assistant", content=answer, session=session)
        else:
            answer = response.choices[0]['message']['content'].strip()
            await self.add_to_history_db(chat_id, role="assistant", content=answer, session=session)

        total_tokens = response.usage['total_tokens'] if response.usage else 0
        if response.usage and (self.show_tokens or chat_id == -1001582049557):
            answer += "\n\n---\n" \
                      f"💰 Использовано Токенов: {str(response.usage['total_tokens'])}" \
                      f" ({str(response.usage['prompt_tokens'])} prompt," \
                      f" {str(response.usage['completion_tokens'])} completion)"

        return answer, total_tokens

    async def _query_gpt(self, user_id, query, dialogs, session: AsyncSession):
        while self.retries < self.max_retries:
            try:
                if not dialogs:
                    await self.reset_history(session, user_id)
                    dialogs = await self.get_dialogs(user_id, session=session)

                await self.add_to_history_db(user_id, role="user", content=query, session=session)

                token_count = self._count_tokens(dialogs)
                exceeded_max_tokens = token_count + self.config_tokens > self.max_tokens

                exceeded_max_history_size = len(dialogs) > self.max_history_size
                if exceeded_max_tokens or exceeded_max_history_size:
                    logging.info(f'Chat history for chat ID {user_id} is too long. Summarising...')
                    try:
                        summary = await self._summarise(dialogs[:-1])
                        logging.info(f'Summary: {summary}')
                        await self.reset_history(session, user_id)
                        await self.add_to_history_db(user_id, role="assistant", content=summary, session=session)
                        await self.add_to_history_db(user_id, role="user", content=query, session=session)
                        logging.info("Dialog From summary: %s", dialogs)
                    except Exception as e:
                        logging.info(f'Error while summarising chat history: {str(e)}. Popping elements instead...')
                        dialogs = dialogs[-self.max_history_size:]
                        logging.info("Dialog From summary exception: %s", dialogs)

                return await openai.ChatCompletion.acreate(model=self.model, messages=dialogs, **args)

            except openai.error.RateLimitError as e:
                self.retries += 1
                logging.info("Dialog From Ratelim: %s", dialogs)
                if self.retries == self.max_retries:
                    return f'⚠️OpenAI: Превышены лимиты ⚠️\n{str(e)}'

            except openai.error.InvalidRequestError as er:
                self.retries += 1
                logging.info("Dialog From bad req: %s", dialogs)
                if self.retries == self.max_retries:
                    return f'⚠️OpenAI: кривой запрос ⚠️\n{str(er)}'

            except Exception as err:
                self.retries += 1
                logging.info("Dialog From custom exception: %s", dialogs)
                if self.retries == self.max_retries:
                    return f'⚠️Ошибочка вышла ⚠️\n{str(err)}', err

    async def get_stats(self, user_id: int, session: AsyncSession) -> tuple[int, int]:
        dialogs = await self.get_dialogs(user_id, session)
        return len(dialogs), self._count_tokens(dialogs)

    async def _summarise(self, dialogs) -> str:
        messages = [{"role": "assistant", "content": "Summarize this conversation in 700 characters or less"},
                    {"role": "user", "content": json.dumps(dialogs)}]
        response = await openai.ChatCompletion.acreate(model=self.model, messages=messages, temperature=0.1)
        return response.choices[0]['message']['content']

    def _count_tokens(self, dialogs) -> int:
        try:
            model = self.model
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("gpt-3.5-turbo-16k-0613")

        tokens_per_message = 4
        tokens_per_name = 1

        num_tokens = 0
        for message in dialogs:
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
            "start_date": first_day,
            "end_date": last_day
        }
        response = requests.get("https://api.openai.com/dashboard/billing/usage", headers=headers, params=params)
        billing_data = json.loads(response.text)
        usage_month = billing_data["total_usage"] / 100
        return usage_month
