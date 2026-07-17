"""
Sinh bộ dữ liệu đánh giá (evaluation set) cho hệ thống retrieval hoa:
với mỗi câu query bằng tiếng Việt, gán nhãn danh sách hoa được kỳ vọng
(expected_flowers) là phù hợp/liên quan nhất.

Output:
    data/processed/retrieval_eval.jsonl

Số lượng: 80 queries.

Format mỗi dòng:
{
  "query": "...",
  "expected_flowers": ["...", "..."]
}

Query xoay quanh 11 chủ đề (nhóm ý nghĩa + tone):
    1. tặng mẹ và biết ơn
    2. tặng bạn và chân thành
    3. tặng người yêu và lãng mạn
    4. khai trương và may mắn
    5. tốt nghiệp và hy vọng
    6. xin lỗi và chân thành
    7. cảm ơn và trân trọng
    8. thăm bệnh và động viên
    9. tone nhẹ nhàng
    10. tone rực rỡ
    11. tone sang trọng

expected_flowers luôn được lấy từ danh sách 12 loài hoa cố định:
    Cẩm tú cầu, Hoa hồng, Baby's breath, Cát tường, Hướng dương,
    Cẩm chướng, Tulip, Đồng tiền, Lan hồ điệp, Hoa ly, Lavender, Cúc tana

Mỗi chủ đề được gán trước một tập hoa liên quan về mặt ý nghĩa/tone
(ví dụ: "tặng mẹ và biết ơn" -> Cẩm chướng, Hoa hồng, Lan hồ điệp, Cát tường).
Với mỗi query, chọn ngẫu nhiên 2-3 hoa trong tập liên quan của chủ đề đó
làm expected_flowers.
random seed = 42 để đảm bảo tái lập được kết quả.

"""

import os
import json
import random

RANDOM_SEED = 42

OUTPUT_PATH = os.path.join("data", "processed", "retrieval_eval.jsonl")


