# ĐẶC TẢ PHẠM VI DỰ ÁN

## 1. Thông tin dự án

### Tên tiếng Anh

Vietnam Data & AI Job Skill Landscape 2026:
Mining Self-Collected Online Job Postings to Discover Occupational and Skill Structure

### Tên tiếng Việt

Khám phá cấu trúc nghề nghiệp và nhu cầu kỹ năng Data/AI tại Việt Nam năm 2026 từ dữ liệu tuyển dụng trực tuyến tự thu thập.

---

## 2. Bài toán nghiên cứu

Thị trường tuyển dụng hiện nay sử dụng rất nhiều chức danh khác nhau cho các vị trí liên quan đến Dữ liệu và Trí tuệ nhân tạo (Data/AI). Tuy nhiên, chức danh công việc không nhất thiết phản ánh nhất quán các kỹ năng thực tế mà nhà tuyển dụng yêu cầu.

Hai tin tuyển dụng có chức danh hoàn toàn giống nhau có thể đòi hỏi các tập kỹ năng rất khác nhau. Ngược lại, hai tin tuyển dụng mang chức danh khác nhau lại có thể yêu cầu hồ sơ kỹ năng gần như tương đồng.

Dự án sẽ tự thu thập các tin tuyển dụng Data/AI và nghiên cứu mối quan hệ giữa:

- chức danh công việc;
- kỹ năng yêu cầu;
- mức độ tương đồng giữa các vị trí việc làm;
- các cụm nghề nghiệp hình thành trực tiếp từ dữ liệu.

Dự án không định trước một số lượng nhóm nghề nghiệp cố định.

---

## 3. Mục tiêu nghiên cứu

Mục tiêu chính của dự án là xây dựng một pipeline Khoa học Dữ liệu hoàn chỉnh từ đầu đến cuối (end-to-end) áp dụng trên dữ liệu tuyển dụng thực tế do nhóm tự thu thập.

Dự án phải hoàn thành các bước sau:

1. Thu thập tin tuyển dụng từ các nguồn công khai.
2. Lọc các tin tuyển dụng thực sự liên quan đến Data/AI.
3. Làm sạch, chuẩn hóa và loại bỏ bản ghi trùng lặp.
4. Trích xuất kỹ năng từ nội dung tin tuyển dụng.
5. Đánh giá hiệu năng của bộ trích xuất kỹ năng.
6. Phân tích cấu trúc chức danh và nhu cầu kỹ năng.
7. Đo lường độ tương đồng từng cặp giữa các tin tuyển dụng.
8. Khám phá các cụm việc làm dựa trên kỹ năng bằng các thuật toán phân cụm.
9. So sánh các cụm phát hiện được với chức danh công việc thực tế.
10. Trình bày các phát hiện, hạn chế và kết luận thực nghiệm rút ra từ dữ liệu.

---

## 4. Câu hỏi nghiên cứu

### RQ1 — Cấu trúc thị trường quan sát được

Những chức danh Data/AI nào tồn tại trong dữ liệu thu thập được, và mức độ phổ biến của chúng ra sao?

Các khía cạnh trọng tâm cần khảo sát:

- số lượng tin tuyển dụng hợp lệ;
- số lượng chức danh thô (raw job titles);
- số lượng chức danh đã chuẩn hóa (normalized job titles);
- các chức danh phổ biến nhất;
- mức độ phân mảnh của chức danh trên thị trường.

### RQ2 — Nhu cầu và cấu trúc kỹ năng

Những kỹ năng kỹ thuật nào xuất hiện thường xuyên nhất, và những kỹ năng nào thường xuyên đồng xuất hiện (co-occur) cùng nhau?

### RQ3 — Mối quan hệ giữa chức danh công việc và yêu cầu kỹ năng

Chức danh công việc có phản ánh nhất quán các yêu cầu kỹ năng hay không?

Phân tích bao gồm hai chiều:

- các chức danh giống nhau nhưng yêu cầu kỹ năng phân kỳ (khác biệt);
- các chức danh khác nhau nhưng yêu cầu kỹ năng hội tụ (tương đồng).

### RQ4 — Cấu trúc nghề nghiệp hình thành từ dữ liệu

Khi không sử dụng chức danh công việc làm đặc trưng đầu vào, những cụm kỹ năng nào xuất hiện tự nhiên từ các tin tuyển dụng?

Sau khi xác định được các cụm, dự án sẽ so sánh chúng với chức danh công việc thực tế để kiểm tra xem quy ước đặt tên trên thị trường có khớp với cấu trúc kỹ năng tiềm ẩn hay không.

