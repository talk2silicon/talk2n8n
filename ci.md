src/__init__.py:6: error: Cannot find implementation or library stub for module named "src.config"  [import-not-found]
src/__init__.py:6: note: See https://mypy.readthedocs.io/en/stable/running_mypy.html#missing-imports
src/talk2n8n/n8n/tool_factory.py:10: error: Cannot find implementation or library stub for module named "talk2n8n.config"  [import-not-found]
src/talk2n8n/n8n/client.py:10: error: Library stubs not installed for "requests"  [import-untyped]
src/talk2n8n/n8n/client.py:10: note: Hint: "python3 -m pip install types-requests"
src/talk2n8n/n8n/client.py:10: note: (or run "mypy --install-types" to install all missing stub packages)
src/talk2n8n/n8n/client.py:13: error: Cannot find implementation or library stub for module named "talk2n8n.config.settings"  [import-not-found]
src/talk2n8n/n8n/client.py:55: error: Returning Any from function declared to return "Optional[list[dict[str, Any]]]"  [no-any-return]
src/talk2n8n/n8n/client.py:75: error: Returning Any from function declared to return "Optional[dict[str, Any]]"  [no-any-return]
src/talk2n8n/n8n/client.py:113: error: Returning Any from function declared to return "str"  [no-any-return]
src/talk2n8n/config/settings.py:17: error: Unexpected keyword argument "env" for "Field"  [call-arg]
/opt/homebrew/lib/python3.10/site-packages/pydantic/fields.py:673: note: "Field" defined here
src/talk2n8n/config/settings.py:22: error: Unexpected keyword argument "env" for "Field"  [call-arg]
src/talk2n8n/config/settings.py:25: error: Unexpected keyword argument "env" for "Field"  [call-arg]
src/talk2n8n/config/settings.py:32: error: Unexpected keyword argument "env" for "Field"  [call-arg]
src/talk2n8n/config/settings.py:35: error: Unexpected keyword argument "env" for "Field"  [call-arg]
src/talk2n8n/config/settings.py:42: error: Unexpected keyword argument "env" for "Field"  [call-arg]
src/talk2n8n/config/settings.py:62: error: Missing named argument "N8N_WEBHOOK_BASE_URL" for "Settings"  [call-arg]
src/talk2n8n/config/settings.py:62: error: Missing named argument "CLAUDE_API_KEY" for "Settings"  [call-arg]
src/talk2n8n/config/settings.py:62: error: Missing named argument "CLAUDE_MODEL" for "Settings"  [call-arg]
src/talk2n8n/config/settings.py:62: error: Missing named argument "LOG_LEVEL" for "Settings"  [call-arg]
src/talk2n8n/n8n/tool_service.py:8: error: Cannot find implementation or library stub for module named "talk2n8n.n8n.client"  [import-not-found]
src/talk2n8n/n8n/tool_service.py:73: error: Need type annotation for "tools" (hint: "tools: dict[<type>, <type>] = ...")  [var-annotated]
src/talk2n8n/n8n/tool_service.py:117: error: Returning Any from function declared to return "Optional[dict[str, Any]]"  [no-any-return]
src/talk2n8n/n8n/tool_service.py:154: error: Returning Any from function declared to return "dict[str, Any]"  [no-any-return]
src/talk2n8n/n8n/tool_service.py:190: error: Returning Any from function declared to return "Optional[dict[str, Any]]"  [no-any-return]
src/talk2n8n/slack/handler.py:10: error: Cannot find implementation or library stub for module named "talk2n8n.agent.agent"  [import-not-found]
src/talk2n8n/agent/agent.py:24: error: Cannot find implementation or library stub for module named "talk2n8n.n8n.client"  [import-not-found]
src/talk2n8n/agent/agent.py:25: error: Cannot find implementation or library stub for module named "talk2n8n.n8n.tool_service"  [import-not-found]
src/talk2n8n/agent/agent.py:29: error: Cannot find implementation or library stub for module named "talk2n8n.config.settings"  [import-not-found]
src/talk2n8n/agent/agent.py:47: error: No overload variant of "create_model" matches argument types "str", "dict[Any, tuple[type, Any]]"  [call-overload]
src/talk2n8n/agent/agent.py:47: note: Possible overload variants:
src/talk2n8n/agent/agent.py:47: note:     def create_model(str, /, *, __config__: Optional[ConfigDict] = ..., __doc__: Optional[str] = ..., __base__: None = ..., __module__: str = ..., __validators__: Optional[dict[str, Callable[..., Any]]] = ..., __cls_kwargs__: Optional[dict[str, Any]] = ..., **field_definitions: Any) -> type[BaseModel]
src/talk2n8n/agent/agent.py:47: note:     def [ModelT: BaseModel] create_model(str, /, *, __config__: Optional[ConfigDict] = ..., __doc__: Optional[str] = ..., __base__: Union[type[ModelT], tuple[type[ModelT], ...]], __module__: str = ..., __validators__: Optional[dict[str, Callable[..., Any]]] = ..., __cls_kwargs__: Optional[dict[str, Any]] = ..., **field_definitions: Any) -> type[ModelT]
src/talk2n8n/agent/agent.py:97: error: Unexpected keyword argument "model" for "ChatAnthropic"  [call-arg]
src/talk2n8n/agent/agent.py:100: error: Argument "api_key" to "ChatAnthropic" has incompatible type "Optional[str]"; expected "Optional[SecretStr]"  [arg-type]
src/talk2n8n/agent/agent.py:192: error: Incompatible return value type (got "CompiledStateGraph", expected "StateGraph")  [return-value]
src/talk2n8n/agent/agent.py:225: error: Unsupported left operand type for + ("Sequence[BaseMessage]")  [operator]
src/talk2n8n/agent/agent.py:229: error: Unsupported left operand type for + ("Sequence[BaseMessage]")  [operator]
src/talk2n8n/agent/agent.py:279: error: Returning Any from function declared to return "str"  [no-any-return]
Found 33 errors in 7 files (checked 14 source files)
❌ mypy failed
thushara@Thusharas-MacBook-Air-2 talk2n8n % 