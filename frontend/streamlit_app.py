import os
import sys
import streamlit as st

# ============================================================
# Add project root to Python path
# ============================================================

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
sys.path.append(PROJECT_ROOT)

from rag.hybrid_retriever import HybridRetriever
from recommendation.inventory_filter import InventoryFilter
from recommendation.scoring import RecommendationScorer


# ============================================================
# Streamlit page config
# ============================================================

st.set_page_config(
    page_title="AI Bouquet Recommendation Demo",
    page_icon="🌸",
    layout="wide"
)


# ============================================================
# Mock Extractor
# ============================================================

def mock_extract_requirements(customer_message: str):
    """
    Mock output của Fine-tuned LLM Extractor.

    Trong bản demo local, hàm này mô phỏng output JSON của model.
    Khi có GPU hoặc đã nối model thật, có thể thay hàm này bằng:
    extract_requirements(customer_message)
    """

    msg = customer_message.lower()

    requirements = {
        "product_type": "bouquet",
        "occasion": None,
        "recipient": None,
        "budget": None,
        "budget_type": None,
        "color_tone": [],
        "style": [],
        "meaning_intent": [],
        "flower_preference": [],
        "flower_avoidance": [],
        "delivery_time": None,
        "missing_fields": []
    }

    # Occasion / recipient
    if "tặng bạn" in msg or "người bạn" in msg or "bạn" in msg:
        requirements["occasion"] = "tặng bạn"
        requirements["recipient"] = "người bạn"
        requirements["meaning_intent"] = ["tình bạn", "chân thành", "quan tâm"]

    elif "tặng mẹ" in msg or "mẹ" in msg:
        requirements["occasion"] = "tặng mẹ"
        requirements["recipient"] = "mẹ"
        requirements["meaning_intent"] = ["biết ơn", "yêu thương"]

    elif "người yêu" in msg or "tặng người yêu" in msg:
        requirements["occasion"] = "tặng người yêu"
        requirements["recipient"] = "người yêu"
        requirements["meaning_intent"] = ["tình yêu", "lãng mạn"]

    elif "khai trương" in msg:
        requirements["occasion"] = "khai trương"
        requirements["recipient"] = "đối tác"
        requirements["meaning_intent"] = ["may mắn", "thành công", "phát triển"]

    elif "tốt nghiệp" in msg:
        requirements["occasion"] = "tốt nghiệp"
        requirements["recipient"] = None
        requirements["meaning_intent"] = ["hy vọng", "chúc mừng", "thành công"]

    elif "cảm ơn" in msg:
        requirements["occasion"] = "cảm ơn"
        requirements["recipient"] = None
        requirements["meaning_intent"] = ["biết ơn", "trân trọng"]

    elif "xin lỗi" in msg:
        requirements["occasion"] = "xin lỗi"
        requirements["recipient"] = None
        requirements["meaning_intent"] = ["chân thành", "hối lỗi"]

    # Budget
    if "300k" in msg or "300 k" in msg:
        requirements["budget"] = 300000
    elif "400k" in msg or "400 k" in msg:
        requirements["budget"] = 400000
    elif "500k" in msg or "500 k" in msg:
        requirements["budget"] = 500000
    elif "600k" in msg or "600 k" in msg:
        requirements["budget"] = 600000
    elif "800k" in msg or "800 k" in msg:
        requirements["budget"] = 800000
    elif "1 triệu" in msg or "1tr" in msg or "1000000" in msg:
        requirements["budget"] = 1000000

    if requirements["budget"] is not None:
        if "dưới" in msg or "đổ lại" in msg or "không quá" in msg:
            requirements["budget_type"] = "maximum"
        elif "tầm" in msg or "khoảng" in msg:
            requirements["budget_type"] = "around"
        else:
            requirements["budget_type"] = "around"

    # Flower preference
    flower_keywords = {
        "cẩm tú cầu": "cẩm tú cầu",
        "hoa hồng": "hoa hồng",
        "hồng đỏ": "hoa hồng đỏ",
        "baby": "Baby's breath",
        "baby's breath": "Baby's breath",
        "cát tường": "cát tường",
        "hướng dương": "hướng dương",
        "tulip": "tulip",
        "cẩm chướng": "cẩm chướng",
        "đồng tiền": "đồng tiền",
        "lan hồ điệp": "lan hồ điệp",
    }

    for keyword, flower_name in flower_keywords.items():
        if keyword in msg:
            if flower_name not in requirements["flower_preference"]:
                requirements["flower_preference"].append(flower_name)

    # Flower avoidance
    if "không dùng hoa hồng đỏ" in msg or "đừng dùng hoa hồng đỏ" in msg:
        requirements["flower_avoidance"].append("hoa hồng đỏ")

    if "không dùng hoa hồng" in msg or "đừng dùng hoa hồng" in msg:
        requirements["flower_avoidance"].append("hoa hồng")

    # Nếu hoa nằm trong avoidance thì xóa khỏi preference
    requirements["flower_preference"] = [
        flower for flower in requirements["flower_preference"]
        if flower not in requirements["flower_avoidance"]
    ]

    # Colors
    colors = ["hồng", "trắng", "xanh", "đỏ", "vàng", "tím", "cam"]
    for color in colors:
        if color in msg:
            if color not in requirements["color_tone"]:
                requirements["color_tone"].append(color)

    # Style
    styles = ["nhẹ nhàng", "sang trọng", "tối giản", "rực rỡ", "lãng mạn", "thanh lịch"]
    for style in styles:
        if style in msg:
            if style not in requirements["style"]:
                requirements["style"].append(style)

    # Delivery time
    if "chiều mai" in msg:
        requirements["delivery_time"] = "chiều mai"
    elif "sáng mai" in msg:
        requirements["delivery_time"] = "sáng mai"
    elif "tối nay" in msg:
        requirements["delivery_time"] = "tối nay"
    elif "hôm nay" in msg:
        requirements["delivery_time"] = "hôm nay"

    # Missing fields
    important_fields = ["occasion", "recipient", "budget", "color_tone", "style"]

    for field in important_fields:
        value = requirements[field]
        if value is None or value == []:
            requirements["missing_fields"].append(field)

    return requirements


