# UNGDC Database Usage Guide

## 📚 Overview

The UNGDC (United Nations General Debate Corpus) database contains diplomatic speeches from the United Nations General Assembly from 1946 to 2022. This guide provides comprehensive information about the database structure, content, and usage.

## 🎯 Database Purpose

The UNGDC database is designed to:
- Store and organize UN diplomatic speeches
- Enable research on international relations and diplomacy
- Provide historical context for global political trends
- Support text analysis and natural language processing

## 🗃️ Database Structure

### Database Name
- **Database**: `ungdc_db`
- **User**: `postgres` (default)
- **Host**: `localhost`
- **Port**: `5432`

### Main Table: `documents`

```sql
CREATE TABLE documents (
    doc_id VARCHAR(50) PRIMARY KEY,
    iso VARCHAR(10),
    session INTEGER,
    year INTEGER,
    text TEXT,
    un_region VARCHAR(50)
);
```

#### Column Descriptions

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `doc_id` | VARCHAR(50) | Unique document identifier | `USA_01_1946` |
| `iso` | VARCHAR(10) | Country ISO code | `USA`, `CAN`, `FRA` |
| `session` | INTEGER | UN General Assembly session number | `1`, `77` |
| `year` | INTEGER | Year of the speech | `1946`, `2022` |
| `text` | TEXT | Full text of the diplomatic speech | "Mr. President, distinguished delegates..." |
| `un_region` | VARCHAR(50) | UN regional group | `GRULAC`, `WEOG`, `AFRICA` |

#### Indexes
- **Primary Key**: `doc_id` (unique identifier)
- **Recommended Indexes**: Consider adding indexes on `iso`, `year`, and `session` for better query performance

## 📊 Database Statistics

- **Total Documents**: 10,568 speeches
- **Time Span**: 1946 - 2022 (77 years)
- **Countries**: 201 unique countries
- **Sessions**: 77 UN General Assembly sessions
- **UN Regions**: 7 regional groups

### Country Distribution

The database contains speeches from all UN member states. Top countries by document count:
- Most countries: 77 documents (complete coverage)
- Some countries: 72-76 documents (partial coverage)

### Year Distribution

- **Earliest speech**: 1946 (UN founding year)
- **Latest speech**: 2022
- **Complete years**: Most years from 1946-2022 have full coverage

### UN Regional Groups

1. **AFRICA** - African Group
2. **ASIA** - Asia-Pacific Group  
3. **EASTEUROPE** - Eastern European Group
4. **GRULAC** - Latin American and Caribbean Group
5. **WEOG** - Western European and Others Group
6. **Other regional groupings as defined by UN

## 🔍 Query Examples

### Basic Queries

#### Get total document count
```sql
SELECT COUNT(*) FROM documents;
```

#### Get documents by country
```sql
-- Single country
SELECT * FROM documents WHERE iso = 'USA' LIMIT 10;

-- Multiple countries
SELECT * FROM documents WHERE iso IN ('USA', 'CAN', 'FRA') LIMIT 10;
```

#### Get documents by year
```sql
-- Single year
SELECT * FROM documents WHERE year = 1946 LIMIT 10;

-- Year range
SELECT * FROM documents WHERE year BETWEEN 2000 AND 2010 LIMIT 10;
```

#### Get documents by session
```sql
SELECT * FROM documents WHERE session = 77 LIMIT 10;
```

#### Get documents by UN region
```sql
SELECT * FROM documents WHERE un_region = 'GRULAC' LIMIT 10;
```

### Advanced Queries

#### Get document count by country
```sql
SELECT iso, COUNT(*) as document_count
FROM documents
GROUP BY iso
ORDER BY document_count DESC;
```

#### Get document count by year
```sql
SELECT year, COUNT(*) as document_count
FROM documents
GROUP BY year
ORDER BY year;
```

#### Get document count by region
```sql
SELECT un_region, COUNT(*) as document_count
FROM documents
GROUP BY un_region
ORDER BY document_count DESC;
```

#### Find speeches mentioning specific terms
```sql
SELECT doc_id, iso, year
FROM documents
WHERE text ILIKE '%climate change%' 
LIMIT 10;
```

#### Get statistics by country and year
```sql
SELECT iso, year, COUNT(*) as speech_count
FROM documents
GROUP BY iso, year
ORDER BY iso, year;
```

### Complex Queries

#### Find countries that spoke in multiple sessions
```sql
SELECT iso, COUNT(DISTINCT session) as session_count
FROM documents
GROUP BY iso
HAVING COUNT(DISTINCT session) > 10
ORDER BY session_count DESC;
```

#### Get yearly speech count trends
```sql
SELECT year, COUNT(*) as speech_count
FROM documents
GROUP BY year
ORDER BY year;
```

#### Find most active countries in specific region
```sql
SELECT iso, COUNT(*) as speech_count
FROM documents
WHERE un_region = 'WEOG'
GROUP BY iso
ORDER BY speech_count DESC
LIMIT 5;
```

## 🚀 API Endpoints

The database is accessed through a FastAPI interface with the following endpoints:

### Base URL
`http://localhost:8000`

### Available Endpoints

#### 1. Health Check
```
GET /health
```
Returns API status

#### 2. Statistics
```
GET /stats
```
Returns database statistics:
- Total documents
- Distinct countries
- Distinct years
- Distinct sessions
- Distinct regions

#### 3. List Countries
```
GET /countries
```
Returns list of all countries with document counts

#### 4. List Regions
```
GET /regions
```
Returns list of all UN regions with document counts

#### 5. List Documents
```
GET /documents
```
**Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Documents per page (default: 50, max: 200)
- `iso`: Country ISO code (use `;` for multiple)
- `year`: Single year filter
- `year_range`: Year range (format: start-end)
- `session`: Session number
- `un_region`: UN region

