"""
Sinh file knowledge base (cơ sở tri thức) về các loài hoa phổ biến ở Việt Nam,
phục vụ cho hệ thống AI gợi ý phối bó hoa (bouquet recommendation).
Schema:
    flower_id            : mã định danh loài hoa (F001, F002, ...)
    flower_name           : tên tiếng Việt
    english_name          : tên tiếng Anh
    available_colors      : các màu sắc phổ biến, phân tách bằng ';'
    meanings              : ý nghĩa biểu trưng, phân tách bằng ';'
    suitable_occasions    : dịp phù hợp để tặng/cắm, phân tách bằng ';'
    style_tags            : phong cách/tag mô tả, phân tách bằng ';'
    bouquet_role          : vai trò trong bó hoa (hoa chủ đạo / hoa phụ trợ / hoa nền - lá / điểm nhấn)
    price_level           : mức giá tương đối (thấp / trung bình / cao / rất cao)
    compatible_flowers    : các loài hoa phối hợp tốt, phân tách bằng ';'
    description           : mô tả ngắn gọn về loài hoa
"""
import os
import sys
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Dữ liệu 50 loài hoa phổ biến tại Việt Nam

FLOWERS = [
    dict(
        flower_name="Hoa hồng", english_name="Rose",
        available_colors="đỏ;hồng;trắng;vàng;cam;tím",
        meanings="tình yêu;đam mê;lãng mạn;sắc đẹp",
        suitable_occasions="Valentine;kỷ niệm ngày cưới;tỏ tình;sinh nhật;20/10",
        style_tags="lãng mạn;cổ điển;sang trọng",
        bouquet_role="hoa chủ đạo",
        price_level="trung bình",
        compatible_flowers="Hoa baby;Hoa cẩm tú cầu;Hoa cát tường;Hoa xác pháo",
        description="Loài hoa biểu tượng của tình yêu, có hàng trăm giống với màu sắc và hương thơm đa dạng, gần như không thể thiếu trong các bó hoa lãng mạn."
    ),
    dict(
        flower_name="Hoa cúc", english_name="Chrysanthemum",
        available_colors="vàng;trắng;tím;cam;đỏ",
        meanings="sự trường thọ;lòng hiếu thảo;niềm vui;sự chân thành",
        suitable_occasions="lễ Vu Lan;viếng tang;mừng thọ;Tết Trung thu",
        style_tags="trang trọng;truyền thống;mộc mạc",
        bouquet_role="hoa chủ đạo",
        price_level="thấp",
        compatible_flowers="Hoa cúc họa mi;Hoa lay ơn;Hoa baby",
        description="Loài hoa quen thuộc trong văn hóa Á Đông, tượng trưng cho sự trường tồn và lòng biết ơn, thường dùng trong dịp lễ và cúng viếng."
    ),
    dict(
        flower_name="Hoa lan hồ điệp", english_name="Phalaenopsis Orchid",
        available_colors="trắng;hồng;tím;vàng;đỏ đốm",
        meanings="sự sang trọng;tình yêu hoàn mỹ;phú quý",
        suitable_occasions="khai trương;Tết Nguyên Đán;chúc mừng thăng chức;tân gia",
        style_tags="sang trọng;hiện đại;quý phái",
        bouquet_role="hoa chủ đạo",
        price_level="cao",
        compatible_flowers="Hoa lan vũ nữ;Hoa ngọc lan;Hoa hồng môn",
        description="Loài lan cánh bướm quý phái, cánh hoa mềm mại bền lâu, thường được cắm thành chậu hoặc giỏ trong các dịp lễ trọng đại."
    ),
    dict(
        flower_name="Hoa ly", english_name="Lily",
        available_colors="trắng;hồng;vàng;cam;đỏ",
        meanings="sự thuần khiết;kiêu hãnh;quyền quý",
        suitable_occasions="khai trương;sinh nhật;chúc mừng;tân gia",
        style_tags="sang trọng;rực rỡ;hương thơm nồng",
        bouquet_role="hoa chủ đạo",
        price_level="cao",
        compatible_flowers="Hoa hồng;Hoa cát tường;Hoa lay ơn",
        description="Hoa có hương thơm nồng nàn, cánh to xòe rộng, mang vẻ đẹp kiêu sa và thường xuất hiện trong các bó hoa chúc mừng lớn."
    ),
    dict(
        flower_name="Hoa hướng dương", english_name="Sunflower",
        available_colors="vàng;cam",
        meanings="sự lạc quan;niềm tin;hướng về ánh sáng;trung thành",
        suitable_occasions="sinh nhật;động viên tinh thần;tốt nghiệp",
        style_tags="tươi sáng;năng động;mộc mạc",
        bouquet_role="hoa chủ đạo",
        price_level="trung bình",
        compatible_flowers="Hoa cúc;Hoa đồng tiền;Hoa baby",
        description="Loài hoa luôn hướng về phía mặt trời, biểu tượng cho sự lạc quan và nguồn năng lượng tích cực."
    ),
    dict(
        flower_name="Hoa tulip", english_name="Tulip",
        available_colors="đỏ;hồng;vàng;tím;trắng;cam",
        meanings="tình yêu hoàn hảo;sự khai mở;danh vọng",
        suitable_occasions="Valentine;8/3;tỏ tình;sinh nhật",
        style_tags="hiện đại;tối giản;tinh tế",
        bouquet_role="hoa chủ đạo",
        price_level="cao",
        compatible_flowers="Hoa baby;Hoa cát tường;Hoa thủy tiên",
        description="Hoa nhập khẩu từ Hà Lan với dáng cúp thanh lịch, được ưa chuộng trong các bó hoa phong cách tối giản hiện đại."
    ),
    dict(
        flower_name="Hoa cẩm chướng", english_name="Carnation",
        available_colors="đỏ;hồng;trắng;vàng;tím",
        meanings="tình mẫu tử;lòng biết ơn;sự ngưỡng mộ",
        suitable_occasions="ngày của Mẹ;20/11;sinh nhật;lễ tốt nghiệp",
        style_tags="ngọt ngào;truyền thống;ấm áp",
        bouquet_role="hoa phụ trợ",
        price_level="thấp",
        compatible_flowers="Hoa hồng;Hoa baby;Hoa cúc",
        description="Loài hoa cánh xếp gợn sóng bền màu, thường được chọn để tặng mẹ và thầy cô vì mang ý nghĩa biết ơn sâu sắc."
    ),
    dict(
        flower_name="Hoa baby", english_name="Baby's Breath",
        available_colors="trắng;hồng nhạt",
        meanings="tình yêu trong sáng;sự thuần khiết;niềm vui nhỏ bé",
        suitable_occasions="cưới hỏi;tỏ tình;trang trí phối nền",
        style_tags="nhẹ nhàng;lãng mạn;vintage",
        bouquet_role="hoa nền - lá",
        price_level="thấp",
        compatible_flowers="Hoa hồng;Hoa tulip;Hoa cát tường;Hoa hướng dương",
        description="Chùm hoa li ti mềm mại thường dùng để độn nền, tạo hiệu ứng bồng bềnh lãng mạn cho bó hoa chính."
    ),
    dict(
        flower_name="Hoa đồng tiền", english_name="Gerbera",
        available_colors="đỏ;cam;vàng;hồng;trắng",
        meanings="sự vui vẻ;may mắn;tài lộc",
        suitable_occasions="khai trương;chúc mừng;sinh nhật",
        style_tags="tươi sáng;trẻ trung;năng động",
        bouquet_role="hoa chủ đạo",
        price_level="thấp",
        compatible_flowers="Hoa hướng dương;Hoa cúc;Hoa baby",
        description="Cánh hoa tròn xoè rực rỡ, tượng trưng cho may mắn và niềm vui, rất phổ biến trong hoa khai trương."
    ),
    dict(
        flower_name="Hoa thược dược", english_name="Dahlia",
        available_colors="đỏ;hồng;cam;tím;trắng",
        meanings="sự sang trọng;lòng chung thủy;đổi mới",
        suitable_occasions="Tết Nguyên Đán;tân gia;chúc mừng",
        style_tags="rực rỡ;cổ điển;sang trọng",
        bouquet_role="hoa chủ đạo",
        price_level="trung bình",
        compatible_flowers="Hoa mẫu đơn;Hoa hồng;Hoa cúc",
        description="Cánh hoa xếp lớp cầu kỳ, thường nở rộ vào dịp Tết, tượng trưng cho sự sung túc và khởi đầu mới."
    ),
    dict(
        flower_name="Hoa mẫu đơn", english_name="Peony",
        available_colors="hồng;đỏ;trắng;cam pastel",
        meanings="phú quý;vinh hoa;tình yêu lãng mạn",
        suitable_occasions="cưới hỏi;tân gia;chúc mừng thành đạt",
        style_tags="sang trọng;lãng mạn;cổ điển",
        bouquet_role="hoa chủ đạo",
        price_level="rất cao",
        compatible_flowers="Hoa hồng;Hoa cát tường;Hoa baby",
        description="Được mệnh danh 'vua của các loài hoa', mẫu đơn có cánh xếp tầng bồng bềnh, biểu trưng cho sự giàu sang phú quý."
    ),
    dict(
        flower_name="Hoa sen", english_name="Lotus",
        available_colors="hồng;trắng;đỏ",
        meanings="sự thanh cao;thuần khiết;giác ngộ",
        suitable_occasions="lễ Phật đản;cúng viếng;trang trí tâm linh",
        style_tags="thanh tịnh;truyền thống;mộc mạc",
        bouquet_role="hoa chủ đạo",
        price_level="trung bình",
        compatible_flowers="Hoa súng;Hoa nhài;Hoa ngọc lan",
        description="Quốc hoa của Việt Nam, mọc lên từ bùn nhưng vẫn giữ vẻ thanh khiết, gắn liền với văn hóa và tâm linh Việt."
    ),
    dict(
        flower_name="Hoa súng", english_name="Water Lily",
        available_colors="tím;hồng;trắng;xanh nhạt",
        meanings="sự tinh khôi;bình yên;tái sinh",
        suitable_occasions="trang trí sân vườn;triển lãm hoa;trang trí hồ nước",
        style_tags="thanh bình;tự nhiên;mộc mạc",
        bouquet_role="điểm nhấn",
        price_level="trung bình",
        compatible_flowers="Hoa sen;Hoa nhài",
        description="Loài hoa nổi trên mặt nước với sắc thái dịu nhẹ, thường dùng trang trí không gian mang tính thư giãn."
    ),
    dict(
        flower_name="Hoa mai", english_name="Apricot Blossom",
        available_colors="vàng",
        meanings="sự thịnh vượng;may mắn đầu năm;phú quý",
        suitable_occasions="Tết Nguyên Đán",
        style_tags="truyền thống;miền Nam;lễ hội",
        bouquet_role="hoa chủ đạo",
        price_level="cao",
        compatible_flowers="Hoa cúc;Hoa lan hồ điệp;Hoa đào",
        description="Biểu tượng mùa xuân miền Nam Việt Nam, cánh hoa vàng rực báo hiệu một năm mới an khang thịnh vượng."
    ),
    dict(
        flower_name="Hoa đào", english_name="Peach Blossom",
        available_colors="hồng;đỏ;trắng",
        meanings="sự may mắn;xua đuổi tà khí;tình yêu đầu xuân",
        suitable_occasions="Tết Nguyên Đán",
        style_tags="truyền thống;miền Bắc;lễ hội",
        bouquet_role="hoa chủ đạo",
        price_level="cao",
        compatible_flowers="Hoa mai;Hoa cúc;Hoa lay ơn",
        description="Biểu tượng mùa xuân miền Bắc Việt Nam, sắc hồng của hoa đào gắn liền với không khí Tết cổ truyền."
    ),
    dict(
        flower_name="Hoa lay ơn", english_name="Gladiolus",
        available_colors="đỏ;hồng;vàng;trắng;cam",
        meanings="sự chính trực;sức mạnh;danh dự",
        suitable_occasions="Tết Nguyên Đán;lễ kỷ niệm;viếng tang",
        style_tags="trang trọng;truyền thống;thẳng thắn",
        bouquet_role="hoa nền - lá",
        price_level="thấp",
        compatible_flowers="Hoa cúc;Hoa hồng;Hoa đào",
        description="Thân hoa cao thẳng với nhiều bông nhỏ mọc dọc thân, thường dùng để tạo chiều cao cho bó hoa hoặc lẵng hoa lớn."
    ),
    dict(
        flower_name="Hoa violet", english_name="Violet",
        available_colors="tím;xanh tím;trắng",
        meanings="sự thủy chung;khiêm nhường;tình yêu nhẹ nhàng",
        suitable_occasions="tỏ tình;tặng bạn thân;trang trí bàn học",
        style_tags="nhẹ nhàng;dịu dàng;nữ tính",
        bouquet_role="hoa phụ trợ",
        price_level="thấp",
        compatible_flowers="Hoa baby;Hoa păng xê;Hoa oải hương",
        description="Loài hoa nhỏ nhắn sắc tím dịu dàng, thường được yêu thích bởi sự khiêm nhường và tinh tế."
    ),
    dict(
        flower_name="Hoa oải hương", english_name="Lavender",
        available_colors="tím",
        meanings="sự tĩnh lặng;chữa lành;thanh khiết",
        suitable_occasions="quà tặng thư giãn;trang trí phòng ngủ;handmade",
        style_tags="vintage;lãng mạn;hương thơm dịu",
        bouquet_role="hoa nền - lá",
        price_level="trung bình",
        compatible_flowers="Hoa hồng;Hoa cúc họa mi;Hoa baby",
        description="Hương thơm dịu nhẹ giúp thư giãn tinh thần, thường xuất hiện trong bó hoa khô hoặc set quà tặng vintage."
    ),
    dict(
        flower_name="Hoa loa kèn", english_name="Easter Lily",
        available_colors="trắng",
        meanings="sự thuần khiết;hy vọng;tinh khôi",
        suitable_occasions="lễ Phục sinh;tháng Tư;trang trí nhà thờ",
        style_tags="thanh lịch;tinh khôi;mùa hè",
        bouquet_role="hoa chủ đạo",
        price_level="trung bình",
        compatible_flowers="Hoa baby;Hoa cát tường;Hoa hồng trắng",
        description="Cánh hoa trắng muốt hình loa kèn, nở rộ vào tháng Tư, mang vẻ đẹp thanh khiết và tinh tế."
    ),
    dict(
        flower_name="Hoa dạ yến thảo", english_name="Petunia",
        available_colors="tím;hồng;trắng;đỏ",
        meanings="sự gắn kết;ấm áp gia đình",
        suitable_occasions="trang trí ban công;trang trí sân vườn",
        style_tags="rực rỡ;mộc mạc;trang trí ngoại thất",
        bouquet_role="điểm nhấn",
        price_level="thấp",
        compatible_flowers="Hoa mười giờ;Hoa dừa cạn",
        description="Loài hoa dạng dây rủ mềm mại, được trồng phổ biến để trang trí ban công và sân vườn nhiều màu sắc."
    ),
    dict(
        flower_name="Hoa păng xê", english_name="Pansy",
        available_colors="tím;vàng;trắng;cam",
        meanings="sự suy tư;tình yêu thầm lặng",
        suitable_occasions="trang trí bàn tiệc;quà tặng nhỏ xinh",
        style_tags="dễ thương;nhẹ nhàng;mùa xuân",
        bouquet_role="điểm nhấn",
        price_level="thấp",
        compatible_flowers="Hoa violet;Hoa thủy tiên",
        description="Cánh hoa có hình dạng như khuôn mặt nhỏ nhắn nhiều màu, thường dùng trang trí tiểu cảnh và bàn tiệc."
    ),
    dict(
        flower_name="Hoa cát tường", english_name="Lisianthus",
        available_colors="trắng;tím;hồng;vàng nhạt",
        meanings="sự may mắn;lời chúc phúc;niềm vui trọn vẹn",
        suitable_occasions="chúc mừng;tân gia;sinh nhật;cưới hỏi",
        style_tags="thanh lịch;nhẹ nhàng;hiện đại",
        bouquet_role="hoa chủ đạo",
        price_level="trung bình",
        compatible_flowers="Hoa hồng;Hoa baby;Hoa tulip",
        description="Cánh hoa mỏng manh như lụa với dáng nở tương tự hoa hồng, mang ý nghĩa lời chúc phúc tốt đẹp."
    ),
    dict(
        flower_name="Hoa trạng nguyên", english_name="Poinsettia",
        available_colors="đỏ;trắng;hồng",
        meanings="niềm vui;sự thành đạt;chúc mừng Giáng sinh",
        suitable_occasions="Giáng sinh;chúc mừng đỗ đạt;tất niên",
        style_tags="rực rỡ;lễ hội;ấm cúng",
        bouquet_role="điểm nhấn",
        price_level="trung bình",
        compatible_flowers="Hoa hồng đỏ;Hoa cúc",
        description="Lá bắc đỏ rực đặc trưng cho mùa Giáng sinh, thường được chọn làm quà chúc mừng thành công."
    ),
    dict(
        flower_name="Hoa hải đường", english_name="Camellia (Japonica)",
        available_colors="đỏ;hồng;trắng",
        meanings="sự khiêm nhường;tình yêu bền vững",
        suitable_occasions="Tết Nguyên Đán;chúc thọ",
        style_tags="truyền thống;quý phái;cổ điển",
        bouquet_role="hoa chủ đạo",
        price_level="trung bình",
        compatible_flowers="Hoa mai;Hoa đào",
        description="Hoa nở đúng dịp Tết với sắc đỏ tươi tắn, tượng trưng cho tình yêu bền vững và sự khiêm nhường cao quý."
    ),
    dict(
        flower_name="Hoa trà", english_name="Camellia",
        available_colors="trắng;hồng;đỏ",
        meanings="sự hoàn hảo;tình yêu trường tồn",
        suitable_occasions="trang trí trà đạo;quà tặng tinh tế",
        style_tags="thanh lịch;Nhật Bản;tối giản",
        bouquet_role="hoa phụ trợ",
        price_level="trung bình",
        compatible_flowers="Hoa hải đường;Hoa ngọc lan",
        description="Cánh hoa dày mịn như nhung, thường gắn với văn hóa trà đạo và vẻ đẹp tinh tế, trầm lắng."
    ),
    dict(
        flower_name="Hoa sim", english_name="Rose Myrtle",
        available_colors="tím",
        meanings="ký ức;sự mộc mạc;tình yêu quê hương",
        suitable_occasions="trang trí quê;quà lưu niệm",
        style_tags="mộc mạc;hoài niệm;đồng quê",
        bouquet_role="điểm nhấn",
        price_level="thấp",
        compatible_flowers="Hoa mười giờ;Hoa dừa cạn",
        description="Loài hoa dại mọc trên đồi núi Việt Nam, gợi nhớ ký ức tuổi thơ và vẻ đẹp bình dị của làng quê."
    ),
    dict(
        flower_name="Hoa bằng lăng", english_name="Crape Myrtle",
        available_colors="tím",
        meanings="tuổi học trò;sự chờ đợi;kỷ niệm",
        suitable_occasions="mùa hè;lễ tốt nghiệp;kỷ niệm thanh xuân",
        style_tags="hoài niệm;học trò;mùa hè",
        bouquet_role="điểm nhấn",
        price_level="thấp",
        compatible_flowers="Hoa phượng;Hoa baby",
        description="Sắc tím đặc trưng của mùa hè Việt Nam, thường gắn liền với ký ức tuổi học trò và mùa chia tay."
    ),
    dict(
        flower_name="Hoa phượng", english_name="Flame Tree Flower",
        available_colors="đỏ;cam đỏ",
        meanings="tuổi học trò;mùa hè;chia ly lưu luyến",
        suitable_occasions="lễ tốt nghiệp;mùa hè;kỷ niệm thanh xuân",
        style_tags="rực rỡ;hoài niệm;học trò",
        bouquet_role="điểm nhấn",
        price_level="thấp",
        compatible_flowers="Hoa bằng lăng;Hoa hướng dương",
        description="Sắc đỏ rực trời hè, biểu tượng quen thuộc gắn với tuổi học trò và mùa chia tay bịn rịn."
    ),
    dict(
        flower_name="Hoa giấy", english_name="Bougainvillea",
        available_colors="hồng;tím;cam;trắng;đỏ",
        meanings="sự kiên cường;bền bỉ;đam mê",
        suitable_occasions="trang trí cổng nhà;trang trí quán cà phê",
        style_tags="mộc mạc;rực rỡ;nhiệt đới",
        bouquet_role="điểm nhấn",
        price_level="thấp",
        compatible_flowers="Hoa dừa cạn;Hoa mười giờ",
        description="Cánh hoa mỏng như giấy, sức sống mãnh liệt trong nắng gió, thường leo giàn trang trí không gian ngoài trời."
    ),
    dict(
        flower_name="Hoa quỳnh", english_name="Queen of the Night",
        available_colors="trắng",
        meanings="vẻ đẹp phù du;sự trân quý khoảnh khắc",
        suitable_occasions="thưởng hoa đêm;quà tặng người yêu nghệ thuật",
        style_tags="huyền bí;thanh tao;hiếm quý",
        bouquet_role="điểm nhấn",
        price_level="cao",
        compatible_flowers="Hoa nhài;Hoa ngọc lan",
        description="Chỉ nở rộ và tỏa hương trong một đêm ngắn ngủi, tượng trưng cho vẻ đẹp thoáng qua nhưng đầy ấn tượng."
    ),
    dict(
        flower_name="Hoa nhài", english_name="Jasmine",
        available_colors="trắng",
        meanings="sự thuần khiết;duyên dáng;tình bạn đẹp",
        suitable_occasions="ướp trà;quà tặng nhẹ nhàng;trang trí không gian thư giãn",
        style_tags="nhẹ nhàng;thanh tao;hương thơm dịu",
        bouquet_role="hoa nền - lá",
        price_level="thấp",
        compatible_flowers="Hoa sen;Hoa ngọc lan;Hoa quỳnh",
        description="Hương thơm ngát dịu dàng, thường dùng ướp trà và tượng trưng cho sự thuần khiết, duyên dáng."
    ),
    dict(
        flower_name="Hoa ngọc lan", english_name="Champaca",
        available_colors="trắng;vàng nhạt",
        meanings="sự thanh cao;hoài niệm;tình yêu sâu lắng",
        suitable_occasions="quà tặng người lớn tuổi;trang trí sân vườn",
        style_tags="hoài niệm;thanh nhã;hương thơm nồng",
        bouquet_role="hoa nền - lá",
        price_level="trung bình",
        compatible_flowers="Hoa sen;Hoa nhài;Hoa lan hồ điệp",
        description="Hương thơm nồng nàn đặc trưng thường gắn với ký ức phố cổ Hà Nội, mang vẻ đẹp thanh cao hoài niệm."
    ),
    dict(
        flower_name="Hoa mộc lan", english_name="Magnolia",
        available_colors="trắng;hồng;tím",
        meanings="sự cao quý;tình yêu thuần khiết;kiên cường",
        suitable_occasions="chúc mừng;tân gia;trang trí sự kiện mùa xuân",
        style_tags="thanh lịch;sang trọng;mùa xuân",
        bouquet_role="hoa chủ đạo",
        price_level="cao",
        compatible_flowers="Hoa mẫu đơn;Hoa lan hồ điệp",
        description="Cánh hoa to bản mềm mại, nở rộ đầu xuân, tượng trưng cho vẻ đẹp cao quý và sự kiên cường."
    ),
    dict(
        flower_name="Hoa dâm bụt", english_name="Hibiscus",
        available_colors="đỏ;hồng;vàng;cam",
        meanings="vẻ đẹp mong manh;sự tận hưởng hiện tại",
        suitable_occasions="trang trí sân vườn;trang trí resort",
        style_tags="nhiệt đới;mộc mạc;rực rỡ",
        bouquet_role="điểm nhấn",
        price_level="thấp",
        compatible_flowers="Hoa giấy;Hoa dừa cạn",
        description="Cánh hoa mỏng manh nở rồi tàn trong ngày, biểu tượng cho vẻ đẹp nhiệt đới tươi mới mỗi sớm mai."
    ),
    dict(
        flower_name="Hoa anh túc", english_name="Poppy",
        available_colors="đỏ;cam;hồng;trắng",
        meanings="sự tưởng nhớ;giấc mơ;vẻ đẹp mong manh",
        suitable_occasions="tưởng niệm;trang trí nghệ thuật",
        style_tags="nghệ thuật;hoài niệm;mong manh",
        bouquet_role="điểm nhấn",
        price_level="trung bình",
        compatible_flowers="Hoa thủy tiên;Hoa cúc họa mi",
        description="Cánh hoa mỏng như lụa rung rinh trong gió, thường gợi cảm giác hoài niệm và vẻ đẹp mong manh."
    ),
    dict(
        flower_name="Hoa thủy tiên", english_name="Daffodil",
        available_colors="vàng;trắng",
        meanings="sự khởi đầu mới;may mắn;hy vọng",
        suitable_occasions="Tết Nguyên Đán;khai trương;năm mới",
        style_tags="tươi mới;thanh lịch;mùa xuân",
        bouquet_role="hoa chủ đạo",
        price_level="cao",
        compatible_flowers="Hoa tulip;Hoa lan hồ điệp",
        description="Loài hoa quý được gọt tỉa công phu vào dịp Tết, tượng trưng cho sự khởi đầu suôn sẻ và may mắn."
    ),
    dict(
        flower_name="Hoa mimosa", english_name="Mimosa",
        available_colors="vàng",
        meanings="sự nhạy cảm;tình yêu dịu dàng;mùa xuân",
        suitable_occasions="8/3;tỏ tình;mùa xuân Đà Lạt",
        style_tags="lãng mạn;mùa xuân;nhẹ nhàng",
        bouquet_role="hoa nền - lá",
        price_level="trung bình",
        compatible_flowers="Hoa tulip;Hoa baby;Hoa cúc họa mi",
        description="Từng chùm hoa vàng li ti bồng bềnh, đặc sản mùa xuân Đà Lạt, biểu tượng cho tình yêu dịu dàng."
    ),
    dict(
        flower_name="Hoa cẩm tú cầu", english_name="Hydrangea",
        available_colors="xanh;tím;hồng;trắng",
        meanings="lòng biết ơn;sự chân thành;đoàn kết gia đình",
        suitable_occasions="cưới hỏi;tân gia;20/11",
        style_tags="lãng mạn;vintage;sang trọng",
        bouquet_role="hoa chủ đạo",
        price_level="cao",
        compatible_flowers="Hoa hồng;Hoa baby;Hoa cát tường",
        description="Từng chùm hoa nhỏ kết thành bông tròn lớn, đổi màu theo độ pH đất, biểu tượng cho lòng biết ơn chân thành."
    ),
    dict(
        flower_name="Hoa xác pháo", english_name="Ixora",
        available_colors="đỏ;cam;vàng",
        meanings="niềm vui;sự sum vầy;may mắn",
        suitable_occasions="Tết Nguyên Đán;lễ hội;trang trí sân vườn",
        style_tags="rực rỡ;lễ hội;truyền thống",
        bouquet_role="điểm nhấn",
        price_level="thấp",
        compatible_flowers="Hoa hồng;Hoa cúc",
        description="Chùm hoa nhỏ kết dày đặc rực rỡ, thường trồng làm cảnh và trang trí dịp lễ Tết sum vầy."
    ),
    dict(
        flower_name="Hoa bồ công anh", english_name="Dandelion",
        available_colors="vàng;trắng",
        meanings="ước mơ;sự tự do;lời ước nguyện",
        suitable_occasions="quà tặng ý nghĩa;trang trí concept nghệ thuật",
        style_tags="mộng mơ;tự do;nghệ thuật",
        bouquet_role="điểm nhấn",
        price_level="thấp",
        compatible_flowers="Hoa cúc họa mi;Hoa lưu ly",
        description="Loài hoa dại gắn với những điều ước, khi hạt bay theo gió tượng trưng cho sự tự do và hy vọng."
    ),
    dict(
        flower_name="Hoa lưu ly", english_name="Forget-me-not",
        available_colors="xanh;tím nhạt",
        meanings="sự thủy chung;nỗi nhớ;tình yêu vĩnh cửu",
        suitable_occasions="tỏ tình;kỷ niệm;chia tay lưu luyến",
        style_tags="nhẹ nhàng;hoài niệm;lãng mạn",
        bouquet_role="hoa nền - lá",
        price_level="thấp",
        compatible_flowers="Hoa baby;Hoa violet",
        description="Những bông hoa nhỏ xanh biếc mang thông điệp 'đừng quên em', biểu tượng cho tình yêu và nỗi nhớ da diết."
    ),
    dict(
        flower_name="Hoa loa kèn đỏ", english_name="Amaryllis",
        available_colors="đỏ;hồng;trắng",
        meanings="niềm kiêu hãnh;vẻ đẹp rực rỡ;sự tự tin",
        suitable_occasions="Giáng sinh;năm mới;chúc mừng thành công",
        style_tags="rực rỡ;sang trọng;lễ hội",
        bouquet_role="hoa chủ đạo",
        price_level="cao",
        compatible_flowers="Hoa trạng nguyên;Hoa hồng đỏ",
        description="Bông hoa lớn rực rỡ nở vào mùa lễ hội cuối năm, biểu tượng cho sự tự tin và vẻ đẹp kiêu hãnh."
    ),
    dict(
        flower_name="Hoa hồng môn", english_name="Anthurium",
        available_colors="đỏ;hồng;trắng",
        meanings="lòng hiếu khách;sự thịnh vượng;tình yêu bền vững",
        suitable_occasions="tân gia;khai trương;chúc mừng",
        style_tags="hiện đại;nhiệt đới;độc đáo",
        bouquet_role="điểm nhấn",
        price_level="trung bình",
        compatible_flowers="Hoa lan hồ điệp;Hoa thiên điểu",
        description="Lá bắc bóng mượt hình trái tim đặc trưng, tượng trưng cho lòng hiếu khách và sự thịnh vượng lâu dài."
    ),
    dict(
        flower_name="Hoa lan vũ nữ", english_name="Oncidium Orchid",
        available_colors="vàng;tím;trắng;cam",
        meanings="niềm vui;sự tự do;tình bạn",
        suitable_occasions="chúc mừng;khai trương;sinh nhật",
        style_tags="hiện đại;bay bổng;độc đáo",
        bouquet_role="hoa phụ trợ",
        price_level="trung bình",
        compatible_flowers="Hoa lan hồ điệp;Hoa cát tường",
        description="Từng chùm hoa nhỏ rung rinh như đàn bướm múa, mang lại cảm giác vui tươi phóng khoáng cho bó hoa."
    ),
    dict(
        flower_name="Hoa lan hoàng thảo", english_name="Dendrobium Orchid",
        available_colors="tím;trắng;vàng;hồng",
        meanings="sự tinh tế;vẻ đẹp bền bỉ;trí tuệ",
        suitable_occasions="chúc mừng;tân gia;sự kiện trang trọng",
        style_tags="thanh lịch;bền bỉ;hiện đại",
        bouquet_role="hoa phụ trợ",
        price_level="trung bình",
        compatible_flowers="Hoa lan hồ điệp;Hoa hồng môn",
        description="Cành hoa dài với nhiều bông nhỏ xếp đều, bền màu lâu, thường dùng phối trong lẵng hoa chúc mừng."
    ),
    dict(
        flower_name="Hoa cúc họa mi", english_name="Daisy",
        available_colors="trắng;vàng nhạt",
        meanings="sự trong sáng;tình yêu ngây thơ;hy vọng",
        suitable_occasions="mùa thu Hà Nội;tỏ tình;chụp ảnh kỷ niệm",
        style_tags="mộc mạc;trong trẻo;mùa thu",
        bouquet_role="hoa chủ đạo",
        price_level="thấp",
        compatible_flowers="Hoa baby;Hoa lưu ly;Hoa oải hương",
        description="Loài hoa báo hiệu mùa thu Hà Nội, cánh trắng mỏng manh quanh nhụy vàng, tượng trưng cho sự trong sáng."
    ),
    dict(
        flower_name="Hoa cúc tần", english_name="Wild Chrysanthemum",
        available_colors="vàng;trắng",
        meanings="sự bình dị;sức sống bền bỉ",
        suitable_occasions="trang trí hàng rào;cảnh quan tự nhiên",
        style_tags="mộc mạc;đồng quê;bền bỉ",
        bouquet_role="hoa nền - lá",
        price_level="thấp",
        compatible_flowers="Hoa cúc;Hoa dừa cạn",
        description="Loài cúc dại mọc hoang bên đường quê, tuy nhỏ bé nhưng sức sống mãnh liệt quanh năm."
    ),
    dict(
        flower_name="Hoa mào gà", english_name="Cockscomb",
        available_colors="đỏ;vàng;cam;hồng",
        meanings="sự bền vững;tình cảm nồng nàn;may mắn",
        suitable_occasions="cúng lễ;trang trí sân vườn;Tết Trung thu",
        style_tags="truyền thống;rực rỡ;mộc mạc",
        bouquet_role="điểm nhấn",
        price_level="thấp",
        compatible_flowers="Hoa cúc;Hoa lay ơn",
        description="Hình dáng bông hoa như mào gà trống, sắc đỏ rực rỡ, thường dùng trong các dịp cúng lễ truyền thống."
    ),
    dict(
        flower_name="Hoa mười giờ", english_name="Moss Rose (Portulaca)",
        available_colors="hồng;đỏ;vàng;cam;trắng",
        meanings="ký ức tuổi thơ;niềm vui giản dị",
        suitable_occasions="trang trí sân vườn;quà tặng hoài niệm",
        style_tags="mộc mạc;hoài niệm;đồng quê",
        bouquet_role="điểm nhấn",
        price_level="thấp",
        compatible_flowers="Hoa dừa cạn;Hoa dạ yến thảo",
        description="Nở rộ đúng khoảng mười giờ sáng mỗi ngày, gợi nhớ tuổi thơ ở những khu vườn quê giản dị."
    ),
    dict(
        flower_name="Hoa dừa cạn", english_name="Vinca (Periwinkle)",
        available_colors="hồng;trắng;tím",
        meanings="tình bạn thân thiết;sự bền bỉ;niềm vui nhẹ nhàng",
        suitable_occasions="trang trí sân vườn;quà tặng bạn bè",
        style_tags="mộc mạc;bền bỉ;nhẹ nhàng",
        bouquet_role="điểm nhấn",
        price_level="thấp",
        compatible_flowers="Hoa mười giờ;Hoa dạ yến thảo",
        description="Hoa nhỏ nở quanh năm bất kể thời tiết khắc nghiệt, biểu tượng cho tình bạn bền bỉ theo thời gian."
    ),
]

# Sinh flower_id và chuẩn hóa DataFrame

def build_dataframe(flowers: list) -> pd.DataFrame:
    for i, f in enumerate(flowers, start=1):
        f["flower_id"] = f"F{i:03d}"

    columns = [
        "flower_id", "flower_name", "english_name", "available_colors",
        "meanings", "suitable_occasions", "style_tags", "bouquet_role",
        "price_level", "compatible_flowers", "description",
    ]
    df = pd.DataFrame(flowers)[columns]
    return df


def main():
    output_dir = os.path.join("data", "processed")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "flower_knowledge_base.csv")

    df = build_dataframe(FLOWERS)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"Đã tạo {len(df)} loài hoa.")
    print(f"File được lưu tại: {output_path}")


if __name__ == "__main__":
    main()