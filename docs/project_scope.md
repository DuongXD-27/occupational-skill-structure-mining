# PHẠM VI DỰ ÁN

## 1. Thông tin

### Tên tiếng Anh

Vietnam Data & AI Job Skill Landscape 2026:
Mining Self-Collected Online Job Postings to Discover Occupational and Skill Structure

### Tên tiếng Việt

Khám phá cấu trúc nghề nghiệp và nhu cầu kỹ năng Data/AI tại Việt Nam năm 2026 từ dữ liệu tuyển dụng trực tuyến tự thu thập.

## 2. Bài toán nghiên cứu

Các nền tảng tuyển dụng hiện sử dụng rất nhiều tên gọi khác nhau cho các vị trí liên quan đến Data và AI, chẳng hạn:

- Data Analyst
- BI Analyst
- Analytics Engineer
- Data Engineer
- Data Scientist
- Machine Learning Engineer
- AI Engineer
- NLP Engineer
- Computer Vision Engineer
- MLOps Engineer
- LLM Engineer

Tuy nhiên, tên công việc không nhất thiết phản ánh chính xác nội dung công việc. Hai tin tuyển dụng cùng mang tên Machine Learning Engineer có thể yêu cầu hai tập kỹ năng rất khác nhau:

- Vị trí A: Python + PyTorch + Computer Vision + OpenCV
- Vị trí B: Python + LLM + RAG + Vector Database + Docker

Ngược lại, hai vị trí mang tên khác nhau như AI Engineer và Machine Learning Engineer có thể yêu cầu gần như cùng một skill profile.

Vì vậy, project không áp đặt một bộ khung danh mục nghề có sẵn từ trước.
Mục tiêu là sử dụng dữ liệu tuyển dụng thực tế để nghiên cứu:

> **Thị trường Data/AI quan sát được hiện có những công việc nào, doanh nghiệp đang yêu cầu những kỹ năng gì, tên công việc phản ánh skill requirements tốt đến mức nào, và nếu bỏ qua tiêu đề công việc thì các dữ liệu về kỹ năng thực tế được yêu cầu tự gom chúng lại thành những "chân dung nghề nghiệp" nào.**

## 3. Câu hỏi nghiên cứu

### RQ1 — Cơ cấu/Thành phần của thị trường

Trong tập thị trường Data/AI quan sát được, có những job titles nào và mức độ phổ biến của chúng ra sao? Phần này trả lời các câu hỏi:

1. Đếm tổng số chức danh nguyên bản lúc mới cào về khi chưa qua chỉnh sửa.
2. Sau normalization — chuẩn hóa và gom các tên tương tự nhau về một dạng chuẩn — còn bao nhiêu title.
3. Sau khi chuẩn hóa, chức danh nào có số lượng tuyển dụng chiếm áp đảo nhất trên thị trường.
4. Đo lường xem cách các công ty đặt tên chức danh có bị tản mác, tùy tiện hay không. Nếu phân mảnh cao, nghĩa là mỗi công ty tự tạo ra một tên riêng, thiếu tính quy chuẩn chung.
5. Thống kê xem có bao nhiêu chức danh thuộc dạng "hiếm hoi" hoặc chỉ được đăng 1–2 lần, thường là do một công ty tự sáng tạo ra hoặc vị trí rất đặc thù.

Số lượng tin thu về chỉ đại diện cho mẫu dữ liệu quan sát được, không phải là toàn bộ nhu cầu tuyển dụng thực tế của thị trường lao động Việt Nam.


### RQ2 — Nhu cầu Kỹ năng và Cấu trúc Kỹ năng

Những kỹ năng kỹ thuật nào được yêu cầu nhiều nhất và những kỹ năng nào thường xuất hiện cùng nhau?

Mục tiêu của phần này bao gồm:

- Xác định các kỹ năng phổ biến nhất trong các tin tuyển dụng Data/AI.
- Đo tần suất xuất hiện của từng kỹ năng.
- Tìm các cặp hoặc nhóm kỹ năng thường xuất hiện cùng nhau.
- Phân tích cấu trúc liên kết giữa các kỹ năng.
- Phát hiện các nhóm kỹ năng có xu hướng tạo thành một skill profile chung.


### RQ3 — Độ nhất quán giữa tên chức danh và kỹ năng thực tế yêu cầu