**Example:**
```
GET /documents?iso=USA;CAN&year_range=2000-2010&page=1&per_page=20
```

#### 6. Get Single Document
```
GET /documents/{doc_id}
```
Returns full document details including text

#### 7. Search Documents
```
GET /search?q={query}
```
Search in document text (minimum 3 characters)

## 🔧 Database Management

### Creating the Database

To create and populate the database:

```bash
cd /path/to/ungdc
python create_db.py
```

This script will:
1. Create the `ungdc_db` database if it doesn't exist
2. Create the `documents` table
3. Import data from `data/ungdc_1946-2022.csv`

### Connecting to the Database

#### Using psql
```bash
psql -U postgres -d ungdc_db -h localhost -p 5432
```

#### Using Python
```python
import psycopg2

conn = psycopg2.connect(
    dbname="ungdc_db",
    user="postgres",
    host="localhost",
    port="5432"
)

cursor = conn.cursor()
cursor.execute("SELECT * FROM documents LIMIT 5")
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()
```

#### Using asyncpg (for API)
```python
import asyncpg

conn = await asyncpg.connect('postgresql://postgres@localhost/ungdc_db')
rows = await conn.fetch("SELECT * FROM documents LIMIT 5")
for row in rows:
    print(row)
await conn.close()
```

## 📈 Data Analysis Examples

### Research Questions You Can Answer

1. **How has the language of diplomacy changed over time?**
   - Analyze text patterns by decade
   - Track keyword frequency over years

2. **Which countries are most active in specific policy areas?**
   - Search for keywords by country
   - Compare speech frequency by topic

3. **How do regional blocs coordinate positions?**
   - Compare speeches from same region
   - Identify common phrases across regions

4. **What are the historical trends in UN participation?**
   - Track number of speeches per country over time
   - Identify periods of increased/decreased engagement

### Example Analysis Queries

#### Find countries that consistently speak every year
```sql
SELECT iso, COUNT(DISTINCT year) as years_active
FROM documents
GROUP BY iso
HAVING COUNT(DISTINCT year) = (SELECT COUNT(DISTINCT year) FROM documents)
ORDER BY years_active DESC;
```

#### Get average speech length by country
```sql
SELECT iso, AVG(LENGTH(text)) as avg_length
FROM documents
GROUP BY iso
ORDER BY avg_length DESC
LIMIT 10;
```

#### Find years with most speeches
```sql
SELECT year, COUNT(*) as speech_count
FROM documents
GROUP BY year
ORDER BY speech_count DESC
LIMIT 5;
```

## 🛠️ Maintenance

### Backing Up the Database

```bash
pg_dump -U postgres -d ungdc_db -h localhost -p 5432 -F c -f ungdc_backup.dump
```

### Restoring the Database

```bash
pg_restore -U postgres -d ungdc_db -h localhost -p 5432 ungdc_backup.dump
```

### Optimizing Performance

```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_documents_iso ON documents(iso);
CREATE INDEX idx_documents_year ON documents(year);
CREATE INDEX idx_documents_session ON documents(session);
CREATE INDEX idx_documents_region ON documents(un_region);

-- Analyze the database for query planning
ANALYZE documents;
```

## 📖 Data Sources

- **Primary Data**: `data/ungdc_1946-2022.csv`
- **Format**: CSV with columns matching database schema
- **Coverage**: Complete UN General Debate speeches 1946-2022
- **Source**: United Nations Digital Library

## 💡 Tips for Effective Use

1. **Start with statistics**: Use `/stats` endpoint to understand data scope
2. **Use pagination**: For large result sets, use `page` and `per_page` parameters
3. **Combine filters**: Use multiple filter parameters for precise results
4. **Leverage regions**: UN regional groups can provide interesting insights
5. **Cache frequent queries**: Store results of common queries to improve performance

## 🚨 Troubleshooting

### Common Issues

**Issue: No results for valid query**
- Check filter parameters are correctly formatted
- Verify country ISO codes are valid (use `/countries` endpoint)
- Ensure year ranges are valid (start ≤ end)

**Issue: Slow query performance**
- Add indexes on frequently queried columns
- Limit result set with `per_page` parameter
- Use specific filters to reduce search space

**Issue: Connection refused**
- Verify PostgreSQL service is running
- Check database credentials
- Confirm database exists and is accessible

### Checking Database Status

```sql
-- Check if table exists
SELECT EXISTS (
    SELECT FROM information_schema.tables
    WHERE table_name = 'documents'
);

-- Check row count
SELECT COUNT(*) FROM documents;

-- Check sample data
SELECT * FROM documents LIMIT 5;
```

## 📝 Changelog

### Current Version
- **Database**: PostgreSQL 12+
- **API**: FastAPI with asyncpg
- **Data**: Complete 1946-2022 coverage
- **Features**: Advanced filtering, full-text search

### Future Enhancements
- Add full-text search indexes
- Implement caching for frequent queries
- Add more detailed metadata
- Expand to include other UN bodies

## 🤝 Support

For issues or questions:
1. Check this documentation first
2. Verify your query syntax
3. Test with simple queries first
4. Consult PostgreSQL documentation for SQL questions

## 📜 License

The UNGDC database and associated code are provided for research purposes. The speech texts are public domain documents from the United Nations. Please attribute the UN as the source when using speech content.

---

**Last Updated**: 2024
**Maintainer**: UNGDC Project Team
**Contact**: [Project Repository](#)

*This guide provides comprehensive coverage of the UNGDC database structure and usage. For specific research questions or advanced use cases, consult the API documentation or database directly.*