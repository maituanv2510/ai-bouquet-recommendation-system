REQUIRED_FIELDS = ["occasion", "recipient", "budget"]

class DialogManager:
    def __init__(self):
        pass

    def get_missing_fields(self, state: dict):
        missing = []

        for field in REQUIRED_FIELDS:
            value = state.get(field)

            if value is None:
                missing.append(field)

            if isinstance(value, list) and len(value) == 0:
                missing.append(field)

        return missing

    def should_recommend(self, state: dict):
        missing = self.get_missing_fields(state)
        return len(missing) == 0

    def ask_next_question(self, state: dict):
        missing = self.get_missing_fields(state)

        if not missing:
            return None

        next_field = missing[0]

        questions = {
            "occasion": "Dạ anh/chị muốn tặng bó hoa này vào dịp gì ạ? Ví dụ sinh nhật, kỷ niệm, tốt nghiệp hoặc chúc mừng.",
            "recipient": "Dạ bó hoa này mình muốn tặng cho ai ạ? Ví dụ bạn nữ, mẹ, người yêu, đồng nghiệp hoặc thầy cô.",
            "budget": "Dạ anh/chị muốn bó hoa trong khoảng ngân sách bao nhiêu ạ?"
        }

        return questions.get(next_field)