# Danh sách 12 loài hoa cố định dùng làm expected_flowers
ALL_FLOWERS = [
    "Cẩm tú cầu", "Hoa hồng", "Baby's breath", "Cát tường", "Hướng dương",
    "Cẩm chướng", "Tulip", "Đồng tiền", "Lan hồ điệp", "Hoa ly",
    "Lavender", "Cúc tana",
]
# Định nghĩa 11 chủ đề: tên chủ đề, tập hoa liên quan, và các mẫu câu query
TOPICS = [
    {
        "name": "tặng mẹ và biết ơn",
        "flowers": ["Cẩm chướng", "Hoa hồng", "Lan hồ điệp", "Cát tường"],
        "templates": [
            "Mình muốn tìm hoa tặng mẹ để bày tỏ lòng biết ơn",
            "Gợi ý giúp mình bó hoa tặng mẹ nhân ngày của Mẹ, thể hiện sự biết ơn",
            "Có hoa nào phù hợp để tặng mẹ, mang ý nghĩa biết ơn công lao sinh thành không?",
            "Tìm hoa tặng mẹ, muốn nói lời cảm ơn vì mẹ đã vất vả nuôi con",
            "Mình cần bó hoa tặng mẹ dịp sinh nhật, thể hiện lòng biết ơn sâu sắc",
            "Hoa nào thể hiện được sự biết ơn khi tặng mẹ nhân dịp 20/10?",
            "Cho mình xin gợi ý hoa tặng mẹ, ý nghĩa biết ơn và trân trọng",
            "Tìm bó hoa tặng mẹ mang thông điệp biết ơn chân thành nhất",
        ],
        "count": 8,
    },
    {
        "name": "tặng bạn và chân thành",
        "flowers": ["Hướng dương", "Đồng tiền", "Cúc tana", "Cẩm chướng"],
        "templates": [
            "Mình muốn tặng hoa cho bạn thân, thể hiện tình cảm chân thành",
            "Gợi ý hoa tặng bạn nhân dịp sinh nhật, mang ý nghĩa chân thành",
            "Có hoa nào phù hợp để tặng bạn bè, thể hiện sự chân thành không?",
            "Tìm bó hoa tặng bạn, muốn gửi gắm tình bạn chân thành bền lâu",
            "Cho mình xin gợi ý hoa tặng bạn, mang thông điệp chân thành và vui vẻ",
            "Hoa nào hợp để tặng bạn nữ, thể hiện tình bạn chân thành?",
            "Mình cần hoa tặng bạn để chúc mừng, nhưng muốn giữ sự chân thành giản dị",
            "Tìm hoa tặng bạn bè lâu năm, thể hiện tấm lòng chân thành",
        ],
        "count": 8,
    },
    {
        "name": "tặng người yêu và lãng mạn",
        "flowers": ["Hoa hồng", "Tulip", "Baby's breath", "Hoa ly"],
        "templates": [
            "Mình muốn tặng hoa cho người yêu, thể hiện sự lãng mạn",
            "Gợi ý hoa tặng người yêu nhân dịp Valentine, mang phong cách lãng mạn",
            "Có hoa nào phù hợp để tỏ tình, mang ý nghĩa lãng mạn không?",
            "Tìm bó hoa tặng người yêu, muốn thể hiện tình yêu lãng mạn sâu đậm",
            "Cho mình xin gợi ý hoa tặng bạn gái, mang cảm giác ngọt ngào lãng mạn",
            "Hoa nào hợp để tặng người yêu nhân kỷ niệm ngày quen nhau, thật lãng mạn?",
            "Mình cần hoa tặng người yêu để cầu hôn, mang không khí lãng mạn",
            "Tìm hoa tặng bạn trai/bạn gái, thể hiện sự lãng mạn tinh tế",
        ],
        "count": 7,
    },
    {
        "name": "khai trương và may mắn",
        "flowers": ["Lan hồ điệp", "Hướng dương", "Đồng tiền", "Hoa ly"],
        "templates": [
            "Mình cần lẵng hoa khai trương, mang ý nghĩa may mắn",
            "Gợi ý hoa chúc mừng khai trương cửa hàng, thể hiện tài lộc may mắn",
            "Có hoa nào phù hợp để tặng khai trương công ty, mang lại may mắn không?",
            "Tìm hoa chúc mừng khai trương, muốn gửi gắm lời chúc phát tài may mắn",
            "Cho mình xin gợi ý lẵng hoa khai trương quán, thể hiện sự may mắn thịnh vượng",
            "Hoa nào hợp để tặng khai trương chi nhánh mới, mang ý nghĩa may mắn?",
            "Mình cần hoa tặng đối tác nhân dịp khai trương, biểu tượng cho may mắn",
        ],
        "count": 7,
    },
    {
        "name": "tốt nghiệp và hy vọng",
        "flowers": ["Hướng dương", "Tulip", "Cát tường", "Đồng tiền"],
        "templates": [
            "Mình muốn tặng hoa mừng tốt nghiệp, thể hiện niềm hy vọng vào tương lai",
            "Gợi ý hoa chúc mừng tốt nghiệp, mang ý nghĩa hy vọng và khởi đầu mới",
            "Có hoa nào phù hợp để tặng bạn tốt nghiệp đại học, mang niềm hy vọng không?",
            "Tìm bó hoa tặng lễ tốt nghiệp, muốn gửi lời chúc tràn đầy hy vọng",
            "Cho mình xin gợi ý hoa tặng cô giáo dịp tốt nghiệp, mang ý nghĩa hy vọng",
            "Hoa nào hợp để tặng em gái vừa tốt nghiệp, thể hiện niềm tin và hy vọng?",
            "Mình cần hoa chúc mừng tốt nghiệp, biểu tượng cho hy vọng vào con đường mới",
        ],
        "count": 7,
    },
    {
        "name": "xin lỗi và chân thành",
        "flowers": ["Cẩm chướng", "Baby's breath", "Cát tường", "Hoa hồng"],
        "templates": [
            "Mình muốn tặng hoa xin lỗi người yêu, thể hiện sự chân thành",
            "Gợi ý hoa xin lỗi bạn thân, mang thông điệp chân thành và hối lỗi",
            "Có hoa nào phù hợp để xin lỗi, thể hiện tấm lòng chân thành không?",
            "Tìm hoa tặng để làm hòa, muốn gửi lời xin lỗi thật chân thành",
            "Cho mình xin gợi ý hoa xin lỗi vợ/chồng, mang ý nghĩa chân thành sâu sắc",
            "Hoa nào hợp để tặng khi xin lỗi đồng nghiệp, thể hiện sự chân thành?",
            "Mình cần hoa xin lỗi mẹ vì đã cãi lời, mang thông điệp chân thành",
        ],
        "count": 7,
    },
    {
        "name": "cảm ơn và trân trọng",
        "flowers": ["Cẩm chướng", "Hoa ly", "Lan hồ điệp", "Cát tường"],
        "templates": [
            "Mình muốn tặng hoa cảm ơn cô giáo, thể hiện sự trân trọng",
            "Gợi ý hoa cảm ơn đồng nghiệp, mang ý nghĩa trân trọng chân thành",
            "Có hoa nào phù hợp để cảm ơn khách hàng, thể hiện sự trân trọng không?",
            "Tìm hoa tặng để nói lời cảm ơn, muốn gửi gắm sự trân trọng sâu sắc",
            "Cho mình xin gợi ý hoa cảm ơn sếp, mang thông điệp trân trọng và biết ơn",
            "Hoa nào hợp để tặng cảm ơn người đã giúp đỡ mình, thể hiện sự trân trọng?",
            "Mình cần hoa cảm ơn bác sĩ đã chữa bệnh, mang ý nghĩa trân trọng",
        ],
        "count": 7,
    },
    {
        "name": "thăm bệnh và động viên",
        "flowers": ["Hướng dương", "Cúc tana", "Đồng tiền", "Cẩm chướng"],
        "templates": [
            "Mình muốn mua hoa thăm bệnh, mang ý nghĩa động viên tinh thần",
            "Gợi ý hoa thăm người ốm, thể hiện sự động viên và chúc mau khỏe",
            "Có hoa nào phù hợp để thăm bệnh viện, mang lại sự động viên không?",
            "Tìm hoa tặng người thân đang nằm viện, muốn động viên tinh thần họ",
            "Cho mình xin gợi ý hoa thăm bệnh đồng nghiệp, mang thông điệp động viên",
            "Hoa nào hợp để tặng khi thăm bệnh bạn bè, thể hiện sự động viên lạc quan?",
            "Mình cần hoa thăm ông bà đang dưỡng bệnh, mang ý nghĩa động viên sức khỏe",
        ],
        "count": 7,
    },
    {
        "name": "tone nhẹ nhàng",
        "flowers": ["Baby's breath", "Lavender", "Cát tường", "Cẩm chướng"],
        "templates": [
            "Mình muốn tìm bó hoa mang tone nhẹ nhàng, dịu dàng",
            "Gợi ý hoa phong cách nhẹ nhàng, tinh tế cho buổi hẹn hò",
            "Có bó hoa nào mang cảm giác nhẹ nhàng, thanh thoát không?",
            "Tìm hoa trang trí bàn làm việc theo tone nhẹ nhàng, dịu mắt",
            "Cho mình xin gợi ý hoa cưới phong cách nhẹ nhàng, mộc mạc",
            "Hoa nào hợp để cắm bình theo tone nhẹ nhàng, pastel dịu dàng?",
            "Mình cần bó hoa quà tặng mang phong cách nhẹ nhàng, tối giản",
            "Tìm hoa trang trí tiệc trà theo tone nhẹ nhàng, thanh lịch",
        ],
        "count": 8,
    },
    {
        "name": "tone rực rỡ",
        "flowers": ["Hướng dương", "Đồng tiền", "Tulip", "Cẩm tú cầu"],
        "templates": [
            "Mình muốn tìm bó hoa mang tone rực rỡ, tươi sáng",
            "Gợi ý hoa phong cách rực rỡ, nổi bật cho tiệc sinh nhật",
            "Có bó hoa nào mang cảm giác rực rỡ, tràn đầy năng lượng không?",
            "Tìm hoa trang trí sự kiện theo tone rực rỡ, bắt mắt",
            "Cho mình xin gợi ý hoa mừng lễ hội phong cách rực rỡ, sặc sỡ",
            "Hoa nào hợp để cắm bình theo tone rực rỡ, nhiều màu sắc?",
            "Mình cần bó hoa quà tặng mang phong cách rực rỡ, vui tươi",
        ],
        "count": 7,
    },
    {
        "name": "tone sang trọng",
        "flowers": ["Lan hồ điệp", "Hoa ly", "Hoa hồng", "Tulip"],
        "templates": [
            "Mình muốn tìm bó hoa mang tone sang trọng, quý phái",
            "Gợi ý hoa phong cách sang trọng cho sự kiện công ty",
            "Có bó hoa nào mang cảm giác sang trọng, đẳng cấp không?",
            "Tìm hoa trang trí tiệc cưới theo tone sang trọng, lộng lẫy",
            "Cho mình xin gợi ý hoa tặng đối tác phong cách sang trọng, tinh tế",
            "Hoa nào hợp để cắm bình theo tone sang trọng, quý phái?",
            "Mình cần bó hoa quà tặng mang phong cách sang trọng, cao cấp",
        ],
        "count": 7,
    },
]