Liệu nhìn vào tên gọi của một công việc trên tin tuyển dụng thì có thể dự đoán chắc chắn người làm vị trí đó cần những kỹ năng gì hay không, hay tồn tại hiện tượng "tên một đằng, yêu cầu một nẻo"?

**Cùng một tên gọi nhưng yêu cầu kỹ năng khác nhau**

Tìm ra những chức danh mà các công ty cùng đặt một tên, nhưng yêu cầu kỹ năng trong JD lại khác nhau đáng kể. Ví dụ, hai vị trí cùng được gọi là "Machine Learning Engineer" nhưng:

- Công ty A yêu cầu: Python + PyTorch + OpenCV + Computer Vision
- Công ty B yêu cầu: Python + LLM + RAG + Vector Database + Docker

Điều này cho thấy cùng một job title có thể chứa nhiều skill profile khác nhau. Project cần xác định những title có mức độ phân hóa kỹ năng cao nhất.

**Tên gọi khác nhau nhưng yêu cầu kỹ năng giống nhau**

Tìm ra những chức danh mang tên khác nhau nhưng danh sách kỹ năng yêu cầu gần như giống nhau. Ví dụ: AI Engineer - Data Scientist - Machine Learning Engineer có thể cùng yêu cầu: Python + SQL + Scikit-learn + Model Training.

Trong trường hợp này, tên chức danh khác nhau nhưng nội dung công việc và skill profile lại có mức độ tương đồng cao.

Việc phát hiện và đo lường sự bất nhất giữa tên nghề và kỹ năng thực tế là một trọng tâm cốt lõi của đề tài.


### RQ4 — Xây dựng cấu trúc nghề nghiệp dựa trên dữ liệu

Nếu che toàn bộ tên chức danh (job title) trên các tin tuyển dụng và chỉ cung cấp danh sách kỹ năng cho thuật toán phân tích, các tin tuyển dụng sẽ tự động được gom thành những cụm công việc nào?

Quy trình nghiên cứu dự kiến:

1. Loại bỏ hoặc không sử dụng thông tin job title trong quá trình clustering.
2. Biểu diễn mỗi job posting thông qua tập kỹ năng được trích xuất.
3. Tính mức độ tương đồng giữa các job posting dựa trên skill profile.
4. Sử dụng thuật toán clustering để tự động nhóm các job posting.
5. Phân tích đặc trưng kỹ năng của từng cluster.
6. Sau khi clustering hoàn tất mới mở lại job title thực tế.
7. So sánh job title với các cluster được hình thành từ dữ liệu kỹ năng.

Câu hỏi cuối cùng là: Nếu không nhìn vào tên chức danh, dữ liệu về kỹ năng tự chia thị trường Data/AI thành những "chân dung nghề nghiệp" nào?

Sau đó có thể đối chiếu:

- Một cluster bao gồm những job title nào?
- Các công ty gọi cùng một skill profile bằng những tên gì?
- Một job title có bị phân tán ra nhiều cluster khác nhau hay không?
- Nhiều job title khác nhau có hội tụ vào cùng một cluster hay không?


## 4. Phạm vi thị trường mục tiêu

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

Danh sách trên chỉ dùng để xác định ranh giới thu thập dữ liệu, không được dùng để gượng ép các tin tuyển dụng vào các nhóm định sẵn.

## 5. Tiêu chí giữ lại tin

Một tin tuyển dụng được giữ lại trong tập dữ liệu nghiên cứu khi thỏa mãn các tiêu chí sau:

- Được đăng công khai trên nguồn dữ liệu đã được nhóm phê duyệt;
- Nằm trong khung thời gian quan sát của dự án;
- Trách nhiệm công việc cốt lõi thực sự mang tính kỹ thuật và liên quan đến Data hoặc AI;
- Chứa chức danh công việc hợp lệ;
- Chứa đủ văn bản mô tả hoặc yêu cầu công việc để phục vụ trích xuất kỹ năng;
- Không phải là bản ghi trùng lặp đã được xác định.

Các vị trí thực tập sinh (Internship) hoặc mới tốt nghiệp (Fresher) vẫn được giữ lại nếu vai trò đó thực sự thuộc phạm vi kỹ thuật Data/AI.

## 6. Tiêu chí loại trừ tin

Các tin tuyển dụng bị loại khỏi tập dữ liệu nghiên cứu nếu thỏa mãn bất kỳ điều kiện nào sau đây:

