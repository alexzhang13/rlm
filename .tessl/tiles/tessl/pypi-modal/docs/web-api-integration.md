# Web & API Integration

Modal provides comprehensive web application serving capabilities, enabling deployment of web servers, REST APIs, and integration with popular web frameworks. These decorators transform Modal functions into web endpoints that can handle HTTP requests and serve web applications.

## Capabilities

### ASGI Application Support

Decorator for serving ASGI-compatible applications like FastAPI, Starlette, and modern async web frameworks.

```python { .api }
def asgi_app(func: Callable) -> Callable:
    """Decorator to serve ASGI applications (FastAPI, Starlette, etc.)"""
```

#### Usage Examples

```python
import modal
from fastapi import FastAPI

app = modal.App("fastapi-server")
web_app = FastAPI()

@web_app.get("/")
def read_root():
    return {"message": "Hello from Modal FastAPI!"}

@web_app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

@web_app.post("/process")
def process_data(data: dict):
    # Expensive processing that benefits from Modal's scaling
    result = expensive_computation(data)
    return {"result": result}

@app.function()
@modal.asgi_app()
def fastapi_app():
    return web_app

# The FastAPI app is now served on Modal's infrastructure
```

### WSGI Application Support

Decorator for serving WSGI-compatible applications like Flask, Django, and traditional web frameworks.

```python { .api }
def wsgi_app(func: Callable) -> Callable:
    """Decorator to serve WSGI applications (Flask, Django, etc.)"""
```

#### Usage Examples

```python
import modal
from flask import Flask, request, jsonify

app = modal.App("flask-server")
web_app = Flask(__name__)

@web_app.route("/")
def hello():
    return jsonify({"message": "Hello from Modal Flask!"})

@web_app.route("/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    # Process file with Modal's compute resources
    result = process_uploaded_file(file)
    return jsonify({"processed": result})

@web_app.route("/predict", methods=["POST"])
def make_prediction():
    data = request.get_json()
    # Use Modal for ML inference
    prediction = run_ml_model(data)
    return jsonify({"prediction": prediction})

@app.function()
@modal.wsgi_app()
def flask_app():
    return web_app

# The Flask app is now served on Modal's infrastructure
```

### Web Endpoint

Decorator for creating simple HTTP endpoints without requiring a full web framework.

```python { .api }
def web_endpoint(func: Callable) -> Callable:
    """Decorator to create HTTP web endpoints"""
```

#### Usage Examples

```python
import modal
import json

app = modal.App("simple-api")

@app.function()
@modal.web_endpoint(method="GET")
def get_status():
    """Simple GET endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0"
    }

@app.function()
@modal.web_endpoint(method="POST")
def process_webhook(data=None):
    """Handle webhook POST requests"""
    if data:
        # Process webhook data
        result = handle_webhook_data(data)
        return {"success": True, "processed": result}
    else:
        return {"error": "No data provided"}, 400

@app.function()
@modal.web_endpoint(method="GET", path="/metrics")
def get_metrics():
    """Custom metrics endpoint"""
    metrics = collect_application_metrics()
    return {"metrics": metrics}

# Endpoints are available at:
# GET  https://your-app.modal.run/get_status
# POST https://your-app.modal.run/process_webhook
# GET  https://your-app.modal.run/metrics
```

### FastAPI Endpoint

Specialized decorator optimized for FastAPI applications with enhanced integration features.

```python { .api }
def fastapi_endpoint(func: Callable) -> Callable:
    """Decorator specifically for FastAPI endpoints with enhanced features"""
```

#### Usage Examples

```python
import modal
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

app = modal.App("advanced-fastapi")

class PredictionRequest(BaseModel):
    text: str
    model: str = "default"

class PredictionResponse(BaseModel):
    prediction: str
    confidence: float
    model_used: str

@app.function()
@modal.fastapi_endpoint()
def ml_prediction_api():
    """Advanced FastAPI endpoint with automatic docs and validation"""
    fastapi_app = FastAPI(
        title="ML Prediction API",
        description="Machine learning predictions powered by Modal",
        version="1.0.0"
    )
    
    @fastapi_app.post("/predict", response_model=PredictionResponse)
    async def predict(request: PredictionRequest):
        try:
            # Load model and make prediction
            model = load_ml_model(request.model)
            prediction, confidence = model.predict(request.text)
            
            return PredictionResponse(
                prediction=prediction,
                confidence=confidence,
                model_used=request.model
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @fastapi_app.get("/models")
    async def list_models():
        """List available models"""
        models = get_available_models()
        return {"models": models}
    
    return fastapi_app

# Automatic OpenAPI docs available at:
# https://your-app.modal.run/docs
# https://your-app.modal.run/redoc
```

### Web Server

Decorator for creating custom web servers with full control over the HTTP handling.

```python { .api }
def web_server(func: Callable) -> Callable:
    """Decorator to create custom web servers"""
```

#### Usage Examples

```python
import modal
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

app = modal.App("custom-server")

class CustomHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"status": "healthy", "server": "custom"}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == "/process":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                result = custom_processing(data)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"result": result}).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()

@app.function()
@modal.web_server()
def custom_web_server():
    """Custom HTTP server with full control"""
    server = HTTPServer(("0.0.0.0", 8000), CustomHandler)
    server.serve_forever()
```