---

## 5. Phạm vi thị trường mục tiêu

Dự án tập trung vào các vị trí kỹ thuật có trách nhiệm cốt lõi liên quan trực tiếp đến một hoặc nhiều lĩnh vực sau:

- Data Analysis (Phân tích dữ liệu);
- Business Intelligence (Kinh doanh thông minh / BI);
- Data Engineering (Kỹ nghệ dữ liệu);
- Data Science (Khoa học dữ liệu);
- Machine Learning (Học máy);
- Artificial Intelligence (Trí tuệ nhân tạo);
- Natural Language Processing (Xử lý ngôn ngữ tự nhiên);
- Computer Vision (Thị giác máy tính);
- Generative AI / LLMs (AI tạo sinh / Mô hình ngôn ngữ lớn);
- MLOps và các vai trò kỹ thuật AI/Data liên quan.

Danh sách trên chỉ dùng để xác định ranh giới thu thập dữ liệu.

Đây không phải là một taxonomy nghề nghiệp và không được dùng để gượng ép các tin tuyển dụng vào các nhóm định sẵn.

---

## 6. Tiêu chí giữ lại tin (Inclusion Criteria)

Một tin tuyển dụng được giữ lại trong tập dữ liệu nghiên cứu khi thỏa mãn các tiêu chí sau:

- Được đăng công khai trên nguồn dữ liệu đã được nhóm phê duyệt;
- Nằm trong khung thời gian quan sát của dự án;
- Trách nhiệm công việc cốt lõi thực sự mang tính kỹ thuật và liên quan đến Data hoặc AI;
- Chứa chức danh công việc hợp lệ;
- Chứa đủ văn bản mô tả hoặc yêu cầu công việc để phục vụ trích xuất kỹ năng;
- Không phải là bản ghi trùng lặp đã được xác định.

Các vị trí thực tập sinh (Internship) hoặc mới tốt nghiệp (Fresher) vẫn được giữ lại nếu vai trò đó thực sự thuộc phạm vi kỹ thuật Data/AI.

---

## 7. Tiêu chí loại trừ tin (Exclusion Criteria)

Các tin tuyển dụng bị loại khỏi tập dữ liệu nghiên cứu nếu thỏa mãn bất kỳ điều kiện nào sau đây:

- Chứa từ khóa như “Data” hoặc “AI” nhưng nhiệm vụ cốt lõi không phải kỹ thuật Data/AI;
- Các vị trí thuần nhập liệu (Data Entry);
- Bán hàng, phát triển kinh doanh, hoặc marketing sản phẩm cho các sản phẩm AI;
- Các vai trò vận hành/hạ tầng IT chung không thực hiện nhiệm vụ Data/AI;
- Nội dung văn bản không đủ để xác định yêu cầu kỹ năng;
- Trang lỗi, liên kết hỏng, hoặc dữ liệu thu thập không đáng tin cậy;
- Bản ghi trùng lặp đã được xác định của một vị trí tuyển dụng đã có.

Các bản ghi bị loại trừ không được xóa khỏi tập dữ liệu thô; chúng phải được đánh cờ trạng thái kèm theo lý do loại trừ rõ ràng.

---

## 8. Phạm vi nguồn dữ liệu

### Lựa chọn nguồn chính thức

- Nguồn chính (Primary source): ITviec;
- Nguồn dự phòng (Backup source): TopCV.

ITviec là nguồn chính thức và được sử dụng cho đợt thu thập dữ liệu thông thường. Dữ liệu mẫu, taxonomy, kiểm tra chất lượng dữ liệu và phân tích hạ nguồn phải truy nguyên được về tập dữ liệu chính này trừ khi dự án phê duyệt rõ ràng một tập dữ liệu khác.

TopCV là nguồn dự phòng. Nguồn này chỉ được kích hoạt nếu ITviec trở nên không thể truy cập, không thể sử dụng về mặt kỹ thuật, không thể cung cấp đủ bản ghi hợp lệ, hoặc không thể đáp ứng mục tiêu thu thập. Việc chọn TopCV làm nguồn dự phòng không đồng nghĩa với việc dự án tự động kết hợp đa nguồn.

Nếu TopCV được kích hoạt, các bản ghi của nó phải thỏa mãn cùng tiêu chí giữ lại và loại trừ, tuân theo cùng lược đồ dữ liệu và quy tắc chất lượng dữ liệu, đồng thời bảo toàn các trường nguồn gốc `source` và `source_url` để các phân tích hạ nguồn có thể phân biệt dữ liệu theo nguồn.