- Chứa từ khóa như “Data” hoặc “AI” nhưng nhiệm vụ cốt lõi không phải kỹ thuật Data/AI;
- Các vị trí thuần nhập liệu (Data Entry);
- Bán hàng, phát triển kinh doanh, hoặc marketing sản phẩm cho các sản phẩm AI;
- Các vai trò vận hành/hạ tầng IT chung không thực hiện nhiệm vụ Data/AI;
- Nội dung văn bản không đủ để xác định yêu cầu kỹ năng;
- Trang lỗi, liên kết hỏng, hoặc dữ liệu thu thập không đáng tin cậy;
- Bản ghi trùng lặp đã được xác định của một vị trí tuyển dụng đã có.

Các bản ghi bị loại trừ không được xóa khỏi tập dữ liệu thô; chúng phải được đánh cờ trạng thái kèm theo lý do loại trừ rõ ràng.


## 7. Phạm vi nguồn dữ liệu

### Lựa chọn nguồn chính thức

- Nguồn chính (Primary source): ITviec;
- Nguồn dự phòng (Backup source): TopCV.

ITviec là nguồn chính thức và được sử dụng cho đợt thu thập dữ liệu thông thường. TopCV là nguồn dự phòng. Nguồn này chỉ được kích hoạt nếu ITviec trở nên không thể truy cập, không thể sử dụng về mặt kỹ thuật, không thể cung cấp đủ bản ghi hợp lệ, hoặc không thể đáp ứng mục tiêu thu thập. Việc chọn TopCV làm nguồn dự phòng không đồng nghĩa với việc dự án tự động kết hợp đa nguồn.

Nếu TopCV được kích hoạt, các bản ghi của nó phải thỏa mãn cùng tiêu chí giữ lại và loại trừ, tuân theo cùng lược đồ dữ liệu và quy tắc chất lượng dữ liệu, đồng thời bảo toàn các trường nguồn gốc `source` và `source_url` để các phân tích hạ nguồn có thể phân biệt dữ liệu theo nguồn.

Trước khi tiến hành thu thập dữ liệu quy mô lớn, nhóm phải kiểm tra:

- Điều khoản dịch vụ (Terms of Service);
- robots.txt;
- Yêu cầu đăng nhập / xác thực;
- Giới hạn tần suất truy cập (rate limits);
- Các hạn chế đối với việc thu thập tự động;
- Các điều khoản quản lý việc tái sử dụng và công bố dữ liệu;
- Đặc tính kỹ thuật và tính ổn định của nền tảng.

Nếu ITviec chứng minh là không khả thi theo các điều kiện trên, nhóm sẽ chuyển hướng sang TopCV. Nếu cả hai đều không khả thi, nhóm sẽ ưu tiên khảo sát các cổng tuyển dụng công khai của doanh nghiệp thay vì cố gắng vượt qua các biện pháp phòng vệ của website.

Dự án tuân thủ nghiêm ngặt việc sử dụng tối đa hai nguồn dữ liệu.

## 8. Yêu cầu dữ liệu

Mỗi tin tuyển dụng trong dataset sẽ gồm các trường dữ liệu được quy định trong `docs/data_schema.md`. Các trường được chia thành hai nhóm:

- Trường bắt buộc: phải có dữ liệu hợp lệ thì tin tuyển dụng mới được đưa vào dataset chính.
- Trường tùy chọn: có thể bị thiếu mà bản ghi vẫn được giữ lại.

Ví dụ, các trường như tiêu đề công việc, nội dung mô tả hoặc nguồn tin có thể được quy định là bắt buộc, trong khi tên công ty hoặc kinh nghiệm thô có thể là tùy chọn. Lương và học vấn không có trường riêng trong schema vì không phục vụ RQ1–RQ4.

Dữ liệu thu thập trực tiếp từ website phải được giữ nguyên để có thể kiểm tra lại nguồn sau này. Mọi dữ liệu đã qua xử lý, ví dụ tiêu đề đã chuẩn hóa, kỹ năng đã trích xuất hoặc các biến được tính toán thêm, phải được lưu ở các trường riêng và không được ghi đè lên dữ liệu gốc, đảm bảo dữ liệu có thể kiểm tra, tái lập và đối chiếu lại trong quá trình nghiên cứu.

## 9. Quy mô dữ liệu kỳ vọng

