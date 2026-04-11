"""
Generate synthetic nutrition articles cho test pipeline.
Nội dung tập trung vào "nên ăn gì / kiêng gì" theo từng bệnh.

    python -m src.data_pipeline.generate_articles
"""

from __future__ import annotations

import json
import os

ARTICLES = [
    {
        "filename": "syn_tieu_duong_che_do_an.json",
        "source": "Tổng hợp dinh dưỡng",
        "text": """Chế độ ăn cho người bị tiểu đường (đái tháo đường type 2)

Người bị tiểu đường cần kiểm soát chặt lượng carbohydrate và đường nạp vào cơ thể mỗi ngày.

Thực phẩm nên ăn:
- Ngũ cốc nguyên hạt: gạo lứt, yến mạch, bánh mì đen, quinoa — có chỉ số đường huyết thấp, hấp thu chậm
- Rau xanh không tinh bột: rau muống, bông cải xanh, cải bó xôi, dưa leo, cà chua — ăn thoải mái
- Đạm nạc: ức gà, cá hồi, cá thu, trứng gà, đậu phụ — giúp no lâu, không tăng đường huyết đột ngột
- Đậu các loại: đậu xanh, đậu đỏ, đậu đen — giàu chất xơ, protein, GI thấp
- Trái cây ít đường: ổi, bưởi, táo, lê, cam — ăn lượng vừa phải
- Chất béo lành mạnh: dầu ô liu, quả bơ, hạt óc chó, hạnh nhân — tốt cho tim mạch
- Khoai lang thay cơm trắng — GI thấp hơn, nhiều chất xơ hơn

Thực phẩm nên kiêng:
- Cơm trắng, bánh mì trắng, bún, phở, miến — tinh bột tinh chế, tăng đường huyết nhanh
- Đường, mật ong, nước ngọt, nước mía, nước ép trái cây đóng hộp
- Bánh kẹo, kem, chè ngọt, socola sữa
- Thức ăn chiên xào nhiều dầu mỡ — dễ gây béo phì, kháng insulin
- Trái cây nhiều đường: xoài chín, chuối chín, vải, nhãn, mít — ăn ít và hạn chế
- Rượu bia — làm đường huyết không ổn định, gây hạ đường huyết đột ngột

Nguyên tắc ăn uống:
- Chia 3 bữa chính + 1-2 bữa phụ nhỏ, không bỏ bữa
- Ăn đúng giờ, không ăn quá no
- Kiểm soát khẩu phần: dùng đĩa nhỏ, ưu tiên rau chiếm 1/2 đĩa
- Theo dõi đường huyết trước và sau ăn 2 giờ
- Uống đủ nước, tránh nước có đường"""
    },
    {
        "filename": "syn_gout_che_do_an.json",
        "source": "Tổng hợp dinh dưỡng",
        "text": """Chế độ ăn cho người bị bệnh gout (gút)

Bệnh gout xảy ra do nồng độ acid uric trong máu tăng cao, gây lắng đọng tinh thể urate ở khớp. Chế độ ăn đóng vai trò quan trọng trong kiểm soát bệnh.

Thực phẩm nên kiêng hoặc hạn chế tối đa:
- Nội tạng động vật: gan, thận, tim, lòng — cực kỳ cao purine
- Hải sản: tôm, cua, sò, nghêu, mực, cá cơm, cá trích, cá mòi — purine rất cao
- Thịt đỏ: thịt bò, thịt lợn, thịt dê — ăn tối đa 100-150g/ngày
- Rượu bia — đặc biệt bia, làm tăng acid uric mạnh nhất, cần kiêng hoàn toàn khi bùng phát
- Nước ngọt có fructose cao: cola, nước tăng lực
- Đậu các loại khi đợt cấp: đậu nành, đậu xanh, đậu đen — lượng purine trung bình

Thực phẩm nên ăn:
- Rau xanh các loại: cải thảo, bắp cải, dưa leo, cà chua, khoai tây
- Trái cây: anh đào (cherry), cam, dưa hấu, táo — vitamin C giúp thải acid uric
- Sản phẩm từ sữa ít béo: sữa tươi không đường, sữa chua — giúp giảm acid uric
- Trứng gà, đậu phụ — nguồn đạm thay thế thịt, ít purine
- Ngũ cốc: gạo trắng, bánh mì, mì — purine thấp
- Uống nhiều nước: 2-3 lít/ngày giúp thải acid uric qua thận

Lưu ý quan trọng:
- Khi bùng phát cơn gout cấp: kiêng tuyệt đối hải sản, nội tạng, rượu bia
- Duy trì cân nặng hợp lý — béo phì làm tăng acid uric
- Không nhịn ăn hoặc ăn kiêng quá mức — tạo thể ketone làm tăng acid uric"""
    },
    {
        "filename": "syn_huyet_ap_cao_che_do_an.json",
        "source": "Tổng hợp dinh dưỡng",
        "text": """Chế độ ăn cho người bị tăng huyết áp

Tăng huyết áp (cao huyết áp) cần kiểm soát natri, tăng kali và magiê trong chế độ ăn. Chế độ ăn DASH (Dietary Approaches to Stop Hypertension) được khuyến nghị.

Thực phẩm nên ăn:
- Rau xanh giàu kali: rau muống, cải bó xôi, bông cải, khoai lang, khoai tây
- Trái cây: chuối, cam, bưởi, dưa hấu — giàu kali giúp hạ huyết áp
- Các loại đậu: đậu xanh, đậu đỏ, đậu đen — giàu magiê và chất xơ
- Cá béo: cá hồi, cá thu, cá ngừ — omega-3 giúp giảm huyết áp
- Sản phẩm từ sữa ít béo: sữa chua, sữa ít béo — canxi giúp điều hòa huyết áp
- Ngũ cốc nguyên hạt: gạo lứt, yến mạch, bánh mì đen
- Hạt: hạt hướng dương, hạnh nhân, óc chó — magiê và chất béo tốt
- Tỏi — allicin trong tỏi có tác dụng giãn mạch, hạ huyết áp

Thực phẩm nên kiêng:
- Muối và thực phẩm mặn: nước mắm, dưa muối, mì gói, đồ hộp, xúc xích — giảm xuống dưới 5g muối/ngày
- Thịt chế biến: thịt xông khói, lạp xưởng, thịt hộp — natri rất cao
- Thức ăn nhanh: pizza, burger, khoai tây chiên
- Rượu bia — làm tăng huyết áp và giảm tác dụng thuốc
- Cà phê, đồ uống chứa caffeine — nên hạn chế
- Thực phẩm nhiều chất béo bão hòa: da gà, mỡ lợn, đồ chiên rán

Nguyên tắc:
- Nấu ăn nhạt dần, thay muối bằng thảo mộc (gừng, tỏi, hành)
- Dùng DASH plate: 1/2 rau quả, 1/4 tinh bột nguyên hạt, 1/4 đạm nạc
- Tập thể dục đều đặn 30 phút/ngày
- Kiểm soát cân nặng — giảm 1kg cân nặng giúp giảm khoảng 1 mmHg huyết áp"""
    },
    {
        "filename": "syn_cholesterol_cao_che_do_an.json",
        "source": "Tổng hợp dinh dưỡng",
        "text": """Chế độ ăn cho người bị cholesterol cao (rối loạn mỡ máu)

Cholesterol cao làm tăng nguy cơ xơ vữa động mạch, nhồi máu cơ tim, đột quỵ. Chế độ ăn có thể giảm LDL-cholesterol ("cholesterol xấu") và tăng HDL-cholesterol ("cholesterol tốt").

Thực phẩm nên ăn:
- Yến mạch và ngũ cốc nguyên hạt — beta-glucan hòa tan làm giảm hấp thu cholesterol
- Cá béo: cá hồi, cá thu, cá ngừ — omega-3 giúp giảm triglyceride và LDL
- Đậu các loại: đậu nành, đậu xanh, đậu đen — giảm LDL hiệu quả
- Rau quả giàu chất xơ hòa tan: táo, lê, cam, bưởi, cà rốt, cà tím
- Hạt: hạnh nhân, óc chó — chất béo không bão hòa đơn và đa
- Dầu ô liu, dầu hướng dương — thay thế dầu động vật
- Bơ (avocado) — chất béo lành mạnh, giúp tăng HDL
- Tỏi — giảm LDL và ngăn oxy hóa cholesterol

Thực phẩm nên kiêng:
- Mỡ động vật: mỡ lợn, bơ động vật, da gà, da lợn
- Thịt đỏ nhiều mỡ: ba chỉ, sườn nhiều mỡ — chất béo bão hòa làm tăng LDL
- Nội tạng: gan, não, lòng đỏ trứng quá nhiều — cholesterol rất cao
- Thực phẩm chiên rán, đồ fast food — chất béo trans làm tăng LDL, giảm HDL
- Bánh ngọt công nghiệp: bánh quy, bánh ngọt đóng gói — chứa dầu hydro hóa
- Sản phẩm sữa nguyên béo: bơ, phô mai, kem tươi

Lưu ý:
- Lòng đỏ trứng: không cần kiêng hoàn toàn, tối đa 3-4 quả/tuần
- Tôm: cholesterol cao nhưng chất béo bão hòa thấp, có thể ăn vừa phải
- Ăn ít nhất 2 bữa cá/tuần
- Kết hợp vận động thể lực để tăng HDL"""
    },
    {
        "filename": "syn_beo_phi_giam_can_che_do_an.json",
        "source": "Tổng hợp dinh dưỡng",
        "text": """Chế độ ăn giảm cân, kiểm soát cân nặng cho người béo phì

Béo phì là tình trạng tích tụ mỡ thừa ảnh hưởng sức khỏe. Chế độ ăn giảm cân cần tạo ra thâm hụt năng lượng an toàn (500-750 kcal/ngày) để giảm 0.5-1 kg/tuần.

Thực phẩm nên ưu tiên:
- Protein nạc: ức gà, cá, trứng trắng, đậu phụ — no lâu, tốn nhiều năng lượng để tiêu hóa
- Rau xanh không tinh bột: cải bó xôi, bông cải, dưa leo, cà chua — ít calo, nhiều chất xơ
- Trái cây ít đường: bưởi, táo, lê, dâu tây, ổi
- Ngũ cốc nguyên hạt với lượng vừa phải: gạo lứt, yến mạch, bánh mì đen
- Sữa chua không đường — probiotic hỗ trợ tiêu hóa và kiểm soát cân nặng
- Uống đủ nước: 2-2.5 lít/ngày — nước uống trước bữa ăn giúp giảm cảm giác đói

Thực phẩm nên hạn chế:
- Thực phẩm nhiều đường: bánh kẹo, nước ngọt, kem, chè, socola
- Thực phẩm chiên rán: gà rán, khoai tây chiên, bánh rán
- Thực phẩm chế biến sẵn: xúc xích, lạp xưởng, mì gói, đồ hộp
- Cơm trắng và tinh bột tinh chế: ăn ít lại, không quá 1-1.5 chén/bữa
- Rượu bia — nhiều calo rỗng, kích thích ăn thêm
- Ăn vặt tối khuya

Chiến lược ăn uống:
- Ăn chậm, nhai kỹ — não cần 20 phút để nhận tín hiệu no
- Dùng đĩa nhỏ hơn
- Không bỏ bữa sáng — dễ ăn bù quá mức vào trưa/tối
- Ăn bữa phụ lành mạnh giữa các bữa chính: 1 quả táo, sữa chua không đường, một nắm hạt
- Nấu ăn tại nhà, kiểm soát nguyên liệu
- Ngủ đủ giấc — thiếu ngủ làm tăng hormone ghrelin gây đói"""
    },
    {
        "filename": "syn_thieu_mau_che_do_an.json",
        "source": "Tổng hợp dinh dưỡng",
        "text": """Chế độ ăn cho người bị thiếu máu do thiếu sắt

Thiếu máu thiếu sắt là loại thiếu máu phổ biến nhất, đặc biệt ở phụ nữ và trẻ em. Chế độ ăn bổ sung sắt và hỗ trợ hấp thu sắt rất quan trọng.

Thực phẩm giàu sắt nên ăn:
Sắt heme (hấp thu tốt hơn, từ động vật):
- Thịt bò, thịt lợn nạc — sắt heme dễ hấp thu nhất
- Gan gà, gan lợn — rất giàu sắt nhưng không nên ăn quá nhiều (nhiều vitamin A)
- Thịt gà, thịt vịt
- Cá và hải sản: tôm, nghêu, sò huyết — đặc biệt sò huyết rất giàu sắt
- Trứng gà

Sắt non-heme (từ thực vật):
- Đậu các loại: đậu xanh, đậu đen, đậu lăng
- Rau lá xanh đậm: rau dền, cải bó xôi, rau muống
- Hạt bí đỏ, hạt mè (vừng)
- Đậu phụ, đậu nành
- Ngũ cốc nguyên hạt, bánh mì nguyên hạt
- Mộc nhĩ (nấm mèo) — giàu sắt

Thực phẩm hỗ trợ hấp thu sắt:
- Vitamin C: cam, bưởi, ổi, ớt chuông, cà chua — ăn cùng bữa có sắt để tăng hấp thu
- Uống nước cam sau bữa ăn thay vì trà hoặc cà phê

Thực phẩm cản trở hấp thu sắt (tránh ăn cùng bữa giàu sắt):
- Trà, cà phê — tannin liên kết sắt
- Canxi cao: sữa, phô mai — uống sữa cách xa bữa ăn giàu sắt 1-2 giờ
- Thực phẩm nhiều phytate: cám gạo, hạt thô chưa ngâm

Lưu ý:
- Nấu trong nồi gang có thể tăng lượng sắt trong thức ăn
- Ngâm đậu trước khi nấu giúp giảm phytate, tăng hấp thu sắt"""
    },
    {
        "filename": "syn_loang_xuong_che_do_an.json",
        "source": "Tổng hợp dinh dưỡng",
        "text": """Chế độ ăn cho người bị loãng xương và phòng ngừa loãng xương

Loãng xương xảy ra khi xương mất dần mật độ khoáng chất, dễ gãy. Canxi và vitamin D là hai yếu tố quan trọng nhất.

Thực phẩm giàu canxi nên ăn:
- Sữa và sản phẩm từ sữa: sữa tươi, sữa chua, phô mai — nguồn canxi hấp thu tốt nhất
- Cá nhỏ ăn cả xương: cá cơm, cá mòi hộp — canxi từ xương cá
- Đậu phụ làm từ thạch cao (calcium sulfate) — canxi cao
- Rau lá xanh đậm: cải bó xôi, cải kale, bông cải xanh — canxi thực vật
- Hạt mè (vừng) — rất giàu canxi
- Hạnh nhân
- Nước khoáng giàu canxi

Thực phẩm giúp hấp thu canxi (vitamin D):
- Cá béo: cá hồi, cá thu, cá ngừ, cá mòi — vitamin D tự nhiên
- Trứng gà (lòng đỏ) — vitamin D
- Nấm phơi nắng — vitamin D từ thực vật
- Tiếp xúc ánh nắng sáng 10-15 phút/ngày (trước 9 giờ sáng)

Thực phẩm cản trở hấp thu canxi nên hạn chế:
- Muối (natri) — làm tăng thải canxi qua nước tiểu
- Cà phê, rượu bia — giảm hấp thu canxi
- Nước ngọt có gas — phosphate cản trở hấp thu canxi
- Thực phẩm quá nhiều oxalate: rau dền, củ cải — liên kết canxi thành muối không hấp thu được

Lưu ý:
- Nhu cầu canxi người trưởng thành: 1000mg/ngày, phụ nữ sau mãn kinh: 1200mg/ngày
- Không nên uống bổ sung canxi quá 500mg một lúc
- Kết hợp tập thể dục chịu tải (đi bộ, chạy bộ, tập tạ) để kích thích tạo xương"""
    },
    {
        "filename": "syn_da_day_viem_loet_che_do_an.json",
        "source": "Tổng hợp dinh dưỡng",
        "text": """Chế độ ăn cho người bị viêm loét dạ dày, đau dạ dày

Viêm loét dạ dày do H. pylori hoặc do dùng thuốc NSAIDs, căng thẳng. Chế độ ăn giúp bảo vệ niêm mạc dạ dày và giảm tiết acid.

Thực phẩm nên ăn:
- Cháo, súp — dễ tiêu, không kích thích tiết acid
- Bánh mì, cơm mềm, nui chín kỹ — tinh bột mềm dễ tiêu
- Khoai tây hấp, luộc — trung hòa acid dạ dày
- Rau xanh luộc hoặc hấp: cải thảo, bí đỏ, cà rốt
- Cá, thịt gà nạc hấp/luộc — đạm dễ tiêu
- Trứng hấp, luộc mềm
- Sữa chua — probiotic hỗ trợ tiêu diệt H. pylori và phục hồi niêm mạc
- Gừng — chống viêm, giảm buồn nôn
- Mật ong nguyên chất — kháng khuẩn, bảo vệ niêm mạc

Thực phẩm nên kiêng:
- Đồ chua, dưa muối, cà muối — tăng acid dạ dày
- Thức ăn cay: ớt, tiêu, mù tạt — kích ứng niêm mạc
- Cà phê, trà đặc, rượu bia — tăng tiết acid
- Thực phẩm chiên rán, nhiều dầu mỡ — khó tiêu, tăng áp lực dạ dày
- Socola — có methylxanthine tăng tiết acid
- Trái cây chua: chanh, cam, bưởi — acid citric kích thích dạ dày
- Ăn no quá, đặc biệt trước khi nằm

Nguyên tắc ăn uống:
- Ăn đúng giờ, không bỏ bữa — dạ dày rỗng tiết acid gây đau
- Ăn chậm, nhai kỹ
- Chia nhỏ 5-6 bữa/ngày thay vì 3 bữa lớn
- Không nằm ngay sau ăn — ngồi thẳng ít nhất 30 phút
- Giảm stress — cortisol làm tăng acid dạ dày"""
    },
    {
        "filename": "syn_tim_mach_che_do_an.json",
        "source": "Tổng hợp dinh dưỡng",
        "text": """Chế độ ăn cho người bị bệnh tim mạch, phòng ngừa đột quỵ

Bệnh tim mạch bao gồm bệnh mạch vành, suy tim, xơ vữa động mạch. Chế độ ăn lành mạnh tim mạch giúp giảm LDL, huyết áp và viêm.

Thực phẩm nên ăn:
- Cá béo 2-3 lần/tuần: cá hồi, cá thu, cá ngừ, cá mòi — omega-3 giảm triglyceride, chống đông máu
- Rau xanh đậm màu: cải bó xôi, cải kale, bông cải — folate và chất chống oxy hóa
- Trái cây: dâu tây, việt quất, lựu, cam, bưởi — flavonoid bảo vệ mạch máu
- Ngũ cốc nguyên hạt: yến mạch, gạo lứt, lúa mạch — chất xơ hòa tan giảm cholesterol
- Đậu các loại: đậu xanh, đậu đỏ, đậu nành — protein thực vật thay thịt đỏ
- Hạt: óc chó, hạnh nhân, hạt lanh — omega-3 và chất béo không bão hòa
- Dầu ô liu — chất béo không bão hòa đơn, chống viêm
- Tỏi, hành tây — giảm huyết áp và cholesterol

Thực phẩm nên kiêng:
- Chất béo bão hòa và trans: mỡ động vật, bơ thực vật, đồ chiên công nghiệp
- Thịt đỏ và thịt chế biến: hạn chế thịt bò, heo, đặc biệt thịt xông khói, xúc xích
- Muối: giảm xuống dưới 5g/ngày, tránh đồ hộp và mì gói
- Đường và tinh bột tinh chế: nước ngọt, bánh ngọt — làm tăng triglyceride
- Rượu bia — làm tăng huyết áp và gây rối loạn nhịp tim

Phong cách ăn Mediterranean được khuyến nghị nhất:
- Ưu tiên cá, đậu, rau, trái cây, dầu ô liu
- Hạn chế thịt đỏ xuống 1-2 lần/tuần
- Dùng thảo mộc thay muối khi nấu"""
    },
    {
        "filename": "syn_tao_bon_che_do_an.json",
        "source": "Tổng hợp dinh dưỡng",
        "text": """Chế độ ăn cho người bị táo bón

Táo bón là tình trạng đại tiện khó, ít hơn 3 lần/tuần, phân cứng. Nguyên nhân chính thường do thiếu chất xơ và nước.

Thực phẩm nên ăn:
Giàu chất xơ hòa tan (giữ nước, làm mềm phân):
- Yến mạch, cám yến mạch
- Táo, lê (ăn cả vỏ), ổi, mận
- Đậu các loại: đậu đen, đậu đỏ, đậu xanh
- Cà rốt, củ cải
- Hạt lanh, hạt chia

Giàu chất xơ không hòa tan (tăng khối lượng phân, kích thích ruột):
- Rau xanh: rau muống, cải bó xôi, bông cải xanh
- Ngũ cốc nguyên hạt: gạo lứt, bánh mì đen
- Khoai lang — rất tốt cho táo bón
- Các loại hạt: hạnh nhân, óc chó
- Dứa/thơm — enzyme bromelain hỗ trợ tiêu hóa

Thực phẩm có tác dụng nhuận tràng tự nhiên:
- Mận khô — sorbitol tự nhiên kích thích ruột
- Kiwi — enzyme actinidin hỗ trợ tiêu hóa
- Sữa chua — probiotic cải thiện vi khuẩn đường ruột
- Dầu ô liu — bôi trơn ruột

Uống đủ nước:
- Tối thiểu 1.5-2 lít nước/ngày
- Uống 1 ly nước ấm ngay khi thức dậy giúp kích thích nhu động ruột

Thực phẩm nên tránh:
- Thức ăn chế biến sẵn, ít chất xơ: bánh mì trắng, cơm trắng, mì gói
- Thịt đỏ nhiều — khó tiêu, ít chất xơ
- Thực phẩm nhiều chất béo bão hòa: đồ chiên rán, fast food
- Rượu bia, cà phê quá nhiều — làm mất nước

Lưu ý:
- Tăng chất xơ từ từ để tránh đầy hơi
- Tập thể dục đều đặn — kích thích nhu động ruột
- Không nhịn đi đại tiện khi có nhu cầu"""
    },
    {
        "filename": "syn_ba_bau_che_do_an.json",
        "source": "Tổng hợp dinh dưỡng",
        "text": """Chế độ ăn cho phụ nữ mang thai (bà bầu)

Trong thời kỳ mang thai, nhu cầu dinh dưỡng tăng cao để hỗ trợ sự phát triển của thai nhi. Tuy nhiên không cần "ăn cho hai người" mà cần ăn đủ chất.

Dưỡng chất quan trọng nhất:

Axit folic (folate):
- Bắp cải, cải bó xôi, rau dền, măng tây — ngăn dị tật ống thần kinh
- Đậu các loại, hạt hướng dương
- Cần bổ sung 400-600mcg/ngày, đặc biệt 3 tháng đầu

Sắt:
- Thịt bò, gan gà (hạn chế), thịt đỏ nạc — thiếu máu thai kỳ rất phổ biến
- Rau dền, đậu đen, đậu lăng
- Kết hợp vitamin C để tăng hấp thu sắt

Canxi:
- Sữa, sữa chua, phô mai ít béo — 1000mg canxi/ngày
- Đậu phụ, hạt mè, cá nhỏ ăn cả xương

DHA/Omega-3:
- Cá hồi, cá thu, cá ngừ — phát triển não và mắt thai nhi
- Hạt lanh, hạt chia — nguồn omega-3 thực vật

Thực phẩm nên tránh khi mang thai:
- Cá có hàm lượng thủy ngân cao: cá kiếm, cá mập, cá kình — tối đa 2 bữa cá/tuần
- Thực phẩm sống: sushi, gỏi, trứng sống, thịt tái — nguy cơ Listeria, Salmonella
- Phô mai mềm chưa tiệt trùng
- Gan động vật quá nhiều — thừa vitamin A gây dị tật
- Rượu bia, cà phê quá 200mg caffeine/ngày
- Thực phẩm có hàn the, phẩm màu, chất bảo quản

Tăng cân hợp lý:
- BMI bình thường: tăng 11-16 kg
- Thiếu cân: tăng 12-18 kg
- Thừa cân: tăng 7-11 kg"""
    },
    {
        "filename": "syn_tap_gym_the_thao_che_do_an.json",
        "source": "Tổng hợp dinh dưỡng",
        "text": """Chế độ ăn cho người tập gym, thể thao, tăng cơ

Người tập thể thao cần chế độ ăn đủ năng lượng, đủ protein để phục hồi và phát triển cơ bắp.

Protein — yếu tố quan trọng nhất để tăng cơ:
- Nhu cầu: 1.6-2.2g protein/kg cân nặng/ngày
- Nguồn protein chất lượng cao:
  + Ức gà, thịt gà nạc — protein cao, chất béo thấp
  + Cá: cá hồi, cá thu, cá ngừ — protein + omega-3 giảm viêm
  + Trứng gà — protein hoàn chỉnh, leucine kích thích tổng hợp cơ
  + Đậu phụ, đậu nành, tempeh — protein thực vật
  + Thịt bò nạc — creatine tự nhiên và sắt
  + Sữa chua Hy Lạp (Greek yogurt) — casein protein tiêu hóa chậm

Carbohydrate — nhiên liệu cho tập luyện:
- Trước tập (1-2 tiếng): gạo, khoai lang, yến mạch, bánh mì — nạp năng lượng
- Sau tập (trong 30-60 phút): chuối, gạo trắng + protein — phục hồi glycogen nhanh
- Ưu tiên tinh bột phức hợp: gạo lứt, yến mạch, khoai lang

Thực phẩm hỗ trợ phục hồi:
- Chuối — kali và carb nhanh bù glycogen
- Cá hồi — omega-3 giảm viêm cơ
- Sữa chua — casein giúp phục hồi qua đêm
- Trứng sau tập — leucine kích thích MPS (tổng hợp protein cơ)
- Anh đào (cherry) — giảm đau cơ sau tập

Thời điểm ăn:
- Bữa trước tập: 1.5-2 tiếng trước, carb + protein nhẹ
- Trong tập: uống nước đủ, có thể ăn chuối nếu tập dài
- Sau tập: protein + carb trong 30-60 phút (anabolic window)
- Trước ngủ: casein protein (sữa, phô mai, sữa chua) — nuôi cơ qua đêm

Cần tránh:
- Bỏ bữa sau tập — mất cơ hội phục hồi
- Ăn quá nhiều chất béo trước tập — làm chậm tiêu hóa
- Rượu bia sau tập — ức chế tổng hợp protein cơ"""
    },
    {
        "filename": "syn_an_chay_dinh_duong.json",
        "source": "Tổng hợp dinh dưỡng",
        "text": """Chế độ ăn chay đủ dinh dưỡng

Ăn chay có thể đầy đủ dinh dưỡng nếu biết phối hợp thực phẩm đúng cách. Cần chú ý đặc biệt đến protein hoàn chỉnh, vitamin B12, sắt, canxi, omega-3 và kẽm.

Nguồn protein thực vật:
- Đậu phụ, tempeh, đậu nành — protein hoàn chỉnh, giàu nhất trong thực vật
- Đậu các loại: đậu đen, đậu đỏ, đậu xanh, đậu lăng
- Quinoa — ngũ cốc protein hoàn chỉnh duy nhất
- Phối hợp: cơm + đậu = protein hoàn chỉnh (bù amino acid cho nhau)
- Hạt: hạnh nhân, hạt bí, hạt hướng dương, hạt chia

Dưỡng chất cần chú ý đặc biệt:

Vitamin B12 (chỉ có trong động vật):
- Người ăn chay thuần phải bổ sung B12 qua thực phẩm tăng cường hoặc viên uống
- Nguồn: nấm men dinh dưỡng, thực phẩm tăng cường B12

Sắt non-heme:
- Đậu, rau dền, đậu lăng, hạt bí đỏ, mộc nhĩ
- Luôn kết hợp với vitamin C để tăng hấp thu

Canxi:
- Đậu phụ (làm bằng thạch cao), hạt mè, rau cải xanh đậm, broccoli, hạnh nhân

Omega-3:
- Hạt lanh, hạt chia, óc chó — ALA (cần chuyển hóa thành EPA/DHA, hiệu quả thấp)
- Tảo biển và dầu tảo — DHA trực tiếp

Kẽm:
- Hạt bí đỏ, hạt gai dầu, đậu các loại, yến mạch

Thực đơn mẫu một ngày:
- Sáng: yến mạch + hạt chia + chuối + sữa đậu nành
- Trưa: cơm lứt + đậu phụ sốt cà chua + rau muống xào tỏi + canh rau
- Phụ: 1 nắm hạt óc chó + 1 quả táo
- Tối: cơm + tempeh kho + bông cải hấp + canh đậu đỏ"""
    },
    {
        "filename": "syn_soi_than_che_do_an.json",
        "source": "Tổng hợp dinh dưỡng",
        "text": """Chế độ ăn cho người bị sỏi thận

Chế độ ăn cho sỏi thận phụ thuộc vào loại sỏi: sỏi canxi oxalate (phổ biến nhất), sỏi urate, sỏi struvite, sỏi cystine.

Nguyên tắc chung cho mọi loại sỏi thận:
- Uống nhiều nước: 2.5-3 lít/ngày — quan trọng nhất, làm loãng nước tiểu
- Nước tiểu cần trong và có màu vàng nhạt

Với sỏi canxi oxalate (phổ biến nhất):

Thực phẩm hạn chế (nhiều oxalate):
- Rau dền, cải bó xôi, củ dền — oxalate rất cao
- Socola, ca cao
- Hạt các loại: đậu phộng, hạt mè
- Trà đậm, trà đen

Thực phẩm nên ăn:
- Canxi từ sữa và sữa chua — canxi trong ruột liên kết với oxalate, ngăn hấp thu vào máu (KHÔNG hạn chế canxi)
- Trái cây họ cam quýt: cam, chanh — citrate trong nước tiểu ngăn tạo sỏi
- Uống nước chanh — citrate tự nhiên

Hạn chế:
- Muối: natri cao làm tăng canxi niệu
- Protein động vật quá nhiều — tăng acid uric và canxi niệu

Với sỏi urate (acid uric):
- Kiêng hải sản, nội tạng, thịt đỏ — tương tự bệnh gout
- Uống nhiều nước kiềm hóa nước tiểu
- Hạn chế fructose: nước ngọt, nước ép trái cây đóng hộp"""
    },
    {
        "filename": "syn_tre_em_dinh_duong.json",
        "source": "Tổng hợp dinh dưỡng",
        "text": """Dinh dưỡng cho trẻ em và thiếu niên

Trẻ em đang phát triển cần đủ năng lượng, protein, canxi, sắt, kẽm và vitamin để tăng trưởng tốt về thể chất và trí não.

Dưỡng chất quan trọng nhất:

Canxi — phát triển xương và răng:
- Sữa và các sản phẩm từ sữa: sữa tươi, sữa chua, phô mai — dễ hấp thu nhất
- Trẻ 1-3 tuổi: 700mg/ngày; 4-8 tuổi: 1000mg; 9-18 tuổi: 1300mg/ngày
- Đậu phụ, rau cải xanh, hạt mè

Sắt — phát triển não và ngăn thiếu máu:
- Thịt bò, gan, thịt gà
- Đậu các loại, rau dền
- Kết hợp với vitamin C

Protein — tăng trưởng cơ bắp:
- Trứng gà — protein hoàn chỉnh, dễ ăn
- Cá: cá hồi, cá thu — DHA phát triển não
- Thịt gà, thịt bò nạc
- Sữa và đậu phụ

DHA — phát triển não và thị lực:
- Cá béo: cá hồi, cá thu, cá ngừ — 2 bữa/tuần
- Trứng gà tăng cường DHA
- Hạt lanh (cho trẻ ăn chay)

Thực phẩm nên hạn chế với trẻ:
- Đồ ngọt, bánh kẹo, nước ngọt — sâu răng, béo phì
- Đồ ăn nhanh, chiên rán — chất béo xấu, nhiều muối
- Mì gói — natri cao
- Nước có gas

Bữa ăn cân bằng cho trẻ:
- Sáng: sữa + ngũ cốc/bánh mì/phở + trứng
- Trưa: cơm + thịt/cá + rau xanh + canh
- Phụ chiều: sữa chua + trái cây
- Tối: cơm + đạm + rau + canh đậu

Lưu ý: Trẻ biếng ăn cần kiên nhẫn, không ép — chia nhỏ bữa, đa dạng món ăn"""
    },
]


def main():
    ROOT    = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    OUT_DIR = os.path.join(ROOT, "data", "raw", "articles")
    os.makedirs(OUT_DIR, exist_ok=True)

    for article in ARTICLES:
        filepath = os.path.join(OUT_DIR, article["filename"])
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(
                {"text": article["text"], "source": article["source"]},
                f, ensure_ascii=False, indent=2
            )
        print(f"  ✓ {article['filename']} ({len(article['text']):,} ký tự)")

    print(f"\nĐã tạo {len(ARTICLES)} bài synthetic vào {OUT_DIR}")


if __name__ == "__main__":
    main()
