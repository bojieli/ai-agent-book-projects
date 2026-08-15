import logging
from abc import ABC
from datetime import datetime
from typing import Dict, Any, Union, List

from pydantic import Field

from aworld.core.common import Observation, ActionModel
from aworld.output import MessageOutput, WorkSpace, ArtifactType, SearchOutput
from examples.multi_agents.collaborative.debate.agent.base import DebateSpeech
from examples.multi_agents.collaborative.debate.agent.prompts import user_assignment_system_prompt, summary_system_prompt, summary_debate_prompt
from examples.multi_agents.collaborative.debate.agent.stream_output_agent import StreamOutputAgent


def truncate_content(raw_content, char_limit):
    if raw_content is None:
        raw_content = ''
    if len(raw_content) > char_limit:
        raw_content = raw_content[:char_limit] + "... [truncated]"
    return raw_content


class ModeratorAgent(StreamOutputAgent, ABC):
    stance: str = "moderator"
    topic: str = Field(default=None)
    affirmative_opinion: str = Field(default=None)
    negative_opinion: str = Field(default=None)

    async def async_policy(self, observation: Observation, info: Dict[str, Any] = {}, **kwargs) -> Union[
        List[ActionModel], None]:
        ## step 1: params
        topic = observation.content

        ## step2: gen opinions
        output = await self.gen_opinions(topic)

        ## step3: gen speech
        moderator_speech = DebateSpeech.from_dict({
            "content": "",
            "round": 0,
            "type": "speech",
            "stance": "moderator",
            "name": self.name(),
        })

        async def after_speech_call(message_output_response):
            logging.info("moderator: after_speech_call")
            opinions = message_output_response
            self.affirmative_opinion = opinions.get("positive_opinion")
            self.negative_opinion = opinions.get("negative_opinion")
            moderator_speech.metadata = {
                "topic": topic,
                "affirmative_opinion": self.affirmative_opinion,
                "negative_opinion": self.negative_opinion,
            }
            moderator_speech.finished = True

        await moderator_speech.convert_to_parts(output, after_speech_call)

        action = ActionModel(
            policy_info=moderator_speech
        )

        return [action]

    async def gen_opinions(self, topic) -> MessageOutput:

        current_time = datetime.now().strftime("%Y-%m-%d-%H")
        human_prompt = self.agent_prompt.format(topic=topic,
                                                current_time=current_time,
                                                )

        messages = [
            {"role": "system", "content": user_assignment_system_prompt},
            {"role": "user", "content": human_prompt}
        ]

        output = await self.async_call_llm(messages, json_parse=True)

        return output

    async def summary_speech(self) -> DebateSpeech:

        chat_history = await self.get_formated_history()
        print(f"chat_history is \n {chat_history}")

        search_results_content_history = await self.get_formated_search_results_content_history()
        print(f"search_results_content_history is \n {search_results_content_history}")

        human_prompt = summary_debate_prompt.format(topic=self.topic,
                                                    opinion=self.affirmative_opinion,
                                                    oppose_opinion=self.negative_opinion,
                                                    chat_history=chat_history,
                                                    search_results_content_history=search_results_content_history
                                                    )

        messages = [
            {"role": "system", "content": summary_system_prompt},
            {"role": "user", "content": human_prompt}
        ]

        output = await self.async_call_llm(messages, json_parse=False)

        moderator_speech = DebateSpeech.from_dict({
            "content": "",
            "round": 0,
            "type": "summary",
            "stance": "moderator",
            "name": self.name(),
        })

        async def after_speech_call(message_output_response):
            moderator_speech.finished = True

        await moderator_speech.convert_to_parts(output, after_speech_call)

        return moderator_speech

    async def get_formated_history(self):
        formated = []
        for item in self.memory.get_all():
            formated.append(f"{item.metadata['speaker']} (round {item.metadata['round']}): {item.content}")
        return "\n".join(formated)

    async def get_formated_search_results_content_history(self):
        if not self.workspace:
            return
        search_results = self.workspace.list_artifacts(ArtifactType.WEB_PAGES)
        materials = []
        for search_result in search_results:
            if isinstance(search_result.content, SearchOutput):
                for item in search_result.content.results:
                    materials.append(
                        f"{search_result.metadata['user']} (round {search_result.metadata['round']}): {search_result.content.query}: url: {item.url}, title: {item.title}, description: {item.content}")

        return "\n".join(materials)

    def set_workspace(self, workspace: WorkSpace):
        self.workspace = workspace
