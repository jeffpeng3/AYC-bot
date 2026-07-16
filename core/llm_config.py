from google.genai.types import (
    Tool,
    GenerateContentConfig,
    GoogleSearch,
    SafetySetting,
    HarmCategory,
    HarmBlockThreshold,
)
from core.config import LLM_TEMPERATURE, LLM_MAX_OUTPUT_TOKENS


def make_llm_config(system_instruction: str) -> GenerateContentConfig:
    return GenerateContentConfig(
        system_instruction=system_instruction,
        tools=[Tool(google_search=GoogleSearch())],
        temperature=LLM_TEMPERATURE,
        max_output_tokens=LLM_MAX_OUTPUT_TOKENS,
        safety_settings=[
            SafetySetting(category=HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=HarmBlockThreshold.BLOCK_NONE),
            SafetySetting(category=HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=HarmBlockThreshold.BLOCK_NONE),
            SafetySetting(category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=HarmBlockThreshold.BLOCK_NONE),
            SafetySetting(category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=HarmBlockThreshold.BLOCK_NONE),
        ],
    )