# ============================================================
# Simple bouquet builder for UI demo
# ============================================================

def build_simple_bouquet(scored_candidates, requirements):
    """
    Bản bouquet builder đơn giản cho demo UI.

    Input:
        scored_candidates: candidates đã qua inventory filter + scoring
        requirements: extracted JSON

    Output:
        recommended bouquet JSON
    """

    if not scored_candidates:
        return None

    budget = requirements.get("budget") or 500000
    wrapping_fee = 40000

    selected_items = []
    total = wrapping_fee

    for idx, item in enumerate(scored_candidates[:6]):
        price = int(item["selling_price"])

        if idx == 0:
            role = "main"
            quantity = 3
        elif idx <= 2:
            role = "secondary"
            quantity = 5
        else:
            role = "filler"
            quantity = 1

        subtotal = price * quantity

        if total + subtotal <= budget:
            selected_items.append({
                "flower_name": item["variant_name"],
                "base_flower_name": item["base_flower_name"],
                "role": role,
                "quantity": quantity,
                "unit_price": price,
                "subtotal": subtotal,
                "score": item["final_score"]
            })
            total += subtotal

    bouquet = {
        "bouquet_name": "Bó hoa gợi ý cá nhân hóa",
        "items": selected_items,
        "wrapping_fee": wrapping_fee,
        "estimated_price": total,
        "budget": budget,
        "is_within_budget": total <= budget
    }

    return bouquet


# ============================================================
# Response generator
# ============================================================

def generate_customer_response(requirements, bouquet):
    if bouquet is None or not bouquet.get("items"):
        return (
            "Hiện hệ thống chưa tìm được bó hoa phù hợp với yêu cầu này. "
            "Anh/chị có thể tăng ngân sách hoặc chọn loại hoa khác để shop tư vấn thêm."
        )

    flower_names = [item["flower_name"] for item in bouquet["items"]]
    flower_text = ", ".join(flower_names)

    occasion = requirements.get("occasion") or "yêu cầu của anh/chị"
    budget = requirements.get("budget")

    if budget:
        budget_text = f" trong ngân sách khoảng {budget:,}đ".replace(",", ".")
    else:
        budget_text = ""

    price_text = f"{bouquet['estimated_price']:,}đ".replace(",", ".")

    response = (
        f"Dạ với {occasion}{budget_text}, shop gợi ý "
        f"'{bouquet['bouquet_name']}' gồm: {flower_text}. "
        f"Giá dự kiến khoảng {price_text}. "
        f"Bó hoa này được chọn dựa trên ý nghĩa hoa, tồn kho hiện tại, "
        f"độ phù hợp với yêu cầu và ràng buộc ngân sách."
    )

    if requirements.get("missing_fields"):
        missing = ", ".join(requirements["missing_fields"])
        response += (
            f"\n\nMột số thông tin anh/chị chưa cung cấp gồm: {missing}. "
            f"Nếu bổ sung thêm, hệ thống có thể cá nhân hóa bó hoa tốt hơn."
        )

    return response


# ============================================================
# UI
# ============================================================

st.title("🌸 AI Bouquet Recommendation System")
st.caption("Fine-tuned LLM Extractor + Hybrid RAG + Inventory-aware Recommendation")

with st.sidebar:
    st.header("Demo Mode")

    demo_mode = st.radio(
        "Chọn chế độ:",
        ["Mock Extractor Local", "Full Extractor Later"],
        index=0
    )

    st.info(
        "Mock Extractor Local dùng JSON giả lập để demo pipeline local. "
        "Phần RAG, inventory filter và scoring vẫn chạy thật."
    )

    st.header("Pipeline")
    st.write("1. Customer request")
    st.write("2. Extracted Requirement JSON")
    st.write("3. Hybrid RAG Retrieval")
    st.write("4. Inventory Filter")
    st.write("5. Recommendation Scoring")
    st.write("6. Bouquet Recommendation")


