# 🚀 Flask Applications Portfolio

[![Flask](https://img.shields.io/badge/Flask-2.3%2B-green)](https://flask.palletsprojects.com/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED)](https://www.docker.com/)
[![Architecture](https://img.shields.io/badge/Architecture-Production--Ready-red)]()

A professional collection of production-ready Flask applications demonstrating modern web development patterns, scalable architecture, and enterprise-grade design principles.

## 🏗️ Architecture Philosophy

This portfolio showcases **modular, scalable Flask applications** built with:
- **Microservices Architecture**: Independently deployable Flask services
- **Domain-Driven Design**: Clear separation of concerns
- **Event-Driven Patterns**: Asynchronous processing with message queues
- **API-First Development**: RESTful and WebSocket APIs
- **Container-First Design**: Docker and Kubernetes readiness

## 📦 Application Showcase

### 🎭 Avatar AI System (`flask-apps/avatar/`)
**Production-Grade AI Assistant Platform**

```python
# Core Architecture Pattern
from flask import Flask
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from celery import Celery

# Application Factory with Blueprints
def create_app(config_name='production'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize Extensions
    db.init_app(app)
    socketio.init_app(app)
    celery.conf.update(app.config)
    
    # Register Blueprints
    from .api.v1 import api_v1_bp
    from .websocket import ws_bp
    from .admin import admin_bp
    
    app.register_blueprint(api_v1_bp, url_prefix='/api/v1')
    app.register_blueprint(ws_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    return app
```

**Key Design Patterns:**
- **Factory Pattern**: Configurable application creation
- **Blueprint Architecture**: Modular route organization
- **Dependency Injection**: Service layer abstraction
- **Observer Pattern**: Event-driven component communication
- **Strategy Pattern**: Pluggable AI provider implementations

### 🎤 Real-time Transcription Service (`flask-apps/whisperer/`)
**WebSocket-Based Audio Processing**

```python
# WebSocket Architecture for Real-time Audio
@socketio.on('audio_stream')
def handle_audio_stream(data):
    """Real-time audio processing pipeline"""
    # 1. Audio chunk reception via WebSocket
    audio_chunk = AudioChunk(data['audio'], data['session_id'])
    
    # 2. Queue for async processing
    process_audio.delay(audio_chunk)
    
    # 3. Real-time transcription via WebSocket
    emit('transcription_update', {
        'status': 'processing',
        'chunk_id': audio_chunk.id
    })

# Celery Task for Background Processing
@celery.task
def process_audio(audio_chunk):
    """Background audio processing"""
    transcription = whisper.transcribe(audio_chunk.data)
    
    # Publish to WebSocket room
    socketio.emit('transcription_result', {
        'text': transcription,
        'chunk_id': audio_chunk.id
    }, room=audio_chunk.session_id)
```

## 🏛️ Core Architecture Components

### 1. **Application Factory Pattern**
```python
# config.py - Environment-based configuration
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Celery configuration
    CELERY_BROKER_URL = os.environ.get('REDIS_URL')
    CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL')
    
    # Flask-SocketIO
    SOCKETIO_MESSAGE_QUEUE = os.environ.get('REDIS_URL')

class DevelopmentConfig(Config):
    DEBUG = True
    EXPLAIN_TEMPLATE_LOADING = True

class ProductionConfig(Config):
    DEBUG = False
    PREFERRED_URL_SCHEME = 'https'
```

### 2. **Service Layer Architecture**
```python
# services/ai_service.py - Abstraction layer for AI providers
class AIService:
    def __init__(self, provider='openai'):
        self.provider = self._initialize_provider(provider)
    
    def _initialize_provider(self, provider_name):
        """Strategy Pattern for multiple AI providers"""
        providers = {
            'openai': OpenAIProvider(),
            'anthropic': AnthropicProvider(),
            'local': LocalLLMProvider(),
            'azure': AzureOpenAIProvider()
        }
        return providers.get(provider_name, providers['openai'])
    
    def generate_response(self, prompt, context=None):
        """Unified interface for AI generation"""
        return self.provider.generate(prompt, context)
    
    def stream_response(self, prompt, callback):
        """Streaming response handling"""
        return self.provider.stream(prompt, callback)

# Dependency Injection in Flask routes
@app.route('/api/chat', methods=['POST'])
def chat_endpoint():
    ai_service = current_app.config['AI_SERVICE']
    response = ai_service.generate_response(request.json['message'])
    return jsonify({'response': response})
```

### 3. **Database Abstraction Layer**
```python
# models/base.py - SQLAlchemy with repository pattern
class BaseRepository:
    def __init__(self, model):
        self.model = model
    
    def get(self, id):
        return self.model.query.get(id)
    
    def create(self, **kwargs):
        instance = self.model(**kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance
    
    def update(self, instance, **kwargs):
        for key, value in kwargs.items():
            setattr(instance, key, value)
        db.session.commit()
        return instance

# models/conversation.py - Domain model
class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), unique=True)
    messages = db.relationship('Message', backref='conversation', lazy='dynamic')
    
    @property
    def recent_messages(self, limit=10):
        return self.messages.order_by(Message.timestamp.desc()).limit(limit).all()
```

## 📁 Project Structure Patterns

### **Enterprise Flask Application Structure**
```
flask-apps/avatar/
├── app/                          # Application package
│   ├── __init__.py              # Application factory
│   ├── config.py                # Configuration classes
│   │
│   ├── api/                     # API layer (REST/WebSocket)
│   │   ├── __init__.py
│   │   ├── v1/                  # API versioning
│   │   │   ├── __init__.py
│   │   │   ├── conversation.py  # Conversation endpoints
│   │   │   ├── voice.py         # Voice endpoints
│   │   │   └── admin.py         # Admin endpoints
│   │   └── websocket.py         # WebSocket handlers
│   │
│   ├── models/                  # Database models
│   │   ├── __init__.py
│   │   ├── conversation.py
│   │   ├── message.py
│   │   └── user.py
│   │
│   ├── services/                # Business logic layer
│   │   ├── __init__.py
│   │   ├── ai_service.py        # AI provider abstraction
│   │   ├── voice_service.py     # Voice processing
│   │   └── storage_service.py   # File storage
│   │
│   ├── tasks/                   # Celery background tasks
│   │   ├── __init__.py
│   │   ├── audio_tasks.py
│   │   └── ai_tasks.py
│   │
│   ├── utils/                   # Utilities and helpers
│   │   ├── __init__.py
│   │   ├── validators.py
│   │   ├── decorators.py
│   │   └── helpers.py
│   │
│   └── extensions.py            # Flask extensions initialization
│
├── migrations/                  # Database migrations (Alembic)
├── tests/                       # Comprehensive test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── static/                      # Static assets
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/                   # Jinja2 templates
│   ├── base.html
│   ├── dashboard.html
│   └── admin/
│
├── requirements/                # Dependency management
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
│
├── Dockerfile                   # Multi-stage Docker build
├── docker-compose.yml           # Service orchestration
├── .env.example                 # Environment template
├── .flake8                      # Code style
├── pytest.ini                   # Test configuration
└── README.md                    # Application-specific docs
```

## 🔧 Technical Implementation Patterns

### **Dependency Management with Poetry**
```toml
# pyproject.toml - Modern dependency management
[tool.poetry]
name = "avatar-ai-system"
version = "1.0.0"
description = "Production AI Assistant Platform"

[tool.poetry.dependencies]
python = "^3.9"
flask = "^2.3.0"
flask-sqlalchemy = "^3.0.5"
flask-socketio = "^5.3.0"
celery = "^5.3.0"
openai = "^0.28.0"
redis = "^5.0.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
black = "^23.0.0"
flake8 = "^6.0.0"
pytest-cov = "^4.1.0"
```

### **Asynchronous Task Processing**
```python
# tasks/audio_tasks.py - Celery task orchestration
@celery.task(bind=True, max_retries=3)
def process_audio_task(self, audio_data, session_id):
    """Background audio processing with retry logic"""
    try:
        # 1. Audio preprocessing
        processed_audio = audio_preprocessor(audio_data)
        
        # 2. Transcription
        transcription = whisper_client.transcribe(processed_audio)
        
        # 3. AI response generation
        response = ai_service.generate_response(transcription)
        
        # 4. Update WebSocket clients
        socketio.emit('response_ready', {
            'transcription': transcription,
            'response': response,
            'session_id': session_id
        })
        
        return {'status': 'success', 'session_id': session_id}
        
    except Exception as exc:
        self.retry(exc=exc, countdown=2 ** self.request.retries)
```

### **WebSocket Integration Pattern**
```python
# api/websocket.py - Real-time communication
@socketio.on('connect')
def handle_connect():
    """Client connection handler"""
    session_id = generate_session_id()
    join_room(session_id)
    
    emit('session_created', {
        'session_id': session_id,
        'status': 'connected'
    })

@socketio.on('audio_chunk')
def handle_audio_chunk(data):
    """Process incoming audio chunks"""
    # Validate and process chunk
    chunk_validator.validate(data)
    
    # Queue for background processing
    process_audio_task.delay(
        audio_data=data['audio'],
        session_id=data['session_id']
    )
    
    # Immediate acknowledgement
    emit('chunk_received', {
        'chunk_id': data['chunk_id'],
        'status': 'processing'
    })
```

## 🚀 Deployment Architecture

### **Multi-Stage Docker Build**
```dockerfile
# Dockerfile
# Stage 1: Builder
FROM python:3.9-slim as builder
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && \
    poetry export -f requirements.txt --output requirements.txt --without-hashes

# Stage 2: Runtime
FROM python:3.9-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run as non-root user
RUN useradd -m -u 1000 appuser
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:create_app()"]
```

### **Kubernetes Deployment**
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: avatar-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: avatar-api
  template:
    metadata:
      labels:
        app: avatar-api
    spec:
      containers:
      - name: flask-app
        image: avatar-ai:latest
        ports:
        - containerPort: 5000
        envFrom:
        - configMapRef:
            name: avatar-config
        - secretRef:
            name: avatar-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
---
# Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: avatar-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: avatar-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## 🧪 Testing Strategy

### **Comprehensive Test Suite**
```python
# tests/integration/test_api_v1.py
class TestConversationAPI:
    def test_create_conversation(self, client, auth_headers):
        """Test conversation creation endpoint"""
        response = client.post(
            '/api/v1/conversations',
            json={'title': 'Test Conversation'},
            headers=auth_headers
        )
        
        assert response.status_code == 201
        assert 'id' in response.json
        assert response.json['title'] == 'Test Conversation'
    
    def test_streaming_response(self, client, auth_headers):
        """Test streaming AI responses"""
        with client.stream(
            'POST',
            '/api/v1/chat/stream',
            json={'message': 'Hello'},
            headers=auth_headers
        ) as response:
            chunks = []
            for line in response.iter_lines():
                if line:
                    chunks.append(json.loads(line))
            
            assert len(chunks) > 0
            assert all('chunk' in chunk for chunk in chunks)

# tests/unit/test_ai_service.py
def test_ai_service_strategy_pattern():
    """Test strategy pattern for AI providers"""
    service = AIService(provider='openai')
    assert isinstance(service.provider, OpenAIProvider)
    
    service = AIService(provider='anthropic')
    assert isinstance(service.provider, AnthropicProvider)
    
    # Default fallback
    service = AIService(provider='unknown')
    assert isinstance(service.provider, OpenAIProvider)
```

## 📚 Design Patterns Demonstrated

### **1. Factory Pattern**
- Application factory for different environments
- Service factories for dependency injection

### **2. Strategy Pattern**
- Pluggable AI providers
- Configurable storage backends
- Multiple authentication methods

### **3. Observer Pattern**
- Event-driven architecture with WebSockets
- Real-time notifications
- Pub/Sub message distribution

### **4. Repository Pattern**
- Abstract database operations
- Clean separation of data access
- Testable data layer

### **5. Decorator Pattern**
- Authentication decorators
- Rate limiting
- Request validation

## 🔄 CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: Flask CI/CD Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis
        ports:
          - 6379:6379
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install poetry
        poetry install
    
    - name: Run tests
      run: |
        poetry run pytest tests/ --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
    
  docker:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: ./flask-apps/avatar
        push: true
        tags: |
          ${{ secrets.DOCKER_USERNAME }}/avatar-ai:latest
          ${{ secrets.DOCKER_USERNAME }}/avatar-ai:${{ github.sha }}
```

## 🎯 Learning Outcomes

This portfolio demonstrates proficiency in:

1. **Production Flask Development**
   - Application factory patterns
   - Blueprint architecture
   - Extension management

2. **Scalable Architecture**
   - Microservices design
   - Database abstraction layers
   - Caching strategies

3. **Real-time Systems**
   - WebSocket integration
   - Event-driven programming
   - Background task processing

4. **DevOps Practices**
   - Containerization with Docker
   - Kubernetes deployment
   - CI/CD pipeline design

5. **Testing & Quality**
   - Comprehensive test suites
   - Code coverage requirements
   - Integration testing