from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from ..models.database import MenuItem, Restaurant, find_item_by_id, Option, OptionChoice
from ..core.prompts import Prompts
from ..core.config import settings
from twilio.twiml.voice_response import VoiceResponse, Gather
import os
import json
import datetime
import logging
import re

logger = logging.getLogger(__name__)

class CallStage(str, Enum):
    INIT = "INIT"
    ORDERING_ID = "ORDERING_ID"
    SELECTING_VARIETY = "SELECTING_VARIETY"
    CONFIRMING_ITEM = "CONFIRMING_ITEM"
    ASK_ADD_MORE = "ASK_ADD_MORE"
    CONFIRMING_ORDER = "CONFIRMING_ORDER"
    COMPLETED = "COMPLETED"

class SelectedOption(BaseModel):
    option_name: str
    choice_name: str
    price_extra: float

class OrderItem(BaseModel):
    item: MenuItem
    selected_options: List[SelectedOption] = []
    
    @property
    def total_price(self) -> float:
        return self.item.price + sum(opt.price_extra for opt in self.selected_options)

class CallContext(BaseModel):
    call_sid: str
    stage: CallStage = CallStage.INIT
    restaurant_id: str
    current_order: List[OrderItem] = []
    
    # Temporary state for current item being ordered
    pending_item: Optional[MenuItem] = None
    pending_options: List[SelectedOption] = []
    current_option_index: int = 0
    
    silence_count: int = 0
    
    class Config:
        arbitrary_types_allowed = True

sessions: Dict[str, CallContext] = {}