## Advanced Web Patterns

### Multi-Framework API Gateway

```python
import modal
from fastapi import FastAPI
from flask import Flask
import asyncio

app = modal.App("api-gateway")

# FastAPI for async endpoints
fastapi_app = FastAPI()

@fastapi_app.get("/async-data")
async def get_async_data():
    # Async data processing
    data = await fetch_external_data()
    return {"data": data, "type": "async"}

# Flask for sync endpoints
flask_app = Flask(__name__)

@flask_app.route("/sync-data")
def get_sync_data():
    # Synchronous data processing
    data = fetch_local_data()
    return {"data": data, "type": "sync"}

@app.function()
@modal.asgi_app()
def async_api():
    return fastapi_app

@app.function()
@modal.wsgi_app()
def sync_api():
    return flask_app

# Different apps serve different endpoints
# https://your-app-async.modal.run/async-data
# https://your-app-sync.modal.run/sync-data
```

### Microservices Architecture

```python
import modal
from fastapi import FastAPI

app = modal.App("microservices")

# User service
user_app = FastAPI(title="User Service")

@user_app.get("/users/{user_id}")
def get_user(user_id: int):
    return get_user_from_database(user_id)

@user_app.post("/users")
def create_user(user_data: dict):
    return create_user_in_database(user_data)

# Order service
order_app = FastAPI(title="Order Service")

@order_app.get("/orders/{order_id}")
def get_order(order_id: int):
    return get_order_from_database(order_id)

@order_app.post("/orders")
def create_order(order_data: dict):
    # Validate user exists
    user_id = order_data.get("user_id")
    user = get_user_from_database(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return create_order_in_database(order_data)

# Deploy as separate services
@app.function()
@modal.asgi_app()
def user_service():
    return user_app

@app.function()
@modal.asgi_app()
def order_service():
    return order_app
```

### WebSocket and Real-time Features

```python
import modal
from fastapi import FastAPI, WebSocket
from typing import List

app = modal.App("realtime-app")
web_app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@web_app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Process message and broadcast to all connections
            processed = process_realtime_data(data)
            await manager.broadcast(f"Processed: {processed}")
    except Exception:
        manager.disconnect(websocket)

@web_app.post("/broadcast")
def broadcast_message(message: dict):
    """HTTP endpoint to broadcast messages"""
    asyncio.create_task(manager.broadcast(json.dumps(message)))
    return {"status": "broadcasted"}

@app.function()
@modal.asgi_app()
def realtime_app():
    return web_app
```

### File Upload and Processing API

```python
import modal
from fastapi import FastAPI, File, UploadFile, HTTPException
from typing import List
import tempfile
import os

app = modal.App("file-processor")
web_app = FastAPI(title="File Processing API")

@web_app.post("/upload/single")
async def upload_single_file(file: UploadFile = File(...)):
    """Upload and process a single file"""
    if not file.filename.endswith(('.jpg', '.png', '.pdf', '.txt')):
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    # Save file temporarily
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name
    
    try:
        # Process file with Modal compute
        if file.filename.endswith(('.jpg', '.png')):
            result = process_image(tmp_path)
        elif file.filename.endswith('.pdf'):
            result = extract_pdf_text(tmp_path)
        else:
            result = process_text_file(tmp_path)
        
        return {
            "filename": file.filename,
            "size": len(content),
            "processed": result
        }
    finally:
        os.unlink(tmp_path)

@web_app.post("/upload/batch")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    """Upload and process multiple files"""
    results = []
    
    for file in files:
        try:
            # Process each file
            content = await file.read()
            result = await process_file_async(file.filename, content)
            results.append({
                "filename": file.filename,
                "status": "success",
                "result": result
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "error": str(e)
            })
    
    return {"processed_files": results}

@web_app.get("/download/{file_id}")
async def download_processed_file(file_id: str):
    """Download processed file results"""
    file_path = get_processed_file_path(file_id)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path)

@app.function()
@modal.asgi_app()
def file_processing_api():
    return web_app
```

### Authentication and Middleware Integration

```python
import modal
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import jwt

app = modal.App("secure-api")
web_app = FastAPI(title="Secure API with Authentication")

# Add CORS middleware
web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    try:
        payload = jwt.decode(
            credentials.credentials, 
            os.environ["JWT_SECRET"], 
            algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

@web_app.post("/login")
def login(credentials: dict):
    """Authenticate user and return JWT token"""
    if authenticate_user(credentials["username"], credentials["password"]):
        token = create_jwt_token(credentials["username"])
        return {"access_token": token, "token_type": "bearer"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

@web_app.get("/protected")
def protected_endpoint(current_user: dict = Depends(verify_token)):
    """Protected endpoint requiring authentication"""
    return {
        "message": f"Hello {current_user['username']}!",
        "data": get_user_specific_data(current_user['user_id'])
    }

@web_app.get("/admin")
def admin_endpoint(current_user: dict = Depends(verify_token)):
    """Admin-only endpoint"""
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return {"admin_data": get_admin_data()}

@app.function(secrets=[modal.Secret.from_name("jwt-secret")])
@modal.asgi_app()
def secure_api():
    return web_app
```