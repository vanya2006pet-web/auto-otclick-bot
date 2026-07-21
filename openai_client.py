import logging
import json
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)


def analyze_request(text: str, style: str = "professional") -> dict:
    """
    Analyze user request using GPT and return score, risks, and response.
    Uses OpenAI Responses API with structured output.
    """
    try:
        system_prompt = f"""You are a professional request analyzer. Analyze the user's request and provide:
1. A score from 0-100 indicating the quality and clarity of the request
2. Key risks or potential issues (list 2-3)
3. A professional response in {style} tone

Respond in JSON format with keys: score, risks, response"""

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.7,
            max_tokens=1500
        )

        content = response.choices[0].message.content
        result = json.loads(content)
        
        return {
            "score": result.get("score", 50),
            "risks": result.get("risks", []),
            "response": result.get("response", "Unable to process request")
        }
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response from OpenAI")
        return {
            "score": 0,
            "risks": ["Unable to parse response"],
            "response": "An error occurred while processing your request"
        }
    except Exception as e:
        logger.error(f"Error in analyze_request: {str(e)}")
        return {
            "score": 0,
            "risks": [f"Error: {str(e)}"],
            "response": "An error occurred while processing your request"
        }


def improve_response(original_text: str, response: str, improvement_type: str = "general") -> str:
    """
    Improve an existing response based on improvement type.
    Types: general, concise, detailed, professional
    """
    try:
        prompts = {
            "general": "Improve this response to be more clear and effective",
            "concise": "Make this response shorter and more concise while keeping the key points",
            "detailed": "Expand this response with more details and examples",
            "professional": "Make this response more professional and formal"
        }

        prompt = prompts.get(improvement_type, prompts["general"])

        response_obj = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional text editor. Improve the provided text."},
                {"role": "user", "content": f"Original request: {original_text}\n\nCurrent response: {response}\n\n{prompt}"}
            ],
            temperature=0.7,
            max_tokens=1500
        )

        return response_obj.choices[0].message.content
    except Exception as e:
        logger.error(f"Error in improve_response: {str(e)}")
        return response


def generate_alternative(original_text: str, style: str = "professional") -> str:
    """
    Generate an alternative response to the user's request.
    """
    try:
        response_obj = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": f"You are a professional communicator. Provide an alternative response in {style} tone."},
                {"role": "user", "content": f"Generate an alternative response to this request:\n{original_text}"}
            ],
            temperature=0.8,
            max_tokens=1500
        )

        return response_obj.choices[0].message.content
    except Exception as e:
        logger.error(f"Error in generate_alternative: {str(e)}")
        return "Unable to generate alternative response"
