class ConversationState:
    def __init__(self):
        self.state = self._get_initial_state()

    def _get_initial_state(self):
        return {
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

            # Customer info
            "customer_name": None,
            "customer_phone": None,
            "customer_address": None,
        }

    def update(self, new_info: dict):
        if not new_info:
            return

        for key, value in new_info.items():
            if key not in self.state:
                continue

            if value is None:
                continue

            if isinstance(value, list):
                for item in value:
                    if item not in self.state[key]:
                        self.state[key].append(item)
            else:
                self.state[key] = value

    def get_state(self):
        return self.state.copy()

    def reset(self):
        self.state = self._get_initial_state()