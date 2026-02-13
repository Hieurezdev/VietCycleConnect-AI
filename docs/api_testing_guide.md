# API Testing Guide with Postman

This guide explains how to test the VietCycleConnect AI API using the provided Postman collection.

## Prerequisite

1.  **Start the Server**: Ensure your API server is running locally.
    ```bash
    uvicorn app.main:app --reload
    ```
    (Or your specific start command)

2.  **Install Postman**: Download and install [Postman](https://www.postman.com/downloads/).

## Importing the Collection

1.  Open Postman.
2.  Click the **Import** button in the top left.
3.  Drag and drop the file `postman/VietCycleConnect_API.postman_collection.json`.
4.  Click **Import**.

## Environment Variables

The collection uses a variable `{{base_url}}` which defaults to `http://localhost:8000`.
If your server runs on a different port, you can:
-   Edit the `base_url` variable in the Collection settings.
-   Or create a Postman Environment and set `base_url` there.

## Available Requests

### 1. Knowledge Base (Website Usage)
-   **Method**: `POST`
-   **URL**: `/api/v1/chat/`
-   **Body**:
    ```json
    {
        "message": "Làm sao để đăng ký tài khoản?",
        "use_knowledge_base": true
    }
    ```
-   **Expected Result**: A helpful guide in Vietnamese about account registration.

### 2. Knowledge Base (Legal Info)
-   **Method**: `POST`
-   **URL**: `/api/v1/chat/`
-   **Body**:
    ```json
    {
        "message": "Chính sách bảo mật của bạn là gì?",
        "use_knowledge_base": true
    }
    ```
-   **Expected Result**: Information about privacy policy.

### 3. Scrap Matching (Find Orders)
-   **Method**: `POST`
-   **URL**: `/api/v1/chat/`
-   **Body**:
    ```json
    {
        "message": "Tìm đơn hàng sắt vụn",
        "use_knowledge_base": false
    }
    ```
-   **Expected Result**: A list of matched **Order IDs**.

## cURL Commands

You can also test the API directly from your terminal using `curl`:

**1. Knowledge Base (Website Usage)**
```bash
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Làm sao để đăng ký tài khoản?",
    "use_knowledge_base": true
  }'
```

**2. Knowledge Base (Legal Info)**
```bash
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Chính sách bảo mật của bạn là gì?",
    "use_knowledge_base": true
  }'
```

**3. Scrap Matching (Find Orders)**
```bash
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tìm đơn hàng sắt vụn",
    "use_knowledge_base": false
  }'
```
