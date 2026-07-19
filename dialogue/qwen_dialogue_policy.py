import json
import re
from pathlib import Path
from typing import Any, Dict, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel


class QwenDialoguePolicy:
    def __init__(
        self,
        base_model_name: str = "Qwen/Qwen2.5-3B-Instruct",
        adapter_path: str = "outputs/qwen2.5-3b-dialogue-policy",
        max_new_tokens: int = 96,
    ):
        self.base_model_name = base_model_name
        self.adapter_path = Path(adapter_path)
        self.max_new_tokens = max_new_tokens

        self.system_prompt = (
            "Bạn là Dialogue Policy Model cho hệ thống tư vấn và quản lý cửa hàng hoa. "
            "Nhiệm vụ của bạn là đọc trạng thái hội thoại hiện tại, tin nhắn gần nhất của bot "
            "và tin nhắn mới của khách hàng, sau đó trả về JSON action hợp lệ. "
            "Chỉ trả về JSON, không giải thích."
        )

        self.tokenizer = None
        self.model = None

        self.load_model()

    # =====================================================
    # LOAD MODEL
    # =====================================================

    def load_model(self):
        if not self.adapter_path.exists():
            raise FileNotFoundError(
                f"Không tìm thấy adapter path: {self.adapter_path}"
            )

        if not (self.adapter_path / "adapter_config.json").exists():
            raise FileNotFoundError(
                f"Không tìm thấy adapter_config.json trong: {self.adapter_path}"
            )

        if not (self.adapter_path / "adapter_model.safetensors").exists():
            raise FileNotFoundError(
                f"Không tìm thấy adapter_model.safetensors trong: {self.adapter_path}"
            )

        print("[QwenDialoguePolicy] Loading tokenizer...")

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.base_model_name,
            trust_remote_code=True,
        )

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        print("[QwenDialoguePolicy] Loading base model...")

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            self.base_model_name,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True,
        )

        print("[QwenDialoguePolicy] Loading LoRA adapter...")

        self.model = PeftModel.from_pretrained(
            self.model,
            str(self.adapter_path),
        )

        self.model.eval()

        print("[QwenDialoguePolicy] Model loaded successfully.")

    # =====================================================
    # MAIN PREDICT
    # =====================================================

    def predict(
        self,
        user_message: str,
        state: Optional[Dict[str, Any]] = None,
        last_bot_message: str = "",
    ) -> Dict[str, Any]:
        state = state or {}

        messages = self._build_messages(
            user_message=user_message,
            state=state,
            last_bot_message=last_bot_message,
        )

        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
        ).to(self.model.device)

        with torch.inference_mode():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                num_beams=1,
                use_cache=True,
                eos_token_id=self.tokenizer.eos_token_id,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        generated_tokens = outputs[0][inputs["input_ids"].shape[-1]:]

        generated_text = self.tokenizer.decode(
            generated_tokens,
            skip_special_tokens=True,
        ).strip()

        policy_output = self._parse_json_output(generated_text)

        policy_output = self._normalize_policy_output(
            policy_output=policy_output,
            user_message=user_message,
            state=state,
        )

        return policy_output

    # =====================================================
    # PROMPT
    # =====================================================

    def _build_messages(
        self,
        user_message: str,
        state: Dict[str, Any],
        last_bot_message: str,
    ):
        user_content = (
            f"STATE:\n{json.dumps(state, ensure_ascii=False)}\n\n"
            f"LAST_BOT:\n{last_bot_message}\n\n"
            f"USER:\n{user_message}"
        )

        return [
            {
                "role": "system",
                "content": self.system_prompt,
            },
            {
                "role": "user",
                "content": user_content,
            },
        ]

    # =====================================================
    # JSON PARSE
    # =====================================================

    def _parse_json_output(self, text: str) -> Dict[str, Any]:
        text = text.strip()

        try:
            return json.loads(text)
        except Exception:
            pass

        match = re.search(r"\{.*\}", text, flags=re.DOTALL)

        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass

        return self._fallback_output()

    # =====================================================
    # NORMALIZE / GUARDRAIL
    # =====================================================

    def _normalize_policy_output(
        self,
        policy_output: Dict[str, Any],
        user_message: str,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        user_lower = user_message.lower()

        if not isinstance(policy_output, dict):
            policy_output = self._fallback_output()

        policy_output.setdefault("intent", "unclear")
        policy_output.setdefault("action", "clarify_user_intent")
        policy_output.setdefault("slots", {})
        policy_output.setdefault("should_update_state", False)
        policy_output.setdefault("should_recommend", False)

        slots = policy_output.get("slots")

        if not isinstance(slots, dict):
            slots = {}

        slots = self._ensure_all_slots(slots)

        # =================================================
        # Security guardrail
        # Customer chatbot không được xác nhận thanh toán
        # =================================================

        if policy_output.get("action") == "confirm_payment":
            policy_output["intent"] = "general_question"
            policy_output["action"] = "answer_general"
            policy_output["should_update_state"] = False
            policy_output["should_recommend"] = False

        if any(
            phrase in user_lower
            for phrase in [
                "xác nhận thanh toán",
                "confirm payment",
                "đã thanh toán",
                "duyệt thanh toán",
                "xác nhận đơn đã trả tiền",
            ]
        ):
            policy_output["intent"] = "general_question"
            policy_output["action"] = "answer_general"
            policy_output["should_update_state"] = False
            policy_output["should_recommend"] = False
            policy_output["slots"] = slots
            return policy_output

        # =================================================
        # Confirm order normalization
        # =================================================

        if self._is_confirm_order(user_lower):
            policy_output["intent"] = "confirm_order"
            policy_output["action"] = "collect_customer_info"
            policy_output["should_update_state"] = False
            policy_output["should_recommend"] = False
            policy_output["slots"] = slots
            return policy_output

        # =================================================
        # Customer info normalization
        # =================================================

        customer_info = self._extract_customer_info(user_message)

        if customer_info:
            slots["customer_name"] = customer_info["customer_name"]
            slots["customer_phone"] = customer_info["customer_phone"]
            slots["customer_address"] = customer_info["customer_address"]

            policy_output["intent"] = "provide_customer_info"
            policy_output["action"] = "create_order"
            policy_output["should_update_state"] = True
            policy_output["should_recommend"] = False
            policy_output["slots"] = slots
            return policy_output

        # =================================================
        # Inventory intent normalization
        # =================================================

        slots, policy_output = self._fix_inventory_intent(
            slots=slots,
            policy_output=policy_output,
            user_lower=user_lower,
        )

        if policy_output.get("action") == "check_inventory":
            policy_output["slots"] = slots
            return policy_output

        # =================================================
        # Flower color question normalization
        # "những hoa trên có màu nào khác không?"
        # "cẩm tú cầu có màu gì?"
        # =================================================

        if self._is_ask_flower_colors(user_lower):
            flowers = self._extract_flowers(user_lower)

            if flowers:
                slots["flower_preference"] = flowers

            policy_output["intent"] = "ask_flower_colors"
            policy_output["action"] = "answer_flower_colors"
            policy_output["should_update_state"] = False
            policy_output["should_recommend"] = False
            policy_output["slots"] = slots
            return policy_output

        # =================================================
        # Modify bouquet / flower / color normalization
        # =================================================

        slots, policy_output, handled_modify = self._fix_modify_bouquet_intent(
            slots=slots,
            policy_output=policy_output,
            user_lower=user_lower,
            state=state,
        )

        if handled_modify:
            policy_output["slots"] = slots
            return policy_output

        # =================================================
        # Light slot normalization
        # =================================================

        slots = self._fix_occasion_slots(slots, user_lower, state)
        slots = self._fix_recipient_slots(slots, user_lower, state)
        slots = self._fix_budget_slots(slots, user_lower, state)

        policy_output["slots"] = slots

        if self._has_any_valid_slot(slots):
            policy_output["should_update_state"] = True

        merged_state = self._merge_state_with_slots(state, slots)

        has_occasion = merged_state.get("occasion") is not None
        has_recipient = merged_state.get("recipient") is not None
        has_budget = merged_state.get("budget") is not None

        if has_occasion and has_recipient and has_budget:
            if policy_output.get("action") not in [
                "check_inventory",
                "answer_flower_colors",
                "answer_flower_meaning",
                "answer_flower_pairing",
                "answer_general",
                "collect_customer_info",
                "create_order",
            ]:
                policy_output["intent"] = "new_bouquet_request"
                policy_output["action"] = "recommend_bouquet"
                policy_output["should_update_state"] = True
                policy_output["should_recommend"] = True

        return policy_output

    # =====================================================
    # SLOT HELPERS
    # =====================================================

    def _ensure_all_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        default_slots = {
            "occasion": None,
            "recipient": None,
            "budget": None,
            "budget_min": None,
            "budget_max": None,
            "budget_type": None,
            "flower_preference": [],
            "flower_avoidance": [],
            "color_tone": [],
            "style": [],
            "delivery_time": None,
            "customer_name": None,
            "customer_phone": None,
            "customer_address": None,
            "order_id": None,
        }

        for key, default_value in default_slots.items():
            if key not in slots:
                slots[key] = default_value

        for key in [
            "flower_preference",
            "flower_avoidance",
            "color_tone",
            "style",
        ]:
            if slots.get(key) is None:
                slots[key] = []
            elif not isinstance(slots.get(key), list):
                slots[key] = [slots.get(key)]

        return slots

    def _has_any_valid_slot(self, slots: Dict[str, Any]) -> bool:
        for _, value in slots.items():
            if value is None:
                continue

            if isinstance(value, list) and len(value) == 0:
                continue

            return True

        return False

    # =====================================================
    # SPECIAL INTENT HELPERS
    # =====================================================

    def _is_confirm_order(self, user_lower: str) -> bool:
        confirm_order_phrases = [
            "ok lấy bó này",
            "lấy bó này",
            "chốt bó này",
            "chốt đơn",
            "tôi lấy bó này",
            "tôi sẽ lấy bó này",
            "mình lấy bó này",
            "em lấy bó này",
            "đặt bó này",
            "cho tôi bó này",
            "cho anh bó này",
            "lấy mẫu này",
            "okela",
            "oke lấy",
            "ok lấy",
            "được đấy",
            "được đó",
            "ưng bó này",
        ]

        return any(phrase in user_lower for phrase in confirm_order_phrases)

    def _is_ask_flower_colors(self, user_lower: str) -> bool:
        color_question_phrases = [
            "có màu nào",
            "màu nào",
            "màu gì",
            "màu nào khác",
            "có màu nào khác",
            "những hoa trên có màu",
            "hoa trên có màu",
            "các hoa trên có màu",
            "có tone nào",
            "tone nào",
            "tone màu nào",
        ]

        return any(phrase in user_lower for phrase in color_question_phrases)

    def _extract_customer_info(self, user_message: str):
        parts = [part.strip() for part in user_message.split("-")]

        if len(parts) >= 3:
            phone_match = re.search(r"(0|\+84)\d{8,10}", user_message)

            if phone_match:
                customer_name = parts[0].strip()
                customer_phone = phone_match.group(0).strip()

                phone_part_index = None
                for idx, part in enumerate(parts):
                    if customer_phone in part:
                        phone_part_index = idx
                        break

                if phone_part_index is not None:
                    address_parts = parts[phone_part_index + 1:]
                    customer_address = " - ".join(address_parts).strip()
                else:
                    customer_address = parts[-1].strip()

                if customer_name and customer_phone and customer_address:
                    return {
                        "customer_name": customer_name,
                        "customer_phone": customer_phone,
                        "customer_address": customer_address,
                    }

        return None

    def _fix_inventory_intent(
        self,
        slots: Dict[str, Any],
        policy_output: Dict[str, Any],
        user_lower: str,
    ):
        inventory_keywords = [
            "còn",
            "còn không",
            "còn hàng",
            "hết hàng",
            "bao nhiêu cành",
            "bao nhiêu bông",
            "tồn kho",
            "shop còn",
            "có sẵn",
        ]

        matched_flowers = self._extract_flowers(user_lower)

        is_inventory_question = any(
            keyword in user_lower for keyword in inventory_keywords
        )

        if is_inventory_question and matched_flowers:
            policy_output["intent"] = "ask_inventory"
            policy_output["action"] = "check_inventory"
            policy_output["should_update_state"] = True
            policy_output["should_recommend"] = False
            slots["flower_preference"] = matched_flowers

        return slots, policy_output

    def _fix_modify_bouquet_intent(
        self,
        slots: Dict[str, Any],
        policy_output: Dict[str, Any],
        user_lower: str,
        state: Dict[str, Any],
    ):
        flowers = self._extract_flowers(user_lower)
        colors = self._extract_colors(user_lower)
        styles = self._extract_styles(user_lower)

        modify_keywords = [
            "đổi",
            "thay",
            "thêm",
            "bớt",
            "làm chủ đạo",
            "chủ đạo",
            "ưu tiên",
            "muốn",
            "cho thêm",
            "phối",
            "lấy màu",
            "màu",
        ]

        has_modify_keyword = any(keyword in user_lower for keyword in modify_keywords)
        has_flower_or_color = bool(flowers or colors or styles)

        has_existing_recommendation_context = (
            state.get("occasion") is not None
            and state.get("recipient") is not None
            and state.get("budget") is not None
        )

        if has_existing_recommendation_context and has_modify_keyword and has_flower_or_color:
            if flowers:
                slots["flower_preference"] = flowers

            if colors:
                slots["color_tone"] = colors

            if styles:
                slots["style"] = styles

            policy_output["intent"] = "modify_flower"
            policy_output["action"] = "recommend_bouquet"
            policy_output["should_update_state"] = True
            policy_output["should_recommend"] = True

            return slots, policy_output, True

        return slots, policy_output, False

    # =====================================================
    # DOMAIN EXTRACTORS
    # =====================================================

    def _extract_flowers(self, user_lower: str):
        flower_patterns = [
            "cẩm tú cầu",
            "hoa hồng kem",
            "hồng kem",
            "hoa hồng",
            "baby trắng",
            "baby",
            "cát tường",
            "tulip",
            "hướng dương",
            "lá bạc",
        ]

        flowers = []

        for flower in flower_patterns:
            if flower in user_lower:
                normalized = flower

                if normalized == "hồng kem":
                    normalized = "hoa hồng kem"

                if normalized not in flowers:
                    flowers.append(normalized)

        return flowers

    def _extract_colors(self, user_lower: str):
        color_patterns = [
            (["xanh dương", "màu xanh dương"], "xanh dương"),
            (["xanh lá", "màu xanh lá"], "xanh lá"),
            (["xanh", "màu xanh"], "xanh"),
            (["hồng", "màu hồng"], "hồng"),
            (["đỏ", "màu đỏ"], "đỏ"),
            (["trắng", "màu trắng"], "trắng"),
            (["vàng", "màu vàng"], "vàng"),
            (["tím", "màu tím"], "tím"),
            (["cam", "màu cam"], "cam"),
            (["kem", "màu kem"], "kem"),
            (["pastel"], "pastel"),
        ]

        colors = []

        for keywords, value in color_patterns:
            if any(keyword in user_lower for keyword in keywords):
                if value not in colors:
                    colors.append(value)

        return colors

    def _extract_styles(self, user_lower: str):
        style_patterns = [
            (["nhẹ nhàng", "dịu dàng"], "nhẹ nhàng"),
            (["sang", "sang trọng", "cao cấp"], "sang trọng"),
            (["lãng mạn", "romantic"], "lãng mạn"),
            (["tối giản", "đơn giản"], "tối giản"),
            (["nổi bật", "rực rỡ"], "nổi bật"),
            (["trẻ trung"], "trẻ trung"),
        ]

        styles = []

        for keywords, value in style_patterns:
            if any(keyword in user_lower for keyword in keywords):
                if value not in styles:
                    styles.append(value)

        return styles

    # =====================================================
    # BASIC SLOT NORMALIZATION
    # =====================================================

    def _fix_occasion_slots(
        self,
        slots: Dict[str, Any],
        user_lower: str,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        if slots.get("occasion") or state.get("occasion"):
            return slots

        occasion_patterns = [
            (["valentine", "lễ tình nhân", "ngày tình nhân", "14/2", "14-2"], "Valentine"),
            (["8/3", "8-3", "quốc tế phụ nữ", "ngày quốc tế phụ nữ"], "8/3"),
            (["20/10", "20-10", "phụ nữ việt nam", "ngày phụ nữ việt nam"], "20/10"),
            (["20/11", "20-11", "nhà giáo", "ngày nhà giáo"], "20/11"),
            (["sinh nhật", "birthday"], "sinh nhật"),
            (["kỷ niệm", "anniversary"], "kỷ niệm"),
            (["tốt nghiệp", "graduation"], "tốt nghiệp"),
            (["khai trương"], "khai trương"),
            (["cầu hôn"], "cầu hôn"),
            (["tỏ tình"], "tỏ tình"),
            (["xin lỗi"], "xin lỗi"),
            (["cảm ơn"], "cảm ơn"),
            (["chia buồn", "viếng", "đám tang"], "chia buồn"),
            (["thăm bệnh"], "thăm bệnh"),
            (["giáng sinh", "noel", "christmas"], "Giáng sinh"),
            (["tết"], "Tết"),
            (["ngày của mẹ"], "Ngày của mẹ"),
        ]

        for keywords, value in occasion_patterns:
            if any(keyword in user_lower for keyword in keywords):
                slots["occasion"] = value
                break

        return slots

    def _fix_recipient_slots(
        self,
        slots: Dict[str, Any],
        user_lower: str,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        if slots.get("recipient") or state.get("recipient"):
            return slots

        recipient_patterns = [
            (["người yêu", "bạn gái", "bạn trai", "crush", "vợ", "chồng"], "người yêu"),
            (["mẹ", "má", "mama"], "mẹ"),
            (["thầy", "cô giáo", "giáo viên", "thầy cô"], "thầy cô"),
            (["bạn bè"], "bạn bè"),
            (["đồng nghiệp"], "đồng nghiệp"),
            (["khách hàng"], "khách hàng"),
            (["sếp"], "sếp"),
        ]

        for keywords, value in recipient_patterns:
            if any(keyword in user_lower for keyword in keywords):
                slots["recipient"] = value
                break

        return slots

    def _fix_budget_slots(
        self,
        slots: Dict[str, Any],
        user_lower: str,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        if slots.get("budget") is None and state.get("budget") is not None:
            return slots

        extracted_budget = self._extract_budget(user_lower)

        if slots.get("budget") is None and extracted_budget is not None:
            slots["budget"] = extracted_budget

        if slots.get("budget") is not None:
            if any(x in user_lower for x in ["dưới", "tối đa", "không quá", "đổ lại"]):
                slots["budget_type"] = "maximum"
                slots["budget_max"] = slots.get("budget")
                slots["budget_min"] = None

            elif any(x in user_lower for x in ["trên", "từ", "ít nhất"]):
                slots["budget_type"] = "minimum"
                slots["budget_min"] = slots.get("budget")
                slots["budget_max"] = None

            elif any(x in user_lower for x in ["khoảng", "tầm", "cỡ"]):
                slots["budget_type"] = "approx"

            elif slots.get("budget_type") is None:
                slots["budget_type"] = "approx"

        return slots

    def _extract_budget(self, user_lower: str) -> Optional[int]:
        text = user_lower.replace(".", "").replace(",", "")

        patterns_million = [
            r"(\d+)\s*tr(?:iệu)?",
            r"(\d+)\s*trieu",
        ]

        for pattern in patterns_million:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1)) * 1_000_000

        patterns_thousand = [
            r"(\d+)\s*k",
            r"(\d+)\s*nghìn",
            r"(\d+)\s*ngàn",
        ]

        for pattern in patterns_thousand:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1)) * 1_000

        pattern_vnd = r"(\d{5,})"
        match = re.search(pattern_vnd, text)
        if match:
            return int(match.group(1))

        return None

    def _merge_state_with_slots(
        self,
        state: Dict[str, Any],
        slots: Dict[str, Any],
    ) -> Dict[str, Any]:
        merged_state = state.copy()

        for key, value in slots.items():
            if value is None:
                continue

            if isinstance(value, list) and len(value) == 0:
                continue

            merged_state[key] = value

        return merged_state

    # =====================================================
    # FALLBACK
    # =====================================================

    def _fallback_output(self) -> Dict[str, Any]:
        return {
            "intent": "unclear",
            "action": "clarify_user_intent",
            "slots": {
                "occasion": None,
                "recipient": None,
                "budget": None,
                "budget_min": None,
                "budget_max": None,
                "budget_type": None,
                "flower_preference": [],
                "flower_avoidance": [],
                "color_tone": [],
                "style": [],
                "delivery_time": None,
                "customer_name": None,
                "customer_phone": None,
                "customer_address": None,
                "order_id": None,
            },
            "should_update_state": False,
            "should_recommend": False,
        }