Trước khi tiến hành thu thập dữ liệu quy mô lớn, nhóm phải kiểm tra:

- Điều khoản dịch vụ (Terms of Service);
- robots.txt;
- Yêu cầu đăng nhập / xác thực;
- Giới hạn tần suất truy cập (rate limits);
- Các hạn chế đối với việc thu thập tự động;
- Các điều khoản quản lý việc tái sử dụng và công bố dữ liệu;
- Đặc tính kỹ thuật và tính ổn định của nền tảng.

Nếu ITviec chứng minh là không khả thi theo các điều kiện trên, nhóm sẽ chuyển hướng sang TopCV.

Nếu cả hai đều không khả thi, nhóm sẽ ưu tiên khảo sát các cổng tuyển dụng công khai của doanh nghiệp thay vì cố gắng vượt qua các biện pháp phòng vệ của website.

Dự án tuân thủ nghiêm ngặt việc sử dụng tối đa hai nguồn dữ liệu.

---

## 9. Yêu cầu dữ liệu

Các trường dữ liệu của dự án được phân loại là bắt buộc hoặc tùy chọn theo [docs/data_schema.md](docs/data_schema.md), đây là tài liệu đặc tả chuẩn ở cấp độ trường.

Các trường bắt buộc phải thỏa mãn các quy tắc lưu giữ và kiểm thực được định nghĩa trong schema để tin tuyển dụng được chấp nhận vào tập dữ liệu dự án. Các trường tùy chọn có thể bị thiếu mà không tự động vô hiệu hóa toàn bộ bản ghi, tùy thuộc vào schema và các quy tắc làm sạch.

Dữ liệu thô và nguyên bản từ nguồn phải được bảo toàn theo đúng schema. Các trường chuẩn hóa và phái sinh phải được lưu trữ riêng biệt và không được ghi đè lên dữ liệu thô ban đầu.

---

## 10. Quy mô dữ liệu kỳ vọng

Mục tiêu ban đầu:

- Khoảng 1.000–2.500 tin tuyển dụng Data/AI hợp lệ, đã khử trùng lặp;
- Thời gian thu thập trong khoảng 8–10 tuần.

Các con số này đóng vai trò định hướng, không phải là ràng buộc cứng.

Chất lượng dữ liệu, khả năng truy nguyên nguồn gốc và tính kiểm toán được ưu tiên hơn quy mô thô.

---

## 11. Nguyên tắc đối với chức danh công việc

Phải lưu trữ đồng thời:

- `raw_job_title`;
- `normalized_job_title`.

Chỉ các biến thể bề mặt và định dạng mới được phép chuẩn hóa.

Không tự ý gộp các công việc có tên khác nhau vào một nhóm nghề nghiệp chung dựa trên các giả định chủ quan.

Cấu trúc nghề nghiệp sẽ được khảo sát ở hạ nguồn thông qua kỹ năng và các thuật toán phân cụm.

---

## 12. Phạm vi bắt buộc (Mandatory Scope)

Các thành phần sau đây là bắt buộc phải thực hiện:

- Đánh giá và lựa chọn nguồn dữ liệu;
- Xây dựng pipeline thu thập / crawler tự phát triển;
- Theo dõi xuất xứ và dòng dữ liệu (provenance and lineage);
- Lọc mức độ liên quan cho các tin tuyển dụng;
- Làm sạch dữ liệu;
- Chuẩn hóa dữ liệu;
- Chuẩn hóa chức danh công việc;
- Phát hiện bản ghi trùng lặp và trùng lặp gần;
- Xây dựng taxonomy kỹ năng;
- Trích xuất kỹ năng;
- Xây dựng tập kiểm thử độc lập, được gán nhãn thủ công;
- Đánh giá bằng Precision, Recall, và F1-score;
- Phân tích thị trường mô tả;
- Phân tích tần suất kỹ năng;
- Phân tích đồng xuất hiện kỹ năng;
- Phân tích độ tương đồng nội bộ chức danh (intra-title similarity);
- Phân tích độ tương đồng giữa các chức danh (inter-title similarity);
- K-Means làm thuật toán phân cụm cơ sở (baseline);
- Phân cụm thứ bậc (Hierarchical clustering) để so sánh;
- Đánh giá chất lượng và kiểm thực phân cụm;
- PCA để giảm chiều dữ liệu và trực quan hóa;
- Phân tích mức độ khớp giữa cụm và chức danh thực tế;
- Tài liệu hóa rõ ràng các hạn chế của nghiên cứu.

---

## 13. Phạm vi tùy chọn (Optional Scope)

