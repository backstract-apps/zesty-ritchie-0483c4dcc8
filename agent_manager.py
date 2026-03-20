"""
AgentManager — thread-safe, per-tenant agent registry.

Each unique combination of (tenant_id, agent_name, model, llm_key, system_prompt)
maps to exactly one cached Agent instance.  When any of those attributes change
the old entry is evicted and a fresh Agent is created on the next call.
"""
import sys
import hashlib
import logging
import threading
from dataclasses import dataclass, field
from typing import Optional
from openai import AsyncOpenAI
from pydantic import BaseModel
from agents import (
    Agent,
    Model,
    ModelProvider,
    OpenAIChatCompletionsModel,
    RunConfig,
    Runner,
    ModelSettings,
    function_tool,
    set_tracing_disabled,
)


logger = logging.getLogger(__name__)


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "google/gemini-3.1-flash-lite-preview"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fingerprint(*parts: str) -> str:
    """Stable SHA-256 fingerprint of an ordered set of strings."""
    raw = "\0".join(parts).encode()
    return hashlib.sha256(raw).hexdigest()

def _get_openrouter_client(api_key) -> AsyncOpenAI:
    # api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        sys.exit("Error: OPENROUTER_API_KEY environment variable is not set.")

    return AsyncOpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=api_key,
    )


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AgentKey:
    """
    Immutable cache key.  Two descriptors that share the same key will
    reuse the same Agent instance.
    """
    tenant_id: str
    agent_name: str
    model: str
    # We hash secrets so they never sit in plain-text in a dict key.
    _llm_key_hash: str = field(repr=False)
    _prompt_hash: str = field(repr=False)

    @classmethod
    def build(
        cls,
        tenant_id: str,
        agent_name: str,
        model: str,
        llm_key: str,
        system_prompt: str,
    ) -> "AgentKey":
        return cls(
            tenant_id=tenant_id,
            agent_name=agent_name,
            model=model,
            _llm_key_hash=_fingerprint(llm_key),
            _prompt_hash=_fingerprint(system_prompt),
        )


@dataclass
class AgentDescriptor:
    """Full specification supplied by the caller — never cached directly."""
    tenant_id: str
    agent_name: str
    model: str
    llm_key: str
    system_prompt: str

    def to_key(self) -> AgentKey:
        return AgentKey.build(
            tenant_id=self.tenant_id,
            agent_name=self.agent_name,
            model=self.model,
            llm_key=self.llm_key,
            system_prompt=self.system_prompt,
        )

# ---------------------------------------------------------------------------
# Agent definition
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a helpful research assistant with access to real-time web search.

When the user asks a question:
1. Use the web_search tool to find relevant, up-to-date information.
2. Synthesise the search results into a clear, well-structured answer.
3. Cite your sources by including the URL where you found the information.

