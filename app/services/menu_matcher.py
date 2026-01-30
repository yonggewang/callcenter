import json
import logging
from openai import OpenAI
from typing import Optional, List, Dict
from ..models.database import Restaurant, MenuItem
from ..core.config import settings

logger = logging.getLogger(__name__)

class MenuMatcher:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("OPENAI_API_KEY not set. MenuMatcher will not work.")

    def match_item(self, speech_text: str, restaurant: Restaurant) -> Optional[MenuItem]:
        """
        Uses LLM to find the best matching menu item for the given speech.
        """
        if not self.client:
            return None

        # 1. Prepare Menu Context (Condensed to save tokens/latency)
        # Format: "id: Name (Category)"
        menu_lines = []
        for item in restaurant.menu:
            menu_lines.append(f"{item.id}: {item.name} ({item.category})")
        
        menu_context = "\n".join(menu_lines)

        # 2. System Prompt
        system_prompt = (
            "You are an intelligent order matching assistant for a restaurant.\n"
            "Your goal is to match the user's spoken request to a specific valid Item ID from the provided menu.\n"
            "Rules:\n"
            "1. Return ONLY a JSON object: {\"item_id\": \"matched_id_or_null\", \"confidence\": 0.0_to_1.0, \"reasoning\": \"brief explanation\"}\n"
            "2. Be helpful: Speech-to-text often makes phonetic mistakes (e.g., 'read' instead of 'sweet', 'poke' instead of 'pork').\n"
            "3. Match based on the most likely intended menu item even if there are typos.\n"
            "4. If it's truly impossible to tell what they want, return null."
        )

        user_prompt = (
            f"Menu:\n{menu_context}\n\n"
            f"User Speech: \"{speech_text}\"\n\n"
            "Match:"
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o", # More powerful reasoning for phone speech typos
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            
            matched_id = data.get("item_id")
            confidence = data.get("confidence", 0)
            
            logger.info(f"NLU Match: {data}")
            
            if matched_id and confidence > 0.6: # Threshold
                 # Find the actual item object
                 for item in restaurant.menu:
                     if item.id == matched_id:
                         return item
                         
            return None

        except Exception as e:
            logger.error(f"MenuMatcher NLU Error: {e}")
            return None

# Global Instance
matcher = MenuMatcher()
