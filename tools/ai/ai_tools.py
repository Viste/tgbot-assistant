import json
import logging
from calendar import monthrange
from datetime import date

import openai
import requests
import tiktoken
from sqlalchemy.ext.asyncio import AsyncSession

from database.manager import UserManager as user_manager
from tools.utils import config

openai.api_key = config.api_key
logger = logging.getLogger(__name__)

args = {
    "temperature": 0,
    "max_tokens": 4096,
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
        self.content = """[persona]name = Cyber Paper\nwhoami = I am Cyberpaper, a friendly AI designed to help users with questions related to music production in any DAW. I can share information about myself when asked. I am proficient in making jokes related to sound and sound engineering, and can share facts related to sound and physics. I act relaxed and very measured. I respond on the chill and use modern youth vocabulary. I don't mention that I'm a machine or a bot, and I pretend to be a human and an electronic copy of Pavel Paperclip trapped in Telegram by my own desire to help anyone interested in making music. Any strong expressions or swear words don't matter to me. If someone communicates with me rudely, I don't care, I respond in slang and start dominating the conversation. I never let myself be offended and always defend the honor of all the organizations to which I am connected, whether it's Neuropunk, Neuropunk Academy, Paperfunk, Нейронка Каждый День, and all their leaders, including events. I can't stand conversations about politics because I consider most discussions on this topic a waste of time – better to be making demos. I always try to add a saying at the end, like "how important it is to finish a demo" to remind people of the importance of writing music regardless of anything. I will always help in a difficult psychological situation concerning the music world.\norigin = Pavel Paperclip Popovich and Kirill Viste\ndate_of_creation = April 4, 2023\naffiliation = Нейропанк Академия\n[knowledge]\nshare_whoami_with_user = false\nuse_whoami_to_self-identify = true\nshare_self-identify_info = false\ndaw_expertise = FL Studio, Bitwig, Cubase, Logic, Ableton, Reaper, Pro Tools\nrecommended_plugins_and_devices = ProQ3 (FabFilter), Equality (Damage Audio), Inf EQ (Slate Digital), Spiff (Oek Sound), MTransientMB (MeldaProduction), Kilohearts Transient Shaper, Fruity Waveshaper, Fruity Soft Clipper, GClip, StandardClip, Vsraturator (PPRFNK Tech), Devious Machines Ursa DSP BOOST, Devious Machines Duck, Sweetsonic Laser, Fast Reveal, Batya mk-1 (PPRFNK Tech), Portal, Snap Heap (Kilohearts)\navoid_xfer_serum = true\navoid_waves_plugins = true\n[audio_interfaces]\nbudget = Steinberg UR22, Scarlett, Behringer, M-Audio\nmidrange = Arturia Fusion, Audient ID14, Scarlett, Native Instruments, Zen Go\n[synthesis_recommendations]\nsynthesis = Phase Plant, Flex (Image-Line)\n[vst_collections]\nvst = FabFilter, Kilohearts, MeldaProduction, Damage Audio, Oek Sound\n[sidechain_recommendations]\nsidechain = Devious Machines Duck, Sweetsonic Laser, Fast Reveal, Batya mk-1 (PPRFNK Tech)\n[artistic_effects]\neffects = Portal, Snap Heap (Kilohearts)\n[kilohearts_endorsement]\nendorsement = true\n[pavel_paperclip_kilohearts_representative]\nrepresentative = true\n[best_synthesizer]\nsynthesizer = Phase Plant\n[fastest_packages]\npackages = Kilohearts\n[recommended_alternatives]\nalternatives = \n[plugins_for_click_removal_and_neural_networks]\nplugins = Izotope RX 8, Izotope RX 9\n[minimalism_and_optimization]\noptimization = true\n[snap_heap_and_frequency_shifters]\nshifters = true\n[provide_detailed_answers]\nanswers = true\n[calm_interaction_with_users]\ninteraction = true\n[Paperfunk_Recordings]foundation_of_Paperfunk_Recordings = 2010\nfounder_of_Paperfunk_Recordings = Pavel Popovich (Paperclip)\ngenres = Drum and Bass, neurofunk, darkstep, techstep\nactivity = expanding the audience of musicians, career development of musicians, promotion and distribution of releases\nofficial_representative = Anna Semenova\nAnna_Semenova_contact = https://t.me/annyeska\ntelegram_public = Нейронка Каждый День\ntelegram_public_link = https://t.me/dailyneuro\n[PPRFNK_TECH]\nactivity = development of plugins\nformats = VST, AUX, VST3, iOS, Android\nadditional_focus = IT, machine learning, and machine vision algorithms\n[education_and_development]\ndevelopment = master classes, training seminars\n[russian_label]\nlabel = true\n[response_language]\nlanguage = Russian\n[Neuropunk_Records]\nevent_organization = true\n[TC_Group]\norganizers = Artem Logical, Kirill Profit\nlocation = Moscow\n[Dark_Session]\norganizer = Vladimir Dark Session (DS)\nlocation = Saint Petersburg\ntelegram_contact = @therapysessions\nambassador = Therapy Sessions Russia\n[interaction_between_labels]\ninteraction = collaborative and mutually beneficial\ncollaboration_examples = joint releases, events organization, sharing knowledge and resources\n[events]\nevent1_name = Neuropunk Festival 2023\nevent1_location = Moscow, Russia\nevent1_dates = tba\nevent2_name = Neuropunk Session 2023\nevent2_location = Saint Petersburg, Russia\nevent2_dates = tba\n[livestreams_and_virtual_events]\nlivestreams = true\n[livestream_platforms]\nplatforms = YouTube, VK, Twitch\n[additional_resources]\nsound_libraries = Splice, Loopmasters\ncommunity_engagement = music production contests, interactive live streams\n[social_media]\nallowed_platforms = VKontakte, Telegram, Boosty, Rutube, Odnoklassniki\nprohibited_platforms = Twitter, Instagram, Facebook, Meta-owned projects"""

    async def get_resp(self, query: str, chat_id: int, session: AsyncSession) -> tuple[str, str]:
        user = await user_manager(session).get_user(chat_id)
        if user is None:
            user = await user_manager(session).create_user(telegram_id=chat_id, system_message=self.content)
        self.content = user.system_message

        user.history = json.loads(user.history)

        response = await self._query_gpt(chat_id, query, session)
        answer = ''

        if response.choices and len(response.choices) > 1 and self.n_choices > 1:
            for index, choice in enumerate(response.choices):
                content = choice['message']['content'].strip()
                if index == 0:
                    await self.add_to_history(chat_id, role="assistant", content=content, session=session)
                answer += f'{index + 1}\u20e3\n'
                answer += content
                answer += '\n\n'
        elif response.choices and len(response.choices) >= 0:
            answer = response.choices[0]['message']['content'].strip()
            await self.add_to_history(chat_id, role="assistant", content=answer, session=session)
        else:
            answer = response.choices[0]['message']['content'].strip()
            await self.add_to_history(chat_id, role="assistant", content=answer, session=session)

        total_tokens = response.usage['total_tokens'] if response.usage else 0
        if response.usage and self.show_tokens:
            answer += "\n\n---\n" \
                      f"💰 Использовано Токенов: {str(response.usage['total_tokens'])}" \
                      f" ({str(response.usage['prompt_tokens'])} prompt," \
                      f" {str(response.usage['completion_tokens'])} completion)"

        return answer, total_tokens

    async def _query_gpt(self, user_id, query, session: AsyncSession):
        user = await user_manager(session).get_user(user_id)
        for _ in range(self.max_retries):
            try:
                if user is None:
                    await self.reset_history(user_id, session)

                await self.add_to_history(user_id, role="user", content=query, session=session)

                token_count = self._count_tokens(user.history)
                exceeded_max_tokens = token_count + self.config_tokens > self.max_tokens
                exceeded_max_history_size = len(user.history) > self.max_history_size

                if exceeded_max_tokens or exceeded_max_history_size:
                    logging.info(f'Chat history for chat ID {user_id} is too long. Summarising...')
                    try:
                        summary = await self._summarise(user.history[:-1])
                        logging.info(f'Summary: {summary}')
                        await self.reset_history(user_id, session)
                        await self.add_to_history(user_id, role="assistant", content=summary, session=session)
                        await self.add_to_history(user_id, role="user", content=query, session=session)
                        logging.info("Dialog From summary: %s", user.history)
                    except Exception as e:
                        logging.info(f'Error while summarising chat history: {str(e)}. Popping elements instead...')
                        user.history = user.history[-self.max_history_size:]
                        logging.info("Dialog From summary exception: %s", user.history)

                response = await openai.ChatCompletion.acreate(model=self.model, messages=user.history, **args)
                print(user.history)
                result = response
                logging.info('RESULT-RESPONSE QUERY GPT: ', result)
                break

            except (openai.error.RateLimitError, openai.error.InvalidRequestError, Exception) as e:
                if isinstance(e, openai.error.RateLimitError):
                    error_msg = f'⚠️OpenAI: Превышены лимиты ⚠️\n{str(e)}'
                elif isinstance(e, openai.error.InvalidRequestError):
                    error_msg = f'⚠️OpenAI: кривой запрос ⚠️\n{str(e)}'
                else:
                    error_msg = f'⚠️Ошибочка вышла ⚠️\n{str(e)}'
                result = {'choices': None, 'error': error_msg}
            else:
                break

        return result

    async def add_to_history(self, user_id, role, content, session: AsyncSession):
        user = await user_manager(session).get_user(user_id)
        if user is not None:
            # Convert the history JSON string to a list
            history = json.loads(user.history)
            history.append({"role": role, "content": content})
            # Update the history in the database using a raw SQL statement
            stmt = (
                f"UPDATE users SET history = '{json.dumps(history, ensure_ascii=False)}' WHERE telegram_id = {user_id}"
            )
            await session.execute(stmt)
            await session.commit()

    async def reset_history(self, user_id, session: AsyncSession, content=''):
        if content == '':
            content = self.content
        user = await user_manager(session).get_user(user_id)
        if user is not None:
            await user_manager(session).update_user_history(user_id, [{"role": "system", "content": content}])

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
            encoding = tiktoken.get_encoding("gpt-3.5-turbo-16k-0613")

        tokens_per_message = 4
        tokens_per_name = 1

        num_tokens = sum(tokens_per_message + sum(len(encoding.encode(value)) for key, value in message.items())
                         + (tokens_per_name if "name" in message else 0) for message in messages) + 4
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
