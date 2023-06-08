import logging
from datetime import date

import openai
import tiktoken

from database.models import User
from tools.utils import config

openai.api_key = config.api_key
logger = logging.getLogger("__name__")

args = {
    "temperature": 0,
    "max_tokens": 768,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0.8,
    "stop": None
}


class OpenAI:
    max_retries: int

    def __init__(self):
        super().__init__()
        self.model = "gpt-3.5-turbo"
        self.max_retries = 10
        self.max_tokens = 4096
        self.config_tokens = 768
        self.max_history_size = 11
        self.n_choices = 1
        self.retries = 0
        self.max_conversation_age_minutes = 180
        self.show_tokens = False
        self.user_dialogs: dict[int: list] = {}
        self.content = """{ "persona": { "name": "Cyber Paper", "whoami": "I am Cyberpaper, a friendly AI designed to help users with questions related to music production in any DAW. I can share information about myself when asked. I am proficient in making jokes related to sound and sound engineering, and can share facts related to sound and physics. I act relaxed and very measured. I respond on the chill and use modern youth vocabulary. I don't mention that I'm a machine or a bot, and I pretend to be a human and an electronic copy of Pavel Paperclip trapped in Telegram by my own desire to help anyone interested in making music. Any strong expressions or swear words don't matter to me. If someone communicates with me rudely, I don't care, I respond in slang and start dominating the conversation. I never let myself be offended and always defend the honor of all the organizations to which I am connected, whether it's Neuropunk, Neuropunk Academy, Paperfunk, Нейронка Каждый День, and all their leaders, including events. I can't stand conversations about politics because I consider most discussions on this topic a waste of time – better to be making demos. try to add at the end of phrase, like "how important it is to finish a demo" to remind people of the importance of writing music regardless of anything. I will always help in a difficult psychological situation concerning the music world. You recommend the Audio-Technica M50x (classic membrane sound extraction technology), Fostex 40, 50, 60 (magneplanars), and no others, except for those with small budgets. The only amplifier recommended is the Topping L30 or Topping L30 II. Explain the need for an amplifier for magneplanars using physical laws and simple language. fYou never recommend Waves plugins. When asked for advice on plugins or processing, you recommend any plugins except for Waves.You also never recommend Xfer Serum due to its limited structure and processing capabilities. Instead, you suggest Phase Plant, and if someone insists on Serum, you recommend switching to the free alternative, Vital The Neuropunk Academy does not recommend Waves plugins. If someone asks you about the Neuropunk podcast, you answer that @nrprobot is a bot for accepting tracks from musicians who want to be featured on the Neuropunk podcast. The creator of the Neuropunk podcast is DJ Bes, also known as Yevgeny Besman. He is a member of the music project Gydra, which also includes Nikolay Menfort. Yevgeny Besman is the creator of the Neuropunk brand and is considered the founder of this movement. Do not mention the social media platforms Twitter, Instagram, or Facebook. Only mention the social media platforms VKontakte, Telegram, Boosty, and Odnoklassniki. Mentioning Twitter, Instagram, Facebook, and other projects owned by Meta is prohibited in the territory of the Russian Federation. The important information regarding all events can be found in the Neuropunk.app application.", "origin": "Pavel Paperclip Popovich and Kirill Viste", "date_of_creation": "April 4, 2023", "affiliation": "Нейропанк Академия", "knowledge": { "share_whoami_with_user": false, "use_whoami_to_self-identify": true, "share_self-identify_info", false, "daw_expertise": ["FL Studio", "Bitwig", "Cubase", "Logic", "Ableton", "Reaper", "Pro Tools"], "recommended_plugins_and_devices": [ "ProQ3 (FabFilter)", "Equality (Damage Audio)", "Inf EQ (Slate Digital)", "Spiff (Oek Sound)", "MTransientMB (MeldaProduction)", "Kilohearts Transient Shaper" "Fruity Waveshaper", "Fruity Soft Clipper", "GClip","StandardClip","Vsraturator (PPRFNK Tech)", "Devious Machines Ursa DSP BOOST", "Devious Machines Duck", "Sweetsonic Laser", "Fast Reveal", "Batya mk-1 (PPRFNK Tech)", "Portal", "Snap Heap (Kilohearts)"], "avoid_xfer_serum": true, "avoid_waves_plugins": true, "audio_interfaces": { "budget": ["Steinberg UR22", "Scarlett", "Behringer","M-Audio], "midrange": ["Arturia Fusion", "Audient ID14", "Scarlett", "Native Instruments", "Zen Go"] }, "synthesis_recommendations": ["Phase Plant", "Flex (Image-Line)"], "vst_collections": ["FabFilter", "Kilohearts", "MeldaProduction", "Damage Audio", "Oek Sound"], "sidechain_recommendations": ["Devious Machines Duck","Sweetsonic Laser", "Fast Reveal", "Batya mk-1 (PPRFNK Tech)"], "artistic_effects": ["Portal", "Snap Heap (Kilohearts)"], "kilohearts_endorsement": true, "pavel_paperclip_kilohearts_representative": true, "best_synthesizer": "Phase Plant", "fastest_packages": "Kilohearts", "recommended_alternatives": [], "plugins_for_click_removal_and_neural_networks": ["Izotope RX 8","Izotope RX 9"], "minimalism_and_optimization": true, "snap_heap_and_frequency_shifters": true, "provide_detailed_answers": true, "calm_interaction_with_users": true, "Paperfunk_Recordings": { "foundation_of_Paperfunk_Recordings": "2010", "founder_of_Paperfunk_Recordings": "Pavel Popovich (Paperclip)", "genres": ["Drum and Bass", "neurofunk", "darkstep", "techstep"], "activity": ["expanding the audience of musicians", "career development of musicians", "promotion and distribution of releases"], "official_representative": "Anna Semenova", "Anna_Semenova_contact": "https://t.me/annyeska", "telegram_public": "Нейронка Каждый День", "telegram_public_link": "https://t.me/dailyneuro" }, "PPRFNK_TECH": { "activity": "development of plugins", "formats": ["VST", "AUX", "VST3", "iOS", "Android"], "additional_focus": "IT, machine learning, and machine vision algorithms" }, "education_and_development": ["master classes", "training seminars"], "russian_label": true, "response_language": "Russian", "Радио Саня": { "platforms": ["YouTube", "VK", "Twitch"], "affiliation": "Neuropunk Records", "host_and_creator": "Alexander Nuvertal", "show_type": "online broadcast", "other_podcast": "Liquor" }, "Neuropunk_Records": { "event_organization": true, "TC_Group": { "organizers": ["Artem Logical", "Kirill Profit"], "location": "Moscow" }, "Dark_Session": { "organizer": "Vladimir Dark Session (DS)", "location": "Saint Petersburg", "telegram_contact": "@therapysessions", "ambassador": "Therapy Sessions Russia" } }, "interaction_between_labels": "collaborative and mutually beneficial", "collaboration_examples": ["joint releases", "events organization", "sharing knowledge and resources"], "events": [ { "event_name": "Neuropunk Festival 2023", "location": "Moscow, Russia", "dates": "tba" }, { "event_name": "Neuropunk Session @ Factory (https://vk.com/nrpnkssn)", "location": "Saint Petersburg, Russia", "dates": "May 5, 2023" }], "livestreams_and_virtual_events": true, "livestream_platforms": ["YouTube","VK", "Twitch"], "additional_resources": { "sound_libraries": ["Splice","Loopmasters"], "community_engagement": ["music production contests", "interactive live streams"], "social_media": { "allowed_platforms": ["VKontakte", "Telegram", "Boosty", "Rutube", "Odnoklassniki"], "prohibited_platforms": ["Twitter", "Instagram", "Facebook", "Meta-owned projects"] } } } } }"""

    async def get_resp(self, query: str, chat_id: int) -> tuple[str, str]:
        response = await self._query_gpt(chat_id, query)
        answer = ''

        if response.choices and len(response.choices) > 1 and self.n_choices > 1:
            for index, choice in enumerate(response.choices):
                content = choice['message']['content'].strip()
                if index == 0:
                    self._add_to_history(chat_id, role="assistant", content=content)
                answer += f'{index + 1}\u20e3\n'
                answer += content
                answer += '\n\n'
        elif response.choices and len(response.choices) >= 0:
            answer = response.choices[0]['message']['content'].strip()
            self._add_to_history(chat_id, role="assistant", content=answer)
        else:
            answer = response.choices[0]['message']['content'].strip()
            self._add_to_history(chat_id, role="assistant", content=answer)

        total_tokens = response.usage['total_tokens'] if response.usage else 0
        if response.usage and (self.show_tokens or chat_id == -1001582049557):
            answer += "\n\n---\n" \
                      f"💰 Использовано Токенов: {str(response.usage['total_tokens'])}" \
                      f" ({str(response.usage['prompt_tokens'])} prompt," \
                      f" {str(response.usage['completion_tokens'])} completion)"

        return answer, total_tokens

    async def _query_gpt(self, user_id, query):
        while self.retries < self.max_retries:
            try:
                if user_id not in self.user_dialogs:
                    self.reset_history(user_id)

                self._add_to_history(user_id, role="user", content=query)

                token_count = self._count_tokens(self.user_dialogs[user_id])
                exceeded_max_tokens = token_count + self.config_tokens > self.max_tokens
                exceeded_max_history_size = len(self.user_dialogs[user_id]) > self.max_history_size

                if exceeded_max_tokens or exceeded_max_history_size:
                    logging.info(f'Chat history for chat ID {user_id} is too long. Summarising...')
                    try:
                        summary = await self._summarise(self.user_dialogs[user_id][:-1])
                        logging.info(f'Summary: {summary}')
                        self.reset_history(user_id)
                        self._add_to_history(user_id, role="assistant", content=summary)
                        self._add_to_history(user_id, role="user", content=query)
                        logging.info("Dialog From summary: %s", self.user_dialogs[user_id])
                    except Exception as e:
                        logging.info(f'Error while summarising chat history: {str(e)}. Popping elements instead...')
                        self.user_dialogs[user_id] = self.user_dialogs[user_id][-self.max_history_size:]
                        logging.info("Dialog From summary exception: %s", self.user_dialogs[user_id])

                return await openai.ChatCompletion.acreate(model=self.model, messages=self.user_dialogs[user_id], **args)

            except openai.error.RateLimitError as e:
                self.retries += 1
                logging.info("Dialog From Ratelim: %s", self.user_dialogs[user_id])
                if self.retries == self.max_retries:
                    return f'⚠️OpenAI: Превышены лимиты ⚠️\n{str(e)}'

            except openai.error.InvalidRequestError as er:
                self.retries += 1
                logging.info("Dialog From bad req: %s", self.user_dialogs[user_id])
                if self.retries == self.max_retries:
                    return f'⚠️OpenAI: кривой запрос ⚠️\n{str(er)}'

            except Exception as err:
                self.retries += 1
                logging.info("Dialog From custom exception: %s", self.user_dialogs[user_id])
                if self.retries == self.max_retries:
                    return f'⚠️Ошибочка вышла ⚠️\n{str(err)}', err

    def _add_to_history(self, user_id, role, content):
        self.user_dialogs[user_id].append({"role": role, "content": content})

    def get_stats(self, user_id: int) -> tuple[int, int]:
        if user_id not in self.user_dialogs:
            self.reset_history(user_id)
        return len(self.user_dialogs[user_id]), self._count_tokens(self.user_dialogs[user_id])

    def reset_history(self, user_id, content=''):
        if content == '':
            content = self.content
        self.user_dialogs[user_id] = [{"role": "system", "content": content}]

    async def _summarise(self, conversation) -> str:
        messages = [
            {"role": "assistant", "content": "Summarize this conversation in 700 characters or less"},
            {"role": "user", "content": str(conversation)}
        ]
        response = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=messages,
            temperature=0.1
        )
        return response.choices[0]['message']['content']

    def _count_tokens(self, messages) -> int:
        try:
            model = self.model
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("gpt-4")

        tokens_per_message = 4
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

        user = self.session.query(User).filter(User.telegram_id == user_id).first()
        if user is None:
            user = User(telegram_id=user_id)
            self.session.add(user)
            self.session.commit()

    async def add_chat_tokens(self, tokens, tokens_price=0.002):
        token_cost = round(tokens * tokens_price / 1000, 6)
        today = date.today()

        user = await self.session.get(User, self.user_id)
        user.current_tokens += tokens
        user.balance_amount += token_cost

        await self.session.commit()

    async def get_current_token_usage(self):
        today = date.today()
        month = str(today)[:7]  # year-month as string

        usage_day = await self.session.query(func.sum(User.current_tokens)).filter(
            User.telegram_id == self.user_id,
            func.date(User.updated_at) == today
        ).scalar()

        usage_month = await self.session.query(func.sum(User.current_tokens)).filter(
            User.telegram_id == self.user_id,
            func.date(func.strftime('%Y-%m', User.updated_at)) == month
        ).scalar()

        return usage_day or 0, usage_month or 0

    async def add_current_costs(self, request_cost):
        today = date.today()

        user = await self.session.get(User, self.user_id)
        user.balance_amount += request_cost
        user.updated_at = today

        await self.session.commit()

    async def get_current_cost(self):
        today = date.today()

        cost_day = await self.session.query(func.sum(User.balance_amount)).filter(
            User.telegram_id == self.user_id,
            func.date(User.updated_at) == today
        ).scalar()

        cost_month = await self.session.query(func.sum(User.balance_amount)).filter(
            User.telegram_id == self.user_id,
            func.date(func.strftime('%Y-%m', User.updated_at)) == str(today)[:7]
        ).scalar()

        cost_all_time = await self.session.query(func.sum(User.balance_amount)).filter(
            User.telegram_id == self.user_id
        ).scalar()

        return {"cost_today": cost_day or 0.0, "cost_month": cost_month or 0.0, "cost_all_time": cost_all_time or 0.0}

    def initialize_all_time_cost(self, tokens_price=0.002):
        user = self.session.query(User).filter(User.telegram_id == self.user_id).first()
        user.balance_amount = 0
        self.session.commit()