sample_requests = [
    "Cho anh một bó hoa tầm 500k có cẩm tú cầu",
    "Tôi cần một bó hoa có kèm cẩm tú cầu để tặng người bạn trong mức giá 500k đổ lại.",
    "Mình muốn bó hoa tặng mẹ, tone hồng trắng, khoảng 600k.",
    "Tôi muốn bó hoa khai trương, màu vàng, dưới 1 triệu.",
    "Shop tư vấn giúp mình bó hoa nhẹ nhàng để cảm ơn cô giáo.",
    "Tôi muốn bó hoa tặng người yêu nhưng không dùng hoa hồng đỏ."
]

selected_sample = st.selectbox(
    "Chọn câu test nhanh:",
    sample_requests
)

customer_message = st.text_area(
    "Nhập yêu cầu khách hàng:",
    value=selected_sample,
    height=100
)

run_button = st.button("Recommend bouquet", type="primary")


# ============================================================
# Run pipeline
# ============================================================

if run_button:
    try:
        with st.spinner("Đang xử lý pipeline..."):

            # Step 1: Extract requirement JSON
            if demo_mode == "Mock Extractor Local":
                requirements = mock_extract_requirements(customer_message)
            else:
                st.warning(
                    "Chế độ Full Extractor chưa được nối trong UI này. "
                    "Tạm thời dùng Mock Extractor để demo local."
                )
                requirements = mock_extract_requirements(customer_message)

            # Step 2: Init pipeline components
            retriever = HybridRetriever()
            inventory_filter = InventoryFilter()
            scorer = RecommendationScorer()

            # Step 3: RAG retrieval
            retrieved_flowers = retriever.retrieve(
                requirements=requirements,
                top_k=8
            )

            # Step 4: Inventory filter
            candidates = inventory_filter.filter_candidates(
                retrieved_flowers=retrieved_flowers,
                requirements=requirements
            )

            # Step 5: Recommendation scoring
            scored_candidates = scorer.score_candidates(
                candidates=candidates,
                requirements=requirements,
                top_k=10
            )

            # Step 6: Build bouquet
            bouquet = build_simple_bouquet(
                scored_candidates=scored_candidates,
                requirements=requirements
            )

            # Step 7: Generate response
            response = generate_customer_response(
                requirements=requirements,
                bouquet=bouquet
            )

        st.success("Pipeline completed!")

        # ====================================================
        # Top customer response
        # ====================================================

        st.subheader("Final Customer Response")
        st.success(response)

        # ====================================================
        # Tabs for demo details
        # ====================================================

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Extracted JSON",
            "Recommended Bouquet",
            "Retrieved Flowers",
            "Inventory Candidates",
            "Scored Candidates"
        ])

        with tab1:
            st.subheader("Output của Extractor")
            st.write(
                "Đây là JSON có cấu trúc được trích xuất từ câu khách hàng. "
                "Trong bản demo local, phần này đang được mock theo schema của fine-tuned model."
            )
            st.json(requirements)

        with tab2:
            st.subheader("Recommended Bouquet JSON")
            if bouquet:
                st.json(bouquet)
            else:
                st.warning("Chưa có bouquet output.")

        with tab3:
            st.subheader("Retrieved Flowers from Hybrid RAG")

            if retrieved_flowers:
                rag_table = []
                for item in retrieved_flowers:
                    rag_table.append({
                        "flower_name": item.get("flower_name"),
                        "rag_score": round(item.get("score", 0), 4),
                        "retrieval_source": ", ".join(item.get("retrieval_source", []))
                    })

                st.dataframe(rag_table, use_container_width=True)
            else:
                st.warning("Không retrieve được hoa nào từ RAG.")

        with tab4:
            st.subheader("Available Inventory Candidates")

            if candidates:
                candidate_table = []
                for item in candidates:
                    candidate_table.append({
                        "variant_name": item["variant_name"],
                        "base_flower": item["base_flower_name"],
                        "color": item["color"],
                        "stock": item["stock_quantity"],
                        "price": int(item["selling_price"]),
                        "freshness": item["freshness_status"],
                        "status": item["status"],
                        "rag_score": round(item["rag_score"], 4)
                    })

                st.dataframe(candidate_table, use_container_width=True)
            else:
                st.warning("Không có flower variant nào còn hàng sau khi filter inventory.")

        with tab5:
            st.subheader("Scored Candidates")

            if scored_candidates:
                scored_table = []
                for item in scored_candidates:
                    scored_table.append({
                        "variant_name": item["variant_name"],
                        "final_score": item["final_score"],
                        "required_flower": item["score_breakdown"]["required_flower_score"],
                        "rag": item["score_breakdown"]["rag_score"],
                        "color": item["score_breakdown"]["color_score"],
                        "stock": item["score_breakdown"]["stock_score"],
                        "freshness": item["score_breakdown"]["freshness_score"],
                        "price": item["score_breakdown"]["price_score"],
                    })

                st.dataframe(scored_table, use_container_width=True)

                st.subheader("Top Candidate Details")
                st.json(scored_candidates[0])
            else:
                st.warning("Không có candidate nào được chấm điểm.")

    except Exception as e:
        st.error("Pipeline failed!")
        st.exception(e)