class FlowManager:
    def __init__(self):
        pass # URL now passed per request for robustness

    def get_context(self, call_sid: str, restaurant: Restaurant) -> CallContext:
        if call_sid not in sessions:
            sessions[call_sid] = CallContext(call_sid=call_sid, restaurant_id=restaurant.id)
        return sessions[call_sid]
    
    def save_context(self, ctx: CallContext):
        sessions[ctx.call_sid] = ctx

    def process_input(self, call_sid: str, input_text: str, restaurant: Restaurant, callback_url: str) -> str:
        ctx = self.get_context(call_sid, restaurant)
        response = VoiceResponse()
        logger.info(f"[process_input] CallSid: {call_sid}, State: {ctx.stage}, Input: '{input_text}'")
        
        try:
            # 1. Handle Silence
            if not input_text or not input_text.strip():
                ctx.silence_count += 1
                if ctx.silence_count >= 3:
                    response.say(Prompts.FALLBACK_GOODBYE)
                    response.hangup()
                    return str(response)
                return self._respond(ctx, response, Prompts.ERROR_SILENCE, callback_url)
            
            ctx.silence_count = 0
            text = input_text.lower().strip()

            # 1.5 Handle INIT stage (if session was lost or started in process_input)
            if ctx.stage == CallStage.INIT:
                ctx.stage = CallStage.ORDERING_ID

            # 2. State Machine
            if ctx.stage == CallStage.ORDERING_ID:
                return self._handle_ordering_id(ctx, text, restaurant, response, callback_url)
                
            elif ctx.stage == CallStage.SELECTING_VARIETY:
                return self._handle_selecting_variety(ctx, text, restaurant, response, callback_url)
                
            elif ctx.stage == CallStage.CONFIRMING_ITEM:
                return self._handle_confirming_item(ctx, text, restaurant, response, callback_url)
                
            elif ctx.stage == CallStage.ASK_ADD_MORE:
                return self._handle_ask_add_more(ctx, text, restaurant, response, callback_url)
                
            elif ctx.stage == CallStage.CONFIRMING_ORDER:
                return self._handle_confirming_order(ctx, text, restaurant, response, callback_url)

            # If stage is unknown or COMPLETED
            return self._respond(ctx, response, Prompts.ERROR_NOT_UNDERSTOOD, callback_url)
            
        except Exception as e:
            import traceback
            logger.error(f"Error in FlowManager: {e}")
            logger.error(traceback.format_exc())
            # Fallback to a safe response to avoid hangup
            response = VoiceResponse()
            response.say("I'm sorry, I encountered an internal error. Let's start over.")
            ctx.stage = CallStage.ORDERING_ID
            self.save_context(ctx)
            return self._respond(ctx, response, Prompts.SPECIFY_ID, callback_url)

    def start_call(self, call_sid: str, restaurant: Restaurant, callback_url: str) -> str:
        ctx = self.get_context(call_sid, restaurant)
        ctx.stage = CallStage.ORDERING_ID
        self.save_context(ctx)
        
        response = VoiceResponse()
        return self._respond(ctx, response, Prompts.GREETING, callback_url)

    # --- Handlers ---

    def _handle_ordering_id(self, ctx: CallContext, text: str, restaurant: Restaurant, response: VoiceResponse, callback_url: str) -> str:
        item = find_item_by_id(text, restaurant)
        if not item:
            from ..models.database import find_item_by_speech
            item = find_item_by_speech(text, restaurant)
            
        if item:
            logger.info(f"[_handle_ordering_id] Found item: {item.name}, Options count: {len(item.options)}")
            ctx.pending_item = item
            ctx.pending_options = []
            
            if item.options:
                ctx.stage = CallStage.SELECTING_VARIETY
                ctx.current_option_index = 0
                self.save_context(ctx)
                
                opt = item.options[0]
                options_list = ", ".join([f"{c.id} for {c.name}" for c in opt.choices])
                msg = Prompts.VARIETY_PROMPT_TEMPLATE.format(dish_name=item.name, options_list=options_list)
                return self._respond(ctx, response, msg, callback_url)
            else:
                ctx.stage = CallStage.CONFIRMING_ITEM
                self.save_context(ctx)
                msg = Prompts.CONFIRM_DISH_TEMPLATE.format(dish_name=item.name)
                logger.info(f"[_handle_ordering_id] Transitioning to CONFIRMING_ITEM for {item.name}")
                return self._respond(ctx, response, msg, callback_url)
        
        logger.warning(f"[_handle_ordering_id] No item found for input: '{text}'")
        return self._respond(ctx, response, Prompts.ID_NOT_FOUND, callback_url)

    def _handle_selecting_variety(self, ctx: CallContext, text: str, restaurant: Restaurant, response: VoiceResponse, callback_url: str) -> str:
        if not ctx.pending_item:
            ctx.stage = CallStage.ORDERING_ID
            return self._respond(ctx, response, Prompts.SPECIFY_ID, callback_url)

        current_opt = ctx.pending_item.options[ctx.current_option_index]
        
        selected_choice = None
        digits = "".join(re.findall(r"\d", text))
        
        if digits:
            for c in current_opt.choices:
                if c.id == digits[0]:
                    selected_choice = c
                    break
        else:
            for c in current_opt.choices:
                if c.name.lower() in text:
                    selected_choice = c
                    break
                    
        if selected_choice:
            ctx.pending_options.append(SelectedOption(
                option_name=current_opt.name,
                choice_name=selected_choice.name,
                price_extra=selected_choice.price_extra
            ))
            
            ctx.current_option_index += 1
            if ctx.current_option_index < len(ctx.pending_item.options):
                opt = ctx.pending_item.options[ctx.current_option_index]
                options_list = ", ".join([f"{c.id} for {c.name}" for c in opt.choices])
                msg = f"Next, for {ctx.pending_item.name}, {opt.name}? {options_list}"
                self.save_context(ctx)
                return self._respond(ctx, response, msg, callback_url)
            else:
                ctx.stage = CallStage.CONFIRMING_ITEM
                self.save_context(ctx)
                options_str = " with " + ", ".join([o.choice_name for o in ctx.pending_options]) if ctx.pending_options else ""
                msg = Prompts.CONFIRM_DISH_TEMPLATE.format(dish_name=f"{ctx.pending_item.name}{options_str}")
                return self._respond(ctx, response, msg, callback_url)
        
        return self._respond(ctx, response, Prompts.INVALID_SELECTION, callback_url)

    def _handle_confirming_item(self, ctx: CallContext, text: str, restaurant: Restaurant, response: VoiceResponse, callback_url: str) -> str:
        # Strict checking for 1 or 2 to avoid "20" matching "2"
        digits = re.findall(r"\b\d\b", text) # Only single digits as whole words
        
        is_yes = "1" in digits or "yes" in text or "yeah" in text or "correct" in text
        is_no = "2" in digits or "no" in text or "not" in text or "wrong" in text
        
        # Fallback if no single digit was found but "1" or "2" is the only thing said
        if not digits:
            if text.strip() == "1": is_yes = True
            if text.strip() == "2": is_no = True
        
        if is_yes:
            order_item = OrderItem(item=ctx.pending_item, selected_options=ctx.pending_options)
            ctx.current_order.append(order_item)
            
            added_name = ctx.pending_item.name
            ctx.pending_item = None
            ctx.pending_options = []
            ctx.stage = CallStage.ASK_ADD_MORE
            self.save_context(ctx)
            
            msg = Prompts.ADD_MORE.format(dish_name=added_name)
            return self._respond(ctx, response, msg, callback_url)
        
        elif is_no:
            ctx.pending_item = None
            ctx.pending_options = []
            ctx.stage = CallStage.ORDERING_ID
            self.save_context(ctx)
            return self._respond(ctx, response, "Okay, let's try again. " + Prompts.SPECIFY_ID, callback_url)
            
        return self._respond(ctx, response, "I'm sorry, please say 1 for yes or 2 for no.", callback_url)

    def _handle_ask_add_more(self, ctx: CallContext, text: str, restaurant: Restaurant, response: VoiceResponse, callback_url: str) -> str:
        digits = re.findall(r"\b\d\b", text)
        is_yes = "1" in digits or "yes" in text or "yeah" in text or "more" in text or "continue" in text
        is_no = "2" in digits or "no" in text or "that's it" in text or "done" in text or "finished" in text or "enough" in text
        
        if not digits:
            if text.strip() == "1": is_yes = True
            if text.strip() == "2": is_no = True
        
        if is_yes:
            ctx.stage = CallStage.ORDERING_ID
            self.save_context(ctx)
            return self._respond(ctx, response, "Great. " + Prompts.SPECIFY_ID, callback_url)
        elif is_no:
            ctx.stage = CallStage.CONFIRMING_ORDER
            self.save_context(ctx)
            
            summary, total = self._calc_summary(ctx)
            msg = Prompts.SUMMARY_TEMPLATE.format(order_summary=summary, total_price=total)
            return self._respond(ctx, response, msg, callback_url)
            
        item = find_item_by_id(text, restaurant)
        if item:
            return self._handle_ordering_id(ctx, text, restaurant, response, callback_url)
            
        return self._respond(ctx, response, "Would you like to add more? Say 1 for yes or 2 for no.", callback_url)

    def _handle_confirming_order(self, ctx: CallContext, text: str, restaurant: Restaurant, response: VoiceResponse, callback_url: str) -> str:
        digits = re.findall(r"\b\d\b", text)
        is_yes = "1" in digits or "yes" in text or "place" in text or "confirm" in text
        is_no = "2" in digits or "no" in text or "cancel" in text

        if not digits:
            if text.strip() == "1": is_yes = True
            if text.strip() == "2": is_no = True
        
        if is_yes:
            self._save_order_disk(ctx, restaurant)
            ctx.stage = CallStage.COMPLETED
            self.save_context(ctx)
            response.say(Prompts.FINAL_SUCCESS)
            response.hangup()
            return str(response)
        elif is_no:
            ctx.stage = CallStage.COMPLETED
            self.save_context(ctx)
            response.say(Prompts.FINAL_CANCEL)
            response.hangup()
            return str(response)
            
        return self._respond(ctx, response, "Please say 1 to confirm your order or 2 to cancel.", callback_url)

    def _save_order_disk(self, ctx: CallContext, restaurant: Restaurant):
        if not os.path.exists("orders"):
            os.makedirs("orders", exist_ok=True)
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"orders/order_{timestamp}_{ctx.call_sid}.json"
        
        summary, total = self._calc_summary(ctx)
        
        order_data = {
            "order_id": f"ORD-{timestamp}",
            "call_sid": ctx.call_sid,
            "timestamp": datetime.datetime.now().isoformat(),
            "restaurant": restaurant.name,
            "items": [
                {
                    "id": i.item.id,
                    "name": i.item.name,
                    "price": i.item.price,
                    "options": [{"name": o.option_name, "choice": o.choice_name, "extra": o.price_extra} for o in i.selected_options],
                    "total": i.total_price
                }
                for i in ctx.current_order
            ],
            "total_price": total,
            "status": "CONFIRMED"
        }
        
        try:
            with open(filename, "w") as f:
                json.dump(order_data, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save order: {e}")

    def _respond(self, ctx: CallContext, response: VoiceResponse, text: str, callback_url: str) -> str:
        # numDigits=2 for ORDERING_ID to be snappy with keypad
        num_digits = 2 if ctx.stage == CallStage.ORDERING_ID else 1
        
        gather = Gather(
            input='speech dtmf', 
            action=callback_url, 
            numDigits=num_digits, 
            speechTimeout='auto'
        )
        gather.say(text)
        response.append(gather)
        return str(response)

    def _calc_summary(self, ctx: CallContext):
        summary_parts = []
        total = 0.0
        for i in ctx.current_order:
            opts = " with " + ", ".join([o.choice_name for o in i.selected_options]) if i.selected_options else ""
            summary_parts.append(f"{i.item.name}{opts}")
            total += i.total_price
        return ", ".join(summary_parts), total