Mục tiêu ban đầu: Khoảng 1.000–2.500 tin tuyển dụng Data/AI hợp lệ, đã khử trùng lặp. Các con số này đóng vai trò định hướng, không phải là ràng buộc cứng. Chất lượng dữ liệu, khả năng truy nguyên nguồn gốc và tính kiểm toán được ưu tiên hơn quy mô thô.


## 10. Nguyên tắc đối với chức danh công việc

Khi thu thập tin tuyển dụng, phải giữ nguyên tên chức danh gốc mà website đăng, ví dụ Senior Data Analyst, DATA ANALYST, Data Analyst - Power BI. Sau đó mới tạo thêm một trường khác là normalized_job_title để chuẩn hóa cách viết. Việc chuẩn hóa chỉ nhằm xử lý khác biệt về viết hoa, seniority hoặc các biến thể hình thức đã thống nhất, chứ không được tự suy diễn rằng hai chức danh khác nhau thực chất là cùng một nghề.

Ví dụ theo quy ước nhóm đã chốt, Senior Data Analyst, Data Analyst và DATA ANALYST đều được chuẩn hóa thành Data Analyst. Nhưng nếu gặp Analytics Engineer và Data Analyst, thì không được tự gộp cả hai thành Data Analyst chỉ vì cảm thấy công việc có vẻ giống nhau. Việc hai chức danh khác nhau có thực sự thuộc cùng một nhóm nghề hay không sẽ để cho phần phân tích kỹ năng và clustering quyết định dựa trên dữ liệu.

Crawler chỉ có nhiệm vụ lấy đúng tên chức danh từ nguồn và lưu nguyên trạng. Nó không được tự sửa title hay ghép thêm công nghệ vào tên. Ví dụ website ghi AI Engineer, còn JD có LLM, RAG, LangChain, thì crawler vẫn phải lưu AI Engineer, không được biến thành AI Engineer - LLM/RAG. Nếu title có các phần phụ như công nghệ hoặc seniority cần xử lý thì cleaner sẽ làm ở bước sau.

## 11. Phạm vi bắt buộc (Mandatory Scope)

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

## 12. Phạm vi tùy chọn (Optional Scope)

Chỉ thực hiện sau khi tất cả các yêu cầu bắt buộc đã hoàn thành đầy đủ.

Phần ưu tiên đầu tiên là so sánh rule-based với LLM trong việc trích xuất kỹ năng. Ví dụ cùng 100 JD đã được gán nhãn thủ công, cho cả hệ thống Dictionary + Regex + Fuzzy và LLM đọc, rồi so sánh Precision, Recall, F1. Đây chính là phần LLM skill-extraction comparator.

Phần thứ hai là Shallow Decision Tree. Sau khi RQ4 clustering tạo ra các cụm nghề chỉ dựa trên skill, Decision Tree được dùng để giúp con người hiểu vì sao một job lại rơi vào cụm đó. Ví dụ thuật toán clustering tìm ra một cụm có nhiều job liên quan đến Data Engineering; cây có thể cho thấy rằng các job có Spark, Airflow và ETL thường đi vào cụm này. Gọi là shallow vì cây được cố tình giữ ít tầng để dễ đọc và giải thích, chứ không nhằm xây một mô hình dự đoán phức tạp.

Phần thứ ba là dashboard tương tác, tức biến các kết quả đã có thành giao diện để người xem có thể xem top skill, job title, mạng lưới skill đồng xuất hiện, các cluster nghề nghiệp... Đây chủ yếu là phần trình bày kết quả, không tạo ra kết luận nghiên cứu cốt lõi mới.

## 13. Ngoài phạm vi dự án (Out of Scope)

Dự án KHÔNG nhằm mục đích:

- Thiết lập một taxonomy nghề nghiệp chính thức cho Việt Nam;
- Thực hiện một cuộc điều tra toàn diện, triệt để về tất cả việc làm Data/AI tại Việt Nam;
- Dự báo xu hướng thị trường lao động dài hạn;
- Xây dựng một hệ thống trích xuất kỹ năng đạt chuẩn SOTA (State-of-the-Art);
- Fine-tune các mô hình ngôn ngữ lớn (LLMs);
- Xây dựng hệ thống RAG hoặc các AI Agent tự chủ;
- Thu thập riêng hoặc phân tích lương/học vấn, xây dựng mô hình dự đoán lương;
- Thu thập bừa bãi toàn bộ dữ liệu của website tuyển dụng;
- Vượt qua CAPTCHA, rào cản xác thực hoặc các biện pháp phòng vệ chống bot.