Chỉ thực hiện sau khi tất cả các yêu cầu bắt buộc đã hoàn thành đầy đủ.

Thứ tự ưu tiên:

1. So sánh trích xuất kỹ năng bằng LLM trên cùng tập dữ liệu benchmark.
2. Sử dụng Cây quyết định nông (Shallow Decision Tree) để diễn giải các cụm phát hiện được.
3. Xây dựng giao diện / dashboard trực quan hóa tương tác.

Các tính năng tùy chọn không bao giờ được làm chậm tiến độ của các mốc bắt buộc.

---

## 14. Ngoài phạm vi dự án (Out of Scope)

Dự án KHÔNG nhằm mục đích:

- Thiết lập một taxonomy nghề nghiệp chính thức cho Việt Nam;
- Thực hiện một cuộc điều tra toàn diện, triệt để về tất cả việc làm Data/AI tại Việt Nam;
- Dự báo xu hướng thị trường lao động dài hạn;
- Xây dựng một hệ thống trích xuất kỹ năng đạt chuẩn SOTA (State-of-the-Art);
- Fine-tune các mô hình ngôn ngữ lớn (LLMs);
- Xây dựng hệ thống RAG hoặc các AI Agent tự chủ;
- Bắt buộc xây dựng mô hình dự đoán lương;
- Thu thập bừa bãi toàn bộ dữ liệu của website tuyển dụng;
- Vượt qua CAPTCHA, rào cản xác thực hoặc các biện pháp phòng vệ chống bot.

---

## 15. Nguyên tắc công bố dữ liệu

Dữ liệu thô và nguyên văn mô tả công việc chỉ được lưu trữ hoặc công bố trong phạm vi cho phép của điều khoản nền tảng nguồn.

Kho mã nguồn ưu tiên công bố:

- Mã nguồn;
- Lược đồ dữ liệu (Data schemas);
- Quy tắc làm sạch dữ liệu;
- Taxonomy kỹ năng;
- Dữ liệu phái sinh khi được phép;
- Các bảng tổng hợp thống kê;
- Biểu đồ, trực quan hóa và các phát hiện phân tích.

Mặc định không đưa toàn bộ payload HTML hoặc văn bản mô tả công việc nguyên văn lên các kho lưu trữ GitHub công khai.

---

## 16. Giới hạn nghiên cứu đã biết

Các phát hiện chỉ đại diện cho:

- Các nền tảng được chọn;
- Các tin tuyển dụng được nhóm xác định là Data/AI;
- Khung thời gian quan sát cụ thể;
- Thông tin được nhà tuyển dụng công bố công khai.

Tập dữ liệu không phải là một cuộc tổng điều tra lao động toàn quốc của Việt Nam.

Các giới hạn dự kiến bao gồm:

- Trường dữ liệu bị thiếu hoặc không đầy đủ trong một số tin tuyển dụng;
- Tin tuyển dụng được đăng lại hoặc phân phối qua nhiều kênh;
- Quy ước đặt tên chức danh không nhất quán giữa các công ty;
- Tính chủ quan trong quá trình chuẩn hóa chức danh;
- Dương tính giả (False positives) và âm tính giả (False negatives) trong trích xuất kỹ năng;
- Các chức danh hiếm / long-tail không có đủ kích thước mẫu cho phân tích tương đồng;
- Phân cụm phản ánh các mẫu dữ liệu, không phải là một taxonomy nghề nghiệp mang tính chuẩn mực;
- Khung thời gian quan sát ngắn ngăn cản việc đưa ra kết luận về xu hướng vĩ mô dài hạn;
- Dữ liệu lương bị thưa thớt và dễ bị thiên lệch chọn mẫu (selection bias).

---

## 17. Tiêu chí hoàn thành dự án cốt lõi

Dự án cốt lõi được coi là hoàn thành khi:

- Thiết lập được một tập dữ liệu tự thu thập, sạch sẽ;
- Xuất xứ và dòng dữ liệu có thể kiểm toán đầy đủ cho mọi bản ghi;
- Bộ trích xuất kỹ năng được đánh giá chính thức trên tập kiểm thử độc lập;
- RQ1, RQ2 và RQ3 được trả lời thấu đáo;
- Phân cụm được thực thi và đánh giá cho RQ4;
- Các cụm được so sánh có hệ thống với chức danh công việc;
- Mọi kết luận đều đi kèm với các cảnh báo và giới hạn phù hợp;
- Toàn bộ pipeline có thể tái lập từ đầu đến cuối, từ tiếp nhận dữ liệu thô đến kết quả phân tích.
