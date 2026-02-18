from dataclasses import dataclass

from dotenv import load_dotenv
import os
# from langchain_community.chat_models import ChatLiteLLM
from langchain_litellm import ChatLiteLLM

load_dotenv()

VERDE_API_KEY = os.getenv("VERDE_API_KEY")
VERDE_URL = os.getenv("VERDE_URL")
VERDE_MODEL = os.getenv("VERDE_MODEL")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")


@dataclass
class _ChatResponse:
    """Normalised response wrapper — provides a .content str attribute."""
    content: str


class VerdeBot:
    def __init__(self):
        pass

    def chat(self, message):
        llm = ChatLiteLLM(
            model=f"litellm_proxy/{VERDE_MODEL}",
            api_key=VERDE_API_KEY,
            api_base=VERDE_URL)
        response = llm.invoke(message)
        return response


class ClaudeBot:
    """Bot backed by the Anthropic Claude API.

    Accepts the same message format as VerdeBot: a list of (role, content)
    tuples where role is "system" or "human".
    """

    def __init__(self):
        pass

    def chat(self, message):
        import anthropic

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        system = ""
        messages = []
        for role, content in message:
            if role == "system":
                system = content
            elif role == "human":
                messages.append({"role": "user", "content": content})
            else:
                messages.append({"role": role, "content": content})

        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            system=system,
            messages=messages,
        )
        return _ChatResponse(content=response.content[0].text)
