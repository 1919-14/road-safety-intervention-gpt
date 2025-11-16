# Detailed Setup Guide

This guide provides step-by-step instructions for setting up the Road Safety Intervention GPT project.

## Prerequisites Checklist

Before you begin, ensure you have:
- [ ] Python 3.8 or higher installed
- [ ] pip package manager
- [ ] Neo4j Desktop or Server
- [ ] Ollama installed
- [ ] At least 8GB RAM
- [ ] Stable internet connection (for initial setup)

## Part 1: System Setup

### 1.1 Python Environment

```bash
# Check Python version
python --version  # Should be 3.8+

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 1.2 Install Python Dependencies

```bash
# Install all requirements
pip install -r requirements.txt

# Verify installations
python -c "import flask; print('Flask OK')"
python -c "import neo4j; print('Neo4j Driver OK')"
python -c "from sentence_transformers import SentenceTransformer; print('Transformers OK')"
```

## Part 2: Neo4j Setup

### 2.1 Install Neo4j Desktop

1. Download from: https://neo4j.com/download/
2. Install and launch Neo4j Desktop
3. Create a new project: "Road Safety GPT"

### 2.2 Create Database

1. Click "Add" → "Local DBMS"
2. Set database name: `road-safety-db`
3. Set password: `admin123` (or update in code)
4. Click "Create"
5. Click "Start" to launch the database

### 2.3 Import CSV Data

**Option A: Using Neo4j Browser**

1. Open Neo4j Browser (click "Open" on your database)
2. Copy `GPT_Input_DB.csv` to Neo4j import folder:
   - Find import folder: Settings → "Open Folder" → "Import"
3. Run this Cypher query in the browser:

```cypher
LOAD CSV WITH HEADERS FROM 'file:///GPT_Input_DB.csv' AS row
CREATE (i:InfrastructureIssue {
  s_no: toInteger(row.\`S. No.\`),
  problem: row.problem,
  category: row.category,
  type: row.type,
  data: row.data,
  code: row.code,
  clause: row.clause
});
```

**Option B: Using Python Script**

Create a file `import_data.py`:

```python
from neo4j import GraphDatabase
import csv

driver = GraphDatabase.driver(
    "neo4j://localhost:7687",
    auth=("neo4j", "admin123")
)

with driver.session() as session:
    with open('GPT_Input_DB.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            session.run('''
                CREATE (i:InfrastructureIssue {
                    s_no: $s_no,
                    problem: $problem,
                    category: $category,
                    type: $type,
                    data: $data,
                    code: $code,
                    clause: $clause
                })
            ''', s_no=int(row['S. No.']), 
                 problem=row['problem'],
                 category=row['category'],
                 type=row['type'],
                 data=row['data'],
                 code=row['code'],
                 clause=row['clause'])

driver.close()
print("Data imported successfully!")
```

Run: `python import_data.py`

### 2.4 Verify Data Import

In Neo4j Browser, run:
```cypher
MATCH (i:InfrastructureIssue) RETURN count(i) as total;
```
Should return: `total: 41`

## Part 3: Ollama Setup

### 3.1 Install Ollama

**On macOS:**
```bash
brew install ollama
```

**On Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**On Windows:**
Download installer from: https://ollama.ai/download

### 3.2 Pull Required Models

```bash
# Pull Llama 3.1 8B (for answer generation)
ollama pull llama3.1:8b

# Pull fine-tuned model (if available on Ollama)
ollama pull VSSKSN/Llama_RSIGPT
```

### 3.3 Start Ollama Server

```bash
# Start Ollama (runs as background service)
ollama serve
```

### 3.4 Verify Ollama

```bash
# List installed models
ollama list

# Test model
ollama run llama3.1:8b "Hello, test message"
```

## Part 4: Project Setup

### 4.1 Clone Repository

```bash
git clone https://github.com/yourusername/road-safety-gpt.git
cd road-safety-gpt
```

### 4.2 Configure File Paths

Update file paths in these files if needed:
- `backend-server.py` (lines 25-27)
- `main.py` (lines 11-13)
- `vector_retriever.py` (constructor)

Ensure paths match your project structure.

### 4.3 Test Individual Components

**Test Vector Retriever:**
```bash
python vector_retriever.py
```
Expected output: "Successfully loaded all JSON files!"

**Test Graph Retrieval:**
```bash
python graph_retrieval.py
```
Expected output: Query results from Neo4j

**Test Answer Generator:**
```bash
python answer_generator.py
```
Expected output: Connection to Ollama confirmed

## Part 5: Run the Application

### 5.1 Start Backend Server

```bash
python backend-server.py
```

Expected output:
```
✓ GraphPipeline initialized successfully
✓ VectorRetriever initialized successfully
✓ AnswerGenerator initialized
 * Running on http://0.0.0.0:5000
```

### 5.2 Open Frontend

**Option A: Direct file access**
- Double-click `index.html`

**Option B: HTTP server (recommended)**
```bash
# In a new terminal
python -m http.server 8000
```
Then visit: http://localhost:8000

### 5.3 Test the System

1. Enter a query in the chat: "What are the regulations for damaged STOP signs?"
2. Wait for response (2-5 seconds)
3. Verify response includes IRC citations

## Troubleshooting

### Neo4j Connection Issues
```bash
# Check if Neo4j is running
# In Neo4j Desktop, ensure database status is "Started"

# Test connection
python -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('neo4j://localhost:7687', auth=('neo4j', 'admin123')); driver.verify_connectivity(); print('Connected!')"
```

### Ollama Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
killall ollama  # On Unix-like systems
ollama serve
```

### Python Package Issues
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check specific package
pip show sentence-transformers
```

### Port Conflicts
If port 5000 or 8000 is in use:
- Change port in `backend-server.py` (last line)
- Or kill process using the port:
  ```bash
  # On Unix-like systems
  lsof -ti:5000 | xargs kill -9
  ```

## Next Steps

Once setup is complete:
1. Read the main README.md for usage examples
2. Check CONTRIBUTING.md if you want to contribute
3. Explore the codebase and experiment!

## Support

If you encounter issues:
1. Check existing GitHub Issues
2. Search for error messages online
3. Create a new issue with detailed information

**Happy coding! 🚀**