If the search results are insufficient, refine your query and search again.
Always prefer recent, authoritative sources.\
"""


class AgentBaseDto(BaseModel):
    agent_name: str
    agent_description: Optional[str]
    model_name: str
    system_prompt: str
    temperature: float


def create_agent(dto: AgentBaseDto) -> Agent:

    """
    name: str,
    handoff_description: str | None = ...,
    tools: list[Tool] = ...,
    mcp_servers: list[MCPServer] = ...,
    mcp_config: MCPConfig = ...,
    instructions: str | ((RunContextWrapper[Any], Agent[Any]) -> MaybeAwaitable[str]) | None = ...,
    prompt: Prompt | DynamicPromptFunction | None = ...,
    handoffs: list[Agent[Any] | Handoff[Any, Any]] = ...,
    model: str | Model | None = ...,
    model_settings: ModelSettings = ...,
    input_guardrails: list[InputGuardrail[Any]] = ...,
    output_guardrails: list[OutputGuardrail[Any]] = ...,
    output_type: type[Any] | AgentOutputSchemaBase | None = ...,
    hooks: AgentHooks[Any] | None = ...,
    tool_use_behavior: StopAtTools | ToolsToFinalOutputFunction[Any] | Literal['run_llm_again', 'stop_on_first_tool'] = ...,
    reset_tool_choice: bool = ...
    """

    return Agent(
        name=dto.agent_name,
        handoff_description=dto.agent_description,
        model=dto.model_name,
        model_settings=ModelSettings(
            temperature=dto.temperature
        ),
        instructions=dto.system_prompt,
        # tools=
        # input_guardrails=
        # output_guardrails=
    )


# ---------------------------------------------------------------------------
# OpenRouterProvider
# ---------------------------------------------------------------------------

class OpenRouterProvider(ModelProvider):
    """Routes all model requests through OpenRouter."""

    def __init__(self, client: AsyncOpenAI) -> None:
        self._client = client

    def get_model(self, model_name: str | None) -> Model:
        return OpenAIChatCompletionsModel(
            model=model_name,
            openai_client=self._client,
        )

async def run_query(query: str, run_config: RunConfig) -> str:
    result = await Runner.run("search_agent", query, run_config=run_config)
    return result.final_output

async def run_agent_query(agent: str, query: str, run_config: RunConfig) -> str:
    result = await Runner.run("search_agent", query, run_config=run_config)
    return result.final_output




# ---------------------------------------------------------------------------
# AgentManager
# ---------------------------------------------------------------------------

class AgentManager:
    """
    Singleton-friendly registry that creates and caches Agent instances.

    Thread-safety: a reentrant lock guards the internal registry so that
    concurrent API requests for the same tenant don't race to build the
    same agent twice.
    """

    def __init__(self) -> None:
        self._registry: dict[AgentKey, Agent] = {}
        self._lock = threading.RLock()
        logger.info("AgentManager initialised.")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_or_create(self, descriptor: AgentDescriptor) -> Agent:
        """Return a cached Agent, creating one if it doesn't exist yet."""
        key = descriptor.to_key()
        with self._lock:
            if key not in self._registry:
                agent = self._build_agent(descriptor)
                self._registry[key] = agent
                logger.info(
                    "Created new agent '%s' for tenant '%s' (model=%s).",
                    descriptor.agent_name,
                    descriptor.tenant_id,
                    descriptor.model,
                )
            else:
                logger.debug(
                    "Reusing cached agent '%s' for tenant '%s'.",
                    descriptor.agent_name,
                    descriptor.tenant_id,
                )
            return self._registry[key]

    def evict(self, descriptor: AgentDescriptor) -> bool:
        """
        Remove an agent from the cache (e.g. after a credential rotation).
        Returns True if an entry was removed.
        """
        key = descriptor.to_key()
        with self._lock:
            removed = self._registry.pop(key, None) is not None
            if removed:
                logger.info(
                    "Evicted agent '%s' for tenant '%s'.",
                    descriptor.agent_name,
                    descriptor.tenant_id,
                )
            return removed

    def evict_tenant(self, tenant_id: str) -> int:
        """Remove every agent belonging to *tenant_id*.  Returns count removed."""
        with self._lock:
            to_remove = [k for k in self._registry if k.tenant_id == tenant_id]
            for k in to_remove:
                del self._registry[k]
            if to_remove:
                logger.info("Evicted %d agent(s) for tenant '%s'.", len(to_remove), tenant_id)
            return len(to_remove)

    def run_sync(self, descriptor: AgentDescriptor, user_prompt: str):
        """Convenience: resolve agent + run synchronously in one call."""
        agent = self.get_or_create(descriptor)
        return Runner.run_sync(agent, user_prompt)

    async def run_async(self, descriptor: AgentDescriptor, user_prompt: str):
        """Convenience: resolve agent + run asynchronously in one call."""
        agent = self.get_or_create(descriptor)
        return await Runner.run(agent, user_prompt)

    @property
    def cached_count(self) -> int:
        with self._lock:
            return len(self._registry)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_agent(descriptor: AgentDescriptor) -> Agent:
        """Construct an Agent wired to the tenant's own OpenAI key."""
        client = AsyncOpenAI(api_key=descriptor.llm_key)
        return Agent(
            name=descriptor.agent_name,
            instructions=descriptor.system_prompt,
            model=descriptor.model,
            # Pass the per-tenant client so the SDK uses the right key.
            model_settings={"openai_client": client},
        )
