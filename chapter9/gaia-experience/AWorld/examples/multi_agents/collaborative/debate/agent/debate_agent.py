import logging
from abc import ABC
from typing import Dict, Any, Union, List, Literal, Optional
from datetime import datetime
import uuid

from aworld.models.model_response import ToolCall
from examples.multi_agents.collaborative.debate.agent.base import DebateSpeech
from examples.multi_agents.collaborative.debate.agent.prompts import user_assignment_prompt, user_assignment_system_prompt, affirmative_few_shots, \
    negative_few_shots, \
    user_debate_prompt
from examples.multi_agents.collaborative.debate.agent.search.search_engine import SearchEngine
from examples.multi_agents.collaborative.debate.agent.search.tavily_search_engine import TavilySearchEngine
from examples.multi_agents.collaborative.debate.agent.stream_output_agent import StreamOutputAgent
from aworld.config import AgentConfig
from aworld.core.common import Observation, ActionModel
from aworld.output import SearchOutput, SearchItem, MessageOutput
from aworld.output.artifact import ArtifactType


def truncate_content(raw_content, char_limit):
    if raw_content is None:
        raw_content = ''
    if len(raw_content) > char_limit:
        raw_content = raw_content[:char_limit] + "... [truncated]"
    return raw_content

class DebateAgent(StreamOutputAgent, ABC):

    stance: Literal["affirmative", "negative"]

    def __init__(self, conf: AgentConfig, name: str, stance: Literal["affirmative", "negative"], search_engine: Optional[SearchEngine] = TavilySearchEngine()):
        conf.name = name
        super().__init__(conf, name)
        self.steps = 0
        self.stance = stance
        self.search_engine = search_engine

    async def speech(self, topic: str, opinion: str,oppose_opinion: str, round: int, speech_history: list[DebateSpeech]) -> DebateSpeech:
        observation = Observation(content=self.get_latest_speech(speech_history).content if self.get_latest_speech(speech_history) else "")
        info = {
            "topic": topic,
            "round": round,
            "opinion": opinion,
            "oppose_opinion": oppose_opinion,
            "history": speech_history
        }
        actions = await self.async_policy(observation, info)

        return actions[0].policy_info


    async def async_policy(self, observation: Observation, info: Dict[str, Any] = {}, **kwargs) -> Union[
        List[ActionModel], None]:
        ## step 1: params
        opponent_claim = observation.content
        round = info["round"]
        opinion = info["opinion"]
        oppose_opinion = info["oppose_opinion"]
        topic = info["topic"]
        history: list[DebateSpeech] = info["history"]

        #Event.emit("xxx")
        ## step2: gen keywords
        keywords = await self.gen_keywords(topic, opinion, oppose_opinion, opponent_claim, history)
        logging.info(f"gen keywords = {keywords}")

        ## step3：search_webpages
        search_results = await self.search_webpages(keywords, max_results=5)
        for search_result in search_results:
            logging.info(f"keyword#{search_result['query']}-> result size is {len(search_result['results'])}")
            search_item = {
                "query": search_result.get("query", ""),
                "results": [SearchItem(title=result["title"],url=result["url"], content=result['content'], raw_content=result['raw_content'], metadata={}) for result in search_result["results"]],
                "origin_tool_call": ToolCall.from_dict({
                    "id": f"call_search",
                    "type": "function",
                    "function": {
                        "name": "search",
                        "arguments": keywords
                    }
                }),
                "task_id": self.context.task_id
            }
            search_output = SearchOutput.from_dict(search_item)
            await self.workspace.create_artifact(
                artifact_type=ArtifactType.WEB_PAGES,
                artifact_id=str(uuid.uuid4()),
                content=search_output,
                metadata={
                    "query": search_output.query,
                    "user": self.name(),
                    "round": info["round"],
                    "opinion": info["opinion"],
                    "oppose_opinion": info["oppose_opinion"],
                    "topic": info["topic"],
                    "tags": [f"user#{self.name()}",f"Rounds#{info['round']}"]
                }
            )

        ## step4 gen result
        user_response = await self.gen_statement(topic, opinion, oppose_opinion, opponent_claim, history, search_results)

        logging.info(f"user_response is {user_response}")

        ## step3: gen speech
        speech = DebateSpeech.from_dict({
            "round": round,
            "type": "speech",
            "stance": self.stance,
            "name": self.name(),
        })

        async def after_speech_call(message_output_response):
            logging.info(f"{self.stance}#{self.name()}: after_speech_call")
            speech.metadata = {}
            speech.content = message_output_response
            speech.finished = True

        await speech.convert_to_parts(user_response, after_speech_call)

        action = ActionModel(
            policy_info=speech
        )

        return [action]


    async def gen_keywords(self, topic, opinion, oppose_opinion, last_oppose_speech_content, history):

        current_time = datetime.now().strftime("%Y-%m-%d-%H")
        human_prompt = user_assignment_prompt.format(topic=topic,
                                                     opinion=opinion,
                                                     oppose_opinion=oppose_opinion,
                                                     last_oppose_speech_content=last_oppose_speech_content,
                                                     current_time = current_time,
                                                     limit=2
                                                     )

        messages = [{'role': 'system', 'content': user_assignment_system_prompt},
                    {'role': 'user', 'content': human_prompt}]

        output = await self.async_call_llm(messages)

        response = await output.get_finished_response()

        return response.split(",")

    async def search_webpages(self, keywords, max_results):
        return await self.search_engine.async_batch_search(queries=keywords, max_results=max_results)

    async def gen_statement(self, topic, opinion, oppose_opinion, opponent_claim, history, search_results) -> MessageOutput:
        search_results_content = ""
        for search_result in search_results:
            search_results_content += f"SearchQuery: {search_result['query']}"
            search_results_content += "\n\n".join([truncate_content(s['content'], 1000) for s in search_result['results']])

        unique_history = history
        # if len(history) >= 2:
        #     for i in range(len(history)):
        #         # Check if the current element is the same as the next one
        #         if i == len(history) - 1 or history[i] != history[i+1]:
        #             # Add the current element to the result list
        #             unique_history.append(history[i])


        affirmative_chat_history = ""
        negative_chat_history = ""

        if len(unique_history) >= 2:
            if self.stance == "affirmative":
                for speech in unique_history[:-1]:
                    if speech.stance == "affirmative":
                        affirmative_chat_history = affirmative_chat_history + "You: " + speech.content + "\n"
                    elif speech.stance == "negative":
                        affirmative_chat_history = affirmative_chat_history + "Your Opponent: " + speech.content + "\n"

            elif self.stance == "negative":
                for speech in unique_history[:-1]:
                    if speech.stance == "negative":
                        negative_chat_history = negative_chat_history + "You: " + speech.content + "\n"
                    elif speech.stance == "affirmative":
                        negative_chat_history = negative_chat_history + "Your Opponent: " + speech.content + "\n"

        few_shots = ""
        chat_history = ""

        if self.stance == "affirmative":
            chat_history = affirmative_chat_history
            few_shots = affirmative_few_shots

        elif self.stance == "negative":
            chat_history = negative_chat_history
            few_shots = negative_few_shots

        human_prompt = user_debate_prompt.format(topic=topic,
                                                opinion=opinion,
                                                oppose_opinion=oppose_opinion,
                                                last_oppose_speech_content=opponent_claim,
                                                search_results_content=search_results_content,
                                                chat_history = chat_history,
                                                few_shots = few_shots
                                                )

        messages = [{'role': 'system', 'content': user_assignment_system_prompt},
                    {'role': 'user', 'content': human_prompt}]

        return await self.async_call_llm(messages)

    def get_latest_speech(self, history: list[DebateSpeech]):
        """
        get the latest speech from history
        """
        if len(history) == 0:
            return None
        return history[-1]

    def set_workspace(self, workspace):
        self.workspace = workspace
