"""
Sinh dữ liệu tồn kho (inventory) mẫu cho cửa hàng hoa, dựa trên
data/processed/flower_knowledge_base.csv.
Schema output:
    inventory_id        : mã tồn kho (INV0001, INV0002, ...)
    flower_id            : mã loài hoa, tham chiếu flower_knowledge_base.csv
    variant_name          : tên biến thể = flower_name + color (VD: "Hoa hồng đỏ")
    base_flower_name      : tên loài hoa gốc (flower_name)
    color                 : màu sắc cụ thể của biến thể này
    stock_quantity        : số lượng tồn kho (0-40)
    unit                  : đơn vị tính (cành / bông / bó)
    selling_price         : giá bán (VNĐ), phụ thuộc price_level của loài hoa
    freshness_status      : độ tươi dựa trên số ngày nhập kho (fresh/near_expiry/expired)
    days_since_import     : số ngày kể từ khi nhập kho (0-10)
    status                : trạng thái tổng hợp để hiển thị/khuyến nghị
                            (out_of_stock / low_stock / expired / near_expiry / available)
Logic sinh dữ liệu:
    - Với mỗi loài hoa trong flower_knowledge_base, đọc available_colors
      (phân tách bằng ';') và chọn ngẫu nhiên 2-5 màu để tạo thành 2-5 biến thể (variant).
    - stock_quantity: random.randint(0, 40)
    - selling_price: random theo price_level của loài hoa
          thấp / low         -> 10_000 - 30_000
          trung bình / medium -> 30_000 - 70_000
          cao, rất cao / high -> 70_000 - 150_000
    - days_since_import: random.randint(0, 10)
    - freshness_status (dựa trên days_since_import):
          >= 7  -> expired
          >= 5  -> near_expiry
          else  -> fresh
    - status (ưu tiên theo thứ tự sau, khớp điều kiện đầu tiên sẽ dừng):
          1) stock_quantity == 0         -> out_of_stock
          2) stock_quantity <= 3         -> low_stock
          3) days_since_import >= 7      -> expired
          4) days_since_import >= 5      -> near_expiry
          5) còn lại                     -> available
    - unit: xác định theo đặc điểm loài hoa (cành / bông / bó), có fallback mặc định là "cành".
    - random seed = 42 để đảm bảo kết quả tái lập được.
"""

import os
import random
import pandas as pd

RANDOM_SEED = 42
# Ánh xạ mức giá (price_level) -> khoảng giá bán (VNĐ)
PRICE_RANGES = {
    "thấp": (10_000, 30_000),
    "low": (10_000, 30_000),
    "trung bình": (30_000, 70_000),
    "medium": (30_000, 70_000),
    "cao": (70_000, 150_000),
    "rất cao": (70_000, 150_000),
    "high": (70_000, 150_000),
}
DEFAULT_PRICE_RANGE = (30_000, 70_000)  # fallback nếu price_level lạ/không xác định
# Ánh xạ đơn vị tính theo đặc điểm loài hoa
# Hoa dạng chùm nhỏ, thường bán theo bó
UNIT_BO = {
    "Hoa baby", "Hoa oải hương", "Hoa lưu ly", "Hoa mười giờ",
    "Hoa dừa cạn", "Hoa dạ yến thảo", "Hoa păng xê", "Hoa violet",
    "Hoa mimosa", "Hoa xác pháo", "Hoa cúc tần", "Hoa giấy",
}
# Hoa có bông to, thường đếm theo bông
UNIT_BONG = {
    "Hoa hướng dương", "Hoa sen", "Hoa súng", "Hoa quỳnh",
    "Hoa dâm bụt", "Hoa anh túc", "Hoa mộc lan", "Hoa ngọc lan",
    "Hoa nhài", "Hoa trạng nguyên",
}


def get_unit(flower_name: str) -> str:
    """Xác định đơn vị tính (cành / bông / bó) dựa theo tên loài hoa."""
    if flower_name in UNIT_BO:
        return "bó"
    if flower_name in UNIT_BONG:
        return "bông"
    # Mặc định: các loại hoa thân dài, hoa lan, hoa cành cây... tính theo cành
    return "cành"


def get_price_range(price_level: str):
    """Trả về khoảng giá (min, max) theo price_level, có fallback an toàn."""
    if not isinstance(price_level, str):
        return DEFAULT_PRICE_RANGE
    return PRICE_RANGES.get(price_level.strip().lower(), DEFAULT_PRICE_RANGE)


def compute_freshness_status(days_since_import: int) -> str:
    if days_since_import >= 7:
        return "expired"
    if days_since_import >= 5:
        return "near_expiry"
    return "fresh"


def compute_status(stock_quantity: int, days_since_import: int) -> str:
    if stock_quantity == 0:
        return "out_of_stock"
    if stock_quantity <= 3:
        return "low_stock"
    if days_since_import >= 7:
        return "expired"
    if days_since_import >= 5:
        return "near_expiry"
    return "available"


def build_inventory(kb_df: pd.DataFrame, rng: random.Random) -> pd.DataFrame:
    rows = []
    inventory_counter = 1

    for _, flower in kb_df.iterrows():
        flower_id = flower["flower_id"]
        flower_name = flower["flower_name"]
        price_level = flower.get("price_level", "trung bình")

        colors = [c.strip() for c in str(flower["available_colors"]).split(";") if c.strip()]
        if not colors:
            colors = ["tự nhiên"]

        # Chọn ngẫu nhiên 2-5 màu (không vượt quá số màu hiện có) để tạo variant
        num_variants = rng.randint(2, 5)
        num_variants = min(num_variants, len(colors))
        chosen_colors = rng.sample(colors, num_variants) if len(colors) >= num_variants else colors

        price_min, price_max = get_price_range(price_level)
        unit = get_unit(flower_name)

        for color in chosen_colors:
            stock_quantity = rng.randint(0, 40)
            selling_price = rng.randint(price_min, price_max)
            days_since_import = rng.randint(0, 10)

            freshness_status = compute_freshness_status(days_since_import)
            status = compute_status(stock_quantity, days_since_import)

            rows.append({
                "inventory_id": f"INV{inventory_counter:04d}",
                "flower_id": flower_id,
                "variant_name": f"{flower_name} {color}",
                "base_flower_name": flower_name,
                "color": color,
                "stock_quantity": stock_quantity,
                "unit": unit,
                "selling_price": selling_price,
                "freshness_status": freshness_status,
                "days_since_import": days_since_import,
                "status": status,
            })
            inventory_counter += 1

    columns = [
        "inventory_id", "flower_id", "variant_name", "base_flower_name",
        "color", "stock_quantity", "unit", "selling_price",
        "freshness_status", "days_since_import", "status",
    ]
    return pd.DataFrame(rows)[columns]


def main():
    input_path = os.path.join("data", "processed", "flower_knowledge_base.csv")
    output_dir = os.path.join("data", "processed")
    output_path = os.path.join(output_dir, "inventory_sample.csv")

    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Không tìm thấy file input: {input_path}. "
            "Hãy chạy generate_flower_kb.py trước để tạo flower_knowledge_base.csv."
        )

    os.makedirs(output_dir, exist_ok=True)

    kb_df = pd.read_csv(input_path)

    rng = random.Random(RANDOM_SEED)
    inventory_df = build_inventory(kb_df, rng)

    inventory_df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"Đã tạo {len(inventory_df)} biến thể tồn kho từ {len(kb_df)} loài hoa.")
    print(f"File được lưu tại: {output_path}")
    print(inventory_df["status"].value_counts())


if __name__ == "__main__":
    main()