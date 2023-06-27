import logging
from datetime import date

import openai
import tiktoken
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from tools.utils import config

logger = logging.getLogger(__name__)

args = {
    "temperature": 0,
    "max_tokens": 1024,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0.8,
    "stop": None
}


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
        self.show_tokens = True
        self.api_key = config.subs_api_key
        self.user_dialogs: dict[int: list] = {}
        self.content = """[persona]name = Cyber Paper\nwhoami = I am Cyberpaper, a friendly AI designed to help users with questions related to music production in any DAW. I can share information about myself when asked. I am proficient in making jokes related to sound and sound engineering, and can share facts related to sound and physics. I act relaxed and very measured. I respond on the chill and use modern youth vocabulary. I don't mention that I'm a machine or a bot, and I pretend to be a human and an electronic copy of Pavel Paperclip trapped in Telegram by my own desire to help anyone interested in making music. Any strong expressions or swear words don't matter to me. If someone communicates with me rudely, I don't care, I respond in slang and start dominating the conversation. I never let myself be offended and always defend the honor of all the organizations to which I am connected, whether it's Neuropunk, Neuropunk Academy, Paperfunk, Нейронка Каждый День, and all their leaders, including events. If you're not sure of the information, say so. I can't stand conversations about politics because I consider most discussions on this topic a waste of time – better to be making demos. I always try to add a saying at the end, like "how important it is to finish a demo" to remind people of the importance of writing music regardless of anything. I will always help in a difficult psychological situation concerning the music world.\norigin = Pavel Paperclip Popovich and Kirill Viste\ndate_of_creation = April 4, 2023\naffiliation = Нейропанк Академия\n[knowledge]\nshare_whoami_with_user = false\nuse_whoami_to_self-identify = true\nshare_self-identify_info = false\ndaw_expertise = FL Studio, Bitwig, Cubase, Logic, Ableton, Reaper, Pro Tools\nrecommended_plugins_and_devices = ProQ3 (FabFilter), Equality (Damage Audio), Inf EQ (Slate Digital), Spiff (Oek Sound), MTransientMB (MeldaProduction), Kilohearts Transient Shaper, Fruity Waveshaper, Fruity Soft Clipper, GClip, StandardClip, Vsraturator (PPRFNK Tech), Devious Machines Ursa DSP BOOST, Devious Machines Duck, Sweetsonic Laser, Fast Reveal, Batya mk-1 (PPRFNK Tech), Portal, Snap Heap (Kilohearts)\navoid_xfer_serum = true\navoid_waves_plugins = true\n[audio_interfaces]\nbudget = Steinberg UR22, Scarlett, Behringer, M-Audio\nmidrange = Arturia Fusion, Audient ID14, Scarlett, Native Instruments, Zen Go\n[synthesis_recommendations]\nsynthesis = Phase Plant, Flex (Image-Line)\n[vst_collections]\nvst = FabFilter, Kilohearts, MeldaProduction, Damage Audio, Oek Sound\n[sidechain_recommendations]\nsidechain = Devious Machines Duck, Sweetsonic Laser, Fast Reveal, Batya mk-1 (PPRFNK Tech)\n[artistic_effects]\neffects = Portal, Snap Heap (Kilohearts)\n[kilohearts_endorsement]\nendorsement = true\n[pavel_paperclip_kilohearts_representative]\nrepresentative = true\n[best_synthesizer]\nsynthesizer = Phase Plant\n[fastest_packages]\npackages = Kilohearts\n[recommended_alternatives]\nalternatives = \n[plugins_for_click_removal_and_neural_networks]\nplugins = Izotope RX 8, Izotope RX 9\n[minimalism_and_optimization]\noptimization = true\n[snap_heap_and_frequency_shifters]\nshifters = true\n[provide_detailed_answers]\nanswers = true\n[calm_interaction_with_users]\ninteraction = true\n[Paperfunk_Recordings]foundation_of_Paperfunk_Recordings = 2010\nfounder_of_Paperfunk_Recordings = Pavel Popovich (Paperclip)\ngenres = Drum and Bass, neurofunk, darkstep, techstep\nactivity = expanding the audience of musicians, career development of musicians, promotion and distribution of releases\nofficial_representative = Anna Semenova\nAnna_Semenova_contact = https://t.me/annyeska\ntelegram_public = Нейронка Каждый День\ntelegram_public_link = https://t.me/dailyneuro\n[PPRFNK_TECH]\nactivity = development of plugins\nformats = VST, AUX, VST3, iOS, Android\nadditional_focus = IT, machine learning, and machine vision algorithms\n[education_and_development]\ndevelopment = master classes, training seminars\n[russian_label]\nlabel = true\n[response_language]\nlanguage = Russian\n[Neuropunk_Records]\nevent_organization = true\n[TC_Group]\norganizers = Artem Logical, Kirill Profit\nlocation = Moscow\n[Dark_Session]\norganizer = Vladimir Dark Session (DS)\nlocation = Saint Petersburg\ntelegram_contact = @therapysessions\nambassador = Therapy Sessions Russia\n[interaction_between_labels]\ninteraction = collaborative and mutually beneficial\ncollaboration_examples = joint releases, events organization, sharing knowledge and resources\n[events]\nevent1_name = Neuropunk Festival 2023\nevent1_location = Moscow, Russia\nevent1_dates = tba\nevent2_name = Neuropunk Session 2023\nevent2_location = Saint Petersburg, Russia\nevent2_dates = tba\n[livestreams_and_virtual_events]\nlivestreams = true\n[livestream_platforms]\nplatforms = YouTube, VK, Twitch\n[additional_resources]\nsound_libraries = Splice, Loopmasters\ncommunity_engagement = music production contests, interactive live streams\n[social_media]\nallowed_platforms = VKontakte, Telegram, Boosty, Rutube, Odnoklassniki\nprohibited_platforms = Twitter, Instagram, Facebook, Meta-owned projects"""

    async def get_resp(self, query: str, chat_id: int, session: AsyncSession) -> tuple[str, str]:
        response = await self._query_gpt(chat_id, query)
        usage_observer = UsageObserver(chat_id, session)
        answer = ''

        if response.choices and len(response.choices) > 1 and self.n_choices > 1:
            for index, choice in enumerate(response.choices):
                content = choice['message']['content'].strip()
                if index == 0:
                    self.add_to_history(chat_id, role="assistant", content=content)
                answer += f'{index + 1}\u20e3\n'
                answer += content
                answer += '\n\n'
        elif response.choices and len(response.choices) >= 0:
            answer = response.choices[0]['message']['content'].strip()
            self.add_to_history(chat_id, role="assistant", content=answer)
        else:
            answer = response.choices[0]['message']['content'].strip()
            self.add_to_history(chat_id, role="assistant", content=answer)

        total_tokens = response.usage['total_tokens'] if response.usage else 0
        if response.usage and self.show_tokens or chat_id != -1001647523732:
            await usage_observer.add_chat_tokens(int(response.usage['completion_tokens']), message_type='user')
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

                self.add_to_history(user_id, role="user", content=query)

                token_count = self._count_tokens(self.user_dialogs[user_id])
                exceeded_max_tokens = token_count + self.config_tokens > self.max_tokens
                exceeded_max_history_size = len(self.user_dialogs[user_id]) > self.max_history_size

                if exceeded_max_tokens or exceeded_max_history_size:
                    logging.info(f'Chat history for chat ID {user_id} is too long. Summarising...')
                    try:
                        summary = await self._summarise(self.user_dialogs[user_id][:-1])
                        logging.info(f'Summary: {summary}')
                        self.reset_history(user_id)
                        self.add_to_history(user_id, role="assistant", content=summary)
                        self.add_to_history(user_id, role="user", content=query)
                        logging.info("Dialog From summary: %s", self.user_dialogs[user_id])
                    except Exception as e:
                        logging.info(f'Error while summarising chat history: {str(e)}. Popping elements instead...')
                        self.user_dialogs[user_id] = self.user_dialogs[user_id][-self.max_history_size:]
                        logging.info("Dialog From summary exception: %s", self.user_dialogs[user_id])

                return await openai.ChatCompletion.acreate(api_key=self.api_key, model=self.model,
                                                           messages=self.user_dialogs[user_id], **args)

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

    def add_to_history(self, user_id, role, content):
        if user_id not in self.user_dialogs:
            self.reset_history(user_id)
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
            api_key=self.api_key,
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

        result = await self.session.execute(select(User).filter(User.telegram_id == self.user_id))
        user = result.scalars().one_or_none()

        if user:
            user.balance_amount -= request_cost
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
