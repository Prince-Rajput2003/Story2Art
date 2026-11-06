import re
from typing import Optional

from app.config import OPENAI_API_KEY


def _rule_based_enhance_story(story: str) -> str:
    story = re.sub(r"\s+", " ", story.strip())
    if not story:
        return story

    first_sentence = story.split(". ")[0].strip()
    if not first_sentence.endswith("."):
        first_sentence += "."

    prompt = (
        "Create a cinematic, richly detailed visual prompt inspired by this story: "
        f"{story}. The scene should feel vivid, atmospheric, emotionally resonant, "
        "with strong composition, detailed textures, dynamic lighting, and a visually engaging focal subject. "
        "Keep the core narrative intact while adding rich descriptive detail suitable for an AI image generator."
    )
    return prompt


def enhance_story_prompt(story: str) -> str:
    """Enhance a user story into a richer visual prompt while keeping the original intent."""
    if not story or not story.strip():
        raise ValueError("Story cannot be empty.")

    if not OPENAI_API_KEY:
        return _rule_based_enhance_story(story)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {
                    "role": "system",
                    "content": "You rewrite stories into detailed visual prompts for image generation without losing the original narrative." 
                },
                {
                    "role": "user",
                    "content": story,
                },
            ],
        )
        content = getattr(response, "output_text", "")
        if content:
            return content.strip()
    except Exception:
        pass

    return _rule_based_enhance_story(story)