def build_queries(rng: random.Random) -> list:
    samples = []
    for topic in TOPICS:
        templates = topic["templates"]
        count = topic["count"]
        flower_pool = topic["flowers"]

        # Đảm bảo dùng hết các mẫu câu có sẵn trước, nếu count > số mẫu thì lặp lại có xáo trộn
        template_cycle = templates[:]
        rng.shuffle(template_cycle)
        chosen_templates = []
        while len(chosen_templates) < count:
            if not template_cycle:
                template_cycle = templates[:]
                rng.shuffle(template_cycle)
            chosen_templates.append(template_cycle.pop())

        for query_text in chosen_templates:
            num_flowers = rng.randint(2, min(3, len(flower_pool)))
            expected = rng.sample(flower_pool, num_flowers)
            samples.append({
                "query": query_text,
                "expected_flowers": expected,
            })

    return samples


def main():
    output_dir = os.path.dirname(OUTPUT_PATH)
    os.makedirs(output_dir, exist_ok=True)

    rng = random.Random(RANDOM_SEED)
    samples = build_queries(rng)

    total_target = sum(topic["count"] for topic in TOPICS)
    assert len(samples) == total_target, (
        f"Số lượng query sinh ra ({len(samples)}) không khớp tổng cấu hình ({total_target})"
    )

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for record in samples:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Đã sinh {len(samples)} queries.")
    print(f"File được lưu tại: {OUTPUT_PATH}")

    # Thống kê nhanh: tần suất xuất hiện của từng hoa trong expected_flowers
    flower_freq = {}
    for s in samples:
        for f in s["expected_flowers"]:
            flower_freq[f] = flower_freq.get(f, 0) + 1
    print("\nTần suất xuất hiện trong expected_flowers:")
    for flower in ALL_FLOWERS:
        print(f"  {flower}: {flower_freq.get(flower, 0)}")


if __name__ == "__main__":
    main()