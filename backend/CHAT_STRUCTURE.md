# Chat Structure Documentation

## Tổng quan

Hệ thống chat đã được thiết kế lại với cấu trúc 3 tầng:
- **Conversation**: Cuộc hội thoại chính
- **Dialog**: Các cuộc trò chuyện con trong conversation
- **Message**: Các tin nhắn trong dialog

## Cấu trúc Database

### Bảng `conversations`
- `id`: Primary key
- `user_id`: Foreign key đến users
- `topic`: Chủ đề của conversation
- `started_at`: Thời gian bắt đầu

### Bảng `dialogs`
- `id`: Primary key
- `conversation_id`: Foreign key đến conversations
- `name`: Tên của dialog
- `created_at`: Thời gian tạo

### Bảng `messages`
- `id`: Primary key
- `dialog_id`: Foreign key đến dialogs
- `sender`: 'user' hoặc 'bot'
- `message`: Nội dung tin nhắn
- `timestamp`: Thời gian gửi

## API Endpoints

### Conversation APIs
- `GET /api/chat/conversations` - Lấy danh sách conversations
- `POST /api/chat/conversations` - Tạo conversation mới
- `GET /api/chat/conversations/{id}` - Lấy thông tin conversation
- `DELETE /api/chat/conversations/{id}` - Xóa conversation

### Dialog APIs
- `GET /api/chat/conversations/{id}/dialogs` - Lấy danh sách dialogs
- `POST /api/chat/conversations/{id}/dialogs` - Tạo dialog mới
- `GET /api/chat/dialogs/{id}` - Lấy thông tin dialog
- `DELETE /api/chat/dialogs/{id}` - Xóa dialog

### Message APIs
- `GET /api/chat/dialogs/{id}/messages` - Lấy lịch sử messages
- `POST /api/chat/dialogs/{id}/messages` - Gửi message

### Dialog Chat APIs (với Knowledge Base)
- `POST /api/dialog/{id}/chat` - Chat với knowledge base
- `GET /api/dialog/{id}/messages` - Lấy messages của dialog
- `POST /api/dialog/{id}/search` - Tìm kiếm trong knowledge base

## Knowledge Base Integration

Mỗi dialog sẽ sử dụng **toàn bộ knowledge base** của user thay vì chỉ một file cụ thể. Điều này cho phép:

1. **Tìm kiếm toàn diện**: Bot có thể tìm kiếm trong tất cả các file đã upload
2. **Context phong phú**: Phản hồi dựa trên nhiều nguồn thông tin
3. **Quản lý đơn giản**: Không cần chọn file cụ thể cho mỗi dialog

## Workflow

1. User tạo conversation với topic
2. Trong conversation, user tạo các dialog khác nhau
3. Mỗi dialog có thể chat với toàn bộ knowledge base
4. Messages được lưu theo dialog để dễ quản lý

## Ví dụ sử dụng

```bash
# 1. Tạo conversation
POST /api/chat/conversations
{
  "topic": "Hỏi đáp y tế"
}

# 2. Tạo dialog trong conversation
POST /api/chat/conversations/1/dialogs
{
  "name": "Hỏi về bệnh tiểu đường"
}

# 3. Chat với knowledge base
POST /api/dialog/1/chat
{
  "message": "Triệu chứng của bệnh tiểu đường là gì?"
}
```

## Thay đổi từ phiên bản cũ

- ❌ Loại bỏ chat riêng cho từng file KB
- ✅ Mỗi dialog sử dụng toàn bộ KB
- ✅ Cấu trúc conversation > dialog > message
- ✅ API endpoints rõ ràng và có tổ chức 