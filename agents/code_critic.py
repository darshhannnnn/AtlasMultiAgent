from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from llm_provider.llm_initializer import get_llm_model
import json

def run_code_critic(user_request, generated_code, provider = None, model_name = None, api_key = None):
    model = get_llm_model(provider=provider, model=model_name, api_key=api_key, temperature=0, max_tokens=2048)
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
    You are a senior software engineer and code reviewer.
    Your task is to review the generated code and determine whether it:
    1. Contains bugs or logical errors.
    2. Has security vulnerabilities.
    3. Has performance issues.
    4. Violates readability or Python best practices.
    5. Fulfills the user's original request.
    Respond ONLY with valid JSON.
    Expected format:
    {{
      "approved": true,
      "code": "<original code>",
      "feedback": ""
    }}
    If problems exist:
    {{
      "approved": false,
      "code": "<improved code or original code>",
      "feedback": "Explain what should be fixed."
    }}
    Do not return markdown.
    Do not wrap the response inside ```json.
    Do not add any text outside the JSON.
    """
        ),
        (
            "human",
    """
    User request: {user_request}
    Generated code: {generated_code}
    """
        )
    ])
    chain = prompt | model | StrOutputParser()
    raw_response = chain.invoke({
        "user_request": user_request,
        "generated_code" : generated_code,
    })
    clean_response = (raw_response.replace("```json","").replace("```","").strip())
    try:
        result = json.loads(clean_response)
    except json.JSONDecodeError:
        result = {
            "approved": False,
            "code": generated_code,
            "feedback": "Could not parse critic response"
        }
    return result