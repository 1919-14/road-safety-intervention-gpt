# API Documentation

## Overview

The Road Safety Intervention GPT provides a RESTful API built with Flask for interacting with the AI system.

**Base URL**: `http://localhost:5000`

---

## Endpoints

### 1. Health Check

**GET** `/api/health`

Check the health status of all system components.

**Request:**
```bash
curl http://localhost:5000/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "pipeline": "ready",
  "retriever": "ready",
  "generator": "ready"
}
```

**Status Codes:**
- `200 OK` - All systems operational
- `500 Internal Server Error` - One or more components failed

---

### 2. Chat Query

**POST** `/api/chat`

Send a road safety query and receive an AI-generated response.

**Request:**
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the regulations for damaged STOP signs?"}'
```

**Request Body:**
```json
{
  "message": "string (required) - User query about road safety"
}
```

**Response:**
```json
{
  "response": "string - Formatted AI response with IRC citations",
  "graph_result": "string - Raw Neo4j query results",
  "vector_result": "string - Raw vector search results",
  "query": "string - Original user query"
}
```

**Example Response:**
```json
{
  "response": "**Direct and Professional Answer:**\n\nDamaged STOP signs must be replaced...",
  "graph_result": "{'success': True, 'records': [{'i.s_no': 1, 'i.type': 'STOP Sign'}]}",
  "vector_result": "VECTOR RAG CONTEXT\n================\nRESULT 1: ...",
  "query": "What are the regulations for damaged STOP signs?"
}
```

**Status Codes:**
- `200 OK` - Query processed successfully
- `400 Bad Request` - Empty or invalid query
- `500 Internal Server Error` - Processing error

**Error Response:**
```json
{
  "error": "string - Error description"
}
```

---

### 3. Chat History (Placeholder)

**GET** `/api/chat-history`

Retrieve chat history (currently a placeholder for future implementation).

**Request:**
```bash
curl http://localhost:5000/api/chat-history
```

**Response:**
```json
{
  "history": [
    {
      "title": "Speed Limit Query",
      "date": "Today",
      "messages": []
    }
  ]
}
```

---

## Response Format

All successful chat responses follow this structured format:

### Answer Structure

```markdown
**Direct and Professional Answer:**
- Clear, context-based answer

**Reference to IRC Standards:**
- IRC:67-2022, Clause 14.4
- IRC:35-2015, Clause 5.3

**Interventions with Specifications:**
- Specific intervention 1 (with measurements)
- Specific intervention 2 (with IRC clause)

**Standard Codes and Clause Numbers:**
- IRC:67-2022, Clause 14.4
- IRC:35-2015, Clause 4.2

**Actionable Recommendations:**
- Recommendation 1
- Recommendation 2
```

---

## Error Handling

### Common Errors

**Empty Query:**
```json
{
  "error": "Empty query"
}
```

**Component Not Available:**
```json
{
  "error": "Query generator not available"
}
```

**Processing Error:**
```json
{
  "error": "I encountered an error while processing your query. Please try again."
}
```

---

## Rate Limiting

Currently, no rate limiting is implemented. For production deployment, consider:
- Rate limiting per IP address
- Token-based authentication
- Queue management for long-running queries

---

## CORS Configuration

CORS is enabled for all origins in development:
```python
CORS(app)  # Allows all origins
```

For production, restrict to specific origins:
```python
CORS(app, origins=["https://yourdomain.com"])
```

---

## Usage Examples

### Python

```python
import requests

# Health check
response = requests.get('http://localhost:5000/api/health')
print(response.json())

# Chat query
response = requests.post(
    'http://localhost:5000/api/chat',
    json={'message': 'What are height requirements for road signs?'}
)
print(response.json()['response'])
```

### JavaScript

```javascript
// Health check
fetch('http://localhost:5000/api/health')
  .then(res => res.json())
  .then(data => console.log(data));

// Chat query
fetch('http://localhost:5000/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    message: 'What are height requirements for road signs?' 
  })
})
  .then(res => res.json())
  .then(data => console.log(data.response));
```

### cURL

```bash
# Health check
curl http://localhost:5000/api/health

# Chat query
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the specifications for speed bumps?"}'
```

---

## Performance Considerations

### Response Time
- Average: 2-5 seconds
- Vector retrieval: ~0.5s
- Graph query generation: 1-3s
- Answer generation: 1-2s

### Optimization Tips
1. Pre-load embeddings at startup (already implemented)
2. Cache frequent queries
3. Use connection pooling for Neo4j
4. Consider async processing for multiple queries

---

## Security

### Current Security Measures
- Flask development server (not for production)
- No authentication (add JWT for production)
- CORS enabled (restrict in production)

### Production Recommendations
1. Use production WSGI server (Gunicorn, uWSGI)
2. Implement API authentication (JWT, OAuth)
3. Add rate limiting
4. Use HTTPS/TLS
5. Sanitize user inputs
6. Implement logging and monitoring

---

## Monitoring & Logging

### Current Logging
```python
import logging
logging.basicConfig(level=logging.INFO)
```

### Recommended Additions
- Request/response logging
- Error tracking (Sentry, Rollbar)
- Performance monitoring (Prometheus, Grafana)
- User analytics

---

## Future Enhancements

- [ ] Streaming responses for real-time updates
- [ ] Multi-language support
- [ ] Conversation history persistence
- [ ] User feedback mechanism
- [ ] Batch query processing
- [ ] WebSocket support for real-time chat
- [ ] Export responses to PDF/Word

---

## Support

For API-related issues:
1. Check logs in backend console
2. Verify all services are running (Neo4j, Ollama)
3. Test with simple queries first
4. Check GitHub Issues for known problems

**Contact**: Create an issue on GitHub for API-related questions.
