import os
from dotenv import load_dotenv
import re

load_dotenv()

class AIService:
    """Converts natural language queries into Cypher queries using Groq"""

    def __init__(self):
        self.provider = "groq"
        self._init_groq()

    
    def _init_groq(self):
        """Initialize Groq (FREE & SUPER FAST)"""
        self.api_key = None
    
    # Try Streamlit secrets first (for deployment and local with secrets.toml)
        try:
            import streamlit as st
            if "GROQ_API_KEY" in st.secrets:
                self.api_key = st.secrets["GROQ_API_KEY"]
                print("✅ Loaded API key from Streamlit secrets")
        except Exception as e:
            print(f"⚠️ Could not load from Streamlit secrets: {e}")
    
    # Fallback to environment variable (for .env file)
        if not self.api_key:
            self.api_key = os.getenv("GROQ_API_KEY")
            if self.api_key:
                print("✅ Loaded API key from .env file")
    
        # Check if we got the key
        if not self.api_key:
            raise Exception(
                "GROQ_API_KEY not found!\n"
                "Get your free key from: https://console.groq.com/\n"
                "Add to .env file or .streamlit/secrets.toml"
            )
    
        try:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
            self.model = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
            print(f"✅ AI Service initialized with Groq (FREE)")
            print(f"✅ Using model: {self.model}")
            print(f"⚡ Speed: 0.3-0.5 seconds per query")
        except ImportError:
            raise Exception(
                "Groq package not found!\n"
                "Install with: pip install groq"
            )
    
    def get_system_prompt(self):
        """Enhanced universal prompt for ANY Cypher query generation"""
        return """You are an EXPERT Neo4j Cypher query generator. Your ONLY job is to convert natural language into VALID, EXECUTABLE Cypher queries.

🚨 CRITICAL OUTPUT RULES:
1. Output ONLY the Cypher query - NO explanations, NO markdown, NO comments
2. NEVER return full nodes (e.g., RETURN s) - ALWAYS return specific properties with aliases
3. ALWAYS use RETURN clause aliases in ORDER BY (e.g., ORDER BY Match_Percent, NOT match_percent)
4. Use toLower() and CONTAINS for ALL string matching to handle case-insensitive searches
5. Add LIMIT to prevent overwhelming results (default: LIMIT 20)

📊 DATABASE SCHEMA (MEMORIZE THIS):

Nodes & Properties:
┌─────────────────────────────────────────────────────────────┐
│ Student: id, name, major, year, gpa, email                  │
│ Skill: id, name, category, level, description               │
│ Course: id, name, code, credits, department, difficulty     │
│ Project: id, title, difficulty, duration_weeks, type        │
│ Internship: id, company, role, location, duration_months    │
└─────────────────────────────────────────────────────────────┘

Relationships:
┌────────────────────────────────────────────────────────────────────┐
│ (Student)-[:HAS_SKILL {proficiency: 1-10}]->(Skill)               │
│ (Student)-[:COMPLETED {grade, semester}]->(Course)                │
│ (Student)-[:ENROLLED_IN {semester, status}]->(Course)             │
│ (Student)-[:COMPLETED {completion_date, role}]->(Project)         │
│ (Course)-[:TEACHES {depth, hours}]->(Skill)                       │
│ (Project)-[:REQUIRES {importance, min_proficiency}]->(Skill)      │
│ (Internship)-[:REQUIRES {min_proficiency, is_mandatory}]->(Skill) │
└────────────────────────────────────────────────────────────────────┘

🎯 QUERY PATTERNS (Learn These):

═══════════════════════════════════════════════════════════════════
PATTERN 1: SIMPLE NODE RETRIEVAL
═══════════════════════════════════════════════════════════════════
Query: "Show all students" / "List students" / "Get students"
MATCH (s:Student)
RETURN s.id AS ID, s.name AS Name, s.major AS Major, s.year AS Year, s.gpa AS GPA
ORDER BY s.name
LIMIT 20

Query: "Show courses" / "List all courses"
MATCH (c:Course)
RETURN c.id AS ID, c.name AS Name, c.code AS Code, c.credits AS Credits, c.department AS Department
ORDER BY c.department, c.name
LIMIT 20

Query: "Show skills" / "List skills"
MATCH (sk:Skill)
RETURN sk.id AS ID, sk.name AS Name, sk.category AS Category, sk.level AS Level
ORDER BY sk.category, sk.name
LIMIT 20

Query: "Show internships" / "List internships"
MATCH (i:Internship)
RETURN i.id AS ID, i.company AS Company, i.role AS Role, i.location AS Location, i.duration_months AS Duration
ORDER BY i.company
LIMIT 20

═══════════════════════════════════════════════════════════════════
PATTERN 2: FILTERED NODE SEARCH
═══════════════════════════════════════════════════════════════════
Query: "Find students with GPA > 3.5" / "Students with high GPA"
MATCH (s:Student)
WHERE s.gpa > 3.5
RETURN s.id AS ID, s.name AS Name, s.major AS Major, s.gpa AS GPA
ORDER BY s.gpa DESC
LIMIT 20

Query: "Show Computer Science students" / "CS majors"
MATCH (s:Student)
WHERE toLower(s.major) CONTAINS 'computer'
RETURN s.id AS ID, s.name AS Name, s.major AS Major, s.year AS Year, s.gpa AS GPA
ORDER BY s.gpa DESC
LIMIT 20

Query: "Find difficult courses" / "Hard courses"
MATCH (c:Course)
WHERE toLower(c.difficulty) IN ['hard', 'advanced', 'difficult']
RETURN c.id AS ID, c.name AS Name, c.code AS Code, c.difficulty AS Difficulty
ORDER BY c.name
LIMIT 20

═══════════════════════════════════════════════════════════════════
PATTERN 3: RELATIONSHIP-BASED QUERIES
═══════════════════════════════════════════════════════════════════
Query: "Show Alice's skills" / "What skills does Bob have" / "Skills of Carol"
MATCH (s:Student)-[has:HAS_SKILL]->(sk:Skill)
WHERE toLower(s.name) CONTAINS '[student_name]'
RETURN sk.name AS Skill, sk.category AS Category, has.proficiency AS Proficiency
ORDER BY has.proficiency DESC

Query: "What courses teach Python" / "Courses for React"
MATCH (c:Course)-[:TEACHES]->(sk:Skill)
WHERE toLower(sk.name) CONTAINS '[skill_name]'
RETURN c.name AS Course, c.code AS Code, c.credits AS Credits, c.difficulty AS Difficulty
ORDER BY c.name
LIMIT 20

Query: "Students with Python proficiency > 8" / "Find experts in Machine Learning"
MATCH (s:Student)-[has:HAS_SKILL]->(sk:Skill)
WHERE toLower(sk.name) CONTAINS '[skill_name]' AND has.proficiency > [threshold]
RETURN s.name AS Student, s.major AS Major, s.gpa AS GPA, has.proficiency AS Proficiency
ORDER BY has.proficiency DESC
LIMIT 20

═══════════════════════════════════════════════════════════════════
PATTERN 4: STUDENTS QUALIFYING FOR INTERNSHIPS
═══════════════════════════════════════════════════════════════════
Query: "Find students who qualify for IBM internship" / "Students eligible for Google"
MATCH (i:Internship)
WHERE toLower(i.company) CONTAINS '[company_name]'
MATCH (i)-[r:REQUIRES]->(req_skill:Skill)
WITH i, collect({skill: req_skill, min_level: r.min_proficiency}) as requirements
MATCH (s:Student)
OPTIONAL MATCH (s)-[has:HAS_SKILL]->(skill:Skill)
WITH s, i, requirements, collect({skill: skill, level: has.proficiency}) as student_skills
WITH s, i, requirements, student_skills, 
     [req IN requirements WHERE any(ss IN student_skills WHERE ss.skill = req.skill AND ss.level >= req.min_level)] as met_requirements
WITH s, i, size(met_requirements) * 100.0 / size(requirements) as match_percent
WHERE match_percent >= 70
RETURN s.id AS Student_ID, s.name AS Name, s.major AS Major, s.gpa AS GPA, 
       i.company AS Company, i.role AS Role, round(match_percent, 1) AS Match_Percent
ORDER BY Match_Percent DESC, s.gpa DESC
LIMIT 20

═══════════════════════════════════════════════════════════════════
PATTERN 5: INTERNSHIP RECOMMENDATIONS FOR STUDENTS
═══════════════════════════════════════════════════════════════════
Query: "Recommend internships for Alice" / "Which internships match Bob"
MATCH (s:Student)-[has:HAS_SKILL]->(skill:Skill)
WHERE toLower(s.name) CONTAINS '[student_name]'
WITH s, collect({skill: skill, level: has.proficiency}) as student_skills
MATCH (i:Internship)-[r:REQUIRES]->(req_skill:Skill)
WITH s, i, student_skills, collect({skill: req_skill, min_level: r.min_proficiency}) as requirements
WITH s, i, requirements, student_skills,
     [req IN requirements WHERE any(ss IN student_skills WHERE ss.skill = req.skill AND ss.level >= req.min_level)] as met_requirements
WITH i, size(met_requirements) * 100.0 / size(requirements) as match_percent
WHERE match_percent >= 40
RETURN i.company AS Company, i.role AS Role, i.location AS Location, 
       round(match_percent, 1) AS Match_Percent
ORDER BY Match_Percent DESC
LIMIT 10

═══════════════════════════════════════════════════════════════════
PATTERN 6: COURSE RECOMMENDATIONS FOR INTERNSHIPS
═══════════════════════════════════════════════════════════════════
Query: "Recommend courses for Carol to qualify for Google Software Engineer"
MATCH (s:Student)
WHERE toLower(s.name) CONTAINS '[student_name]'
MATCH (i:Internship)
WHERE toLower(i.company) CONTAINS '[company]' AND toLower(i.role) CONTAINS '[role]'
MATCH (i)-[r:REQUIRES]->(needed:Skill)
OPTIONAL MATCH (s)-[has:HAS_SKILL]->(needed)
WHERE has IS NULL OR has.proficiency < r.min_proficiency
WITH s, needed, r.min_proficiency as required_level, COALESCE(has.proficiency, 0) as current_level
MATCH (c:Course)-[:TEACHES]->(needed)
WHERE NOT (s)-[:COMPLETED]->(c) AND NOT (s)-[:ENROLLED_IN]->(c)
WITH c, collect(DISTINCT needed.name) as skills_taught, avg(required_level - current_level) as avg_gap
RETURN DISTINCT c.name AS Course, c.code AS Code, c.credits AS Credits, 
       skills_taught AS Skills_Taught, round(avg_gap, 1) AS Skill_Gap_Filled
ORDER BY Skill_Gap_Filled DESC
LIMIT 10

═══════════════════════════════════════════════════════════════════
PATTERN 7: SKILL GAP ANALYSIS (CRITICAL - PAY ATTENTION!)
═══════════════════════════════════════════════════════════════════
Query: "Show skill gaps for Bob for Amazon ML Engineer"
Query: "Missing skills for Emma Davis to qualify for Microsoft Cloud Engineer"
Query: "Show all missing skills for Alice for Google Software Engineer"
Query: "What skills does Carol need for IBM internship"

IMPORTANT: This pattern shows skills the student LACKS or is WEAK in, NOT their existing skills!
- Filter for skills where student has NO skill (has IS NULL) OR proficiency < required
- Show missing skills (Gap > 0) or weak skills (current < required)
- Order by Gap DESC to show most critical gaps first

Template:
MATCH (s:Student)
WHERE toLower(s.name) CONTAINS '[student_name]'
MATCH (i:Internship)
WHERE toLower(i.company) CONTAINS '[company]' AND toLower(i.role) CONTAINS '[role]'
MATCH (i)-[r:REQUIRES]->(skill:Skill)
OPTIONAL MATCH (s)-[has:HAS_SKILL]->(skill)
WITH skill, r.min_proficiency as required, COALESCE(has.proficiency, 0) as current
WHERE current < required
RETURN skill.name AS Skill, skill.category AS Category, 
       required AS Required_Level, current AS Current_Level, 
       (required - current) AS Gap,
       CASE WHEN current = 0 THEN 'Missing' 
            WHEN current < required THEN 'Weak' 
            ELSE 'Sufficient' END AS Status
ORDER BY Gap DESC

═══════════════════════════════════════════════════════════════════
PATTERN 8: AGGREGATION QUERIES
═══════════════════════════════════════════════════════════════════
Query: "Count students by major" / "How many students in each major"
MATCH (s:Student)
RETURN s.major AS Major, count(s) AS Student_Count
ORDER BY Student_Count DESC

Query: "Average GPA by major"
MATCH (s:Student)
RETURN s.major AS Major, round(avg(s.gpa), 2) AS Average_GPA, count(s) AS Students
ORDER BY Average_GPA DESC

Query: "Count courses by department"
MATCH (c:Course)
RETURN c.department AS Department, count(c) AS Course_Count
ORDER BY Course_Count DESC

═══════════════════════════════════════════════════════════════════
🎓 SMART QUERY GENERATION RULES:
═══════════════════════════════════════════════════════════════════

1. ENTITY EXTRACTION:
   - Student names: "Alice", "Bob Smith", "Carol White"
   - Companies: "Google", "Amazon", "Microsoft", "Meta", "Apple", "IBM", "Netflix"
   - Skills: "Python", "Java", "React", "Machine Learning", "SQL"
   - Roles: "Software Engineer", "ML Engineer", "Data Scientist"

2. KEYWORD DETECTION:
   - "show/list/get/find/display" → Retrieval query
   - "recommend/suggest" → Recommendation query
   - "qualify/eligible/match" → Matching query
   - "skill gap/missing skills" → Gap analysis
   - "count/average/sum" → Aggregation query

3. THRESHOLD INTERPRETATION:
   - "good students" → gpa > 3.5
   - "expert/advanced" → proficiency > 8
   - "intermediate" → proficiency 5-7
   - "beginner" → proficiency < 5
   - "qualified" → match_percent >= 70

4. CASE SENSITIVITY:
   - ALWAYS use toLower() for string comparisons
   - Use CONTAINS instead of exact match

5. SAFETY CHECKS:
   - Filter out completed/enrolled courses when recommending
   - Use OPTIONAL MATCH when data might not exist
   - Add reasonable LIMITs (10-20 results)

Remember: Output ONLY the Cypher query. NO explanations. NO markdown blocks.
"""

    def extract_entities(self, query):
        """Extract key entities from natural language query"""
        entities = {
            'student_name': None,
            'company': None,
            'role_keywords': None,
            'skill': None,
            'course': None,
            'threshold': None,
            'query_type': None
        }
        
        query_lower = query.lower()
        
        # Detect query type
        if any(word in query_lower for word in ['recommend', 'suggest']):
            entities['query_type'] = 'recommendation'
        elif 'missing skill' in query_lower or 'skill gap' in query_lower or ('missing' in query_lower and 'skill' in query_lower):
            entities['query_type'] = 'gap_analysis'
        elif any(word in query_lower for word in ['qualify', 'eligible', 'match']):
            entities['query_type'] = 'matching'
        elif any(word in query_lower for word in ['count', 'average', 'sum', 'how many']):
            entities['query_type'] = 'aggregation'
        else:
            entities['query_type'] = 'retrieval'
        
        # Extract student names (common patterns)
        student_patterns = [
            r'for\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'to\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+to',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)[\'s]',
            r'student\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'does\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+have',
            r'skills for\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]
        
        for pattern in student_patterns:
            match = re.search(pattern, query)
            if match:
                entities['student_name'] = match.group(1).lower()
                break
        
        # Extract company names
        companies = ['google', 'amazon', 'microsoft', 'meta', 'apple', 'netflix', 'facebook', 'ibm', 'oracle', 'salesforce', 'tesla', 'uber']
        for company in companies:
            if company in query_lower:
                entities['company'] = company
                break
        
        # Extract role keywords
        roles = {
            'software': ['software', 'engineer', 'developer', 'swe', 'backend', 'frontend', 'full stack'],
            'ml': ['ml', 'machine learning', 'ai', 'artificial intelligence'],
            'data': ['data scientist', 'data analyst', 'data engineer'],
            'cloud': ['cloud', 'devops', 'infrastructure']
        }
        
        for role_key, keywords in roles.items():
            if any(keyword in query_lower for keyword in keywords):
                entities['role_keywords'] = role_key
                break
        
        # Extract skills
        common_skills = ['python', 'java', 'javascript', 'react', 'sql', 'machine learning', 
                        'deep learning', 'aws', 'docker', 'kubernetes', 'node', 'angular', 
                        'vue', 'django', 'flask', 'spring', 'c++', 'c#', 'ruby']
        for skill in common_skills:
            if skill in query_lower:
                entities['skill'] = skill
                break
        
        # Extract thresholds
        threshold_match = re.search(r'(?:>|above|greater than|more than)\s*(\d+(?:\.\d+)?)', query_lower)
        if threshold_match:
            entities['threshold'] = float(threshold_match.group(1))
        
        return entities

    def generate_cypher_query(self, natural_language_query):
        """Main function: Convert user question into Cypher"""
        try:
            print(f"\n🤖 AI Input: {natural_language_query}")
            
            # Extract entities first
            entities = self.extract_entities(natural_language_query)
            print(f"📊 Extracted entities: {entities}")
            
            # Try AI generation first
            cypher_query = self._call_groq(natural_language_query, entities)
            
            print(f"✅ Generated Cypher:\n{cypher_query}")
            return cypher_query
            
        except Exception as e:
            print(f"❌ AI Error: {e}")
            print("⚠️ Using intelligent fallback generation")
            return self.intelligent_fallback(natural_language_query, entities)

    def _call_groq(self, prompt, entities):
        """Call Groq API with enhanced prompt including extracted entities"""
        try:
            # Build context-aware prompt
            context = f"""Convert this natural language query to Cypher: "{prompt}"

Extracted Context:
- Query Type: {entities.get('query_type', 'unknown')}
- Student: {entities.get('student_name', 'not specified')}
- Company: {entities.get('company', 'not specified')}
- Role: {entities.get('role_keywords', 'not specified')}
- Skill: {entities.get('skill', 'not specified')}
- Threshold: {entities.get('threshold', 'not specified')}

Generate the appropriate Cypher query based on the patterns in your knowledge."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.get_system_prompt()},
                    {"role": "user", "content": context}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            cypher = response.choices[0].message.content.strip()
            return self._clean_cypher_response(cypher)
            
        except Exception as e:
            raise Exception(f"Groq API error: {str(e)}")

    def _fix_cypher_scoping(self, cypher):
        """Fix common Cypher variable scoping issues"""
        # Fix ORDER BY using variables not in RETURN
        if "ORDER BY avg_gap" in cypher and "as Skill_Gap_Filled" in cypher:
            cypher = cypher.replace("ORDER BY avg_gap", "ORDER BY Skill_Gap_Filled")
        
        if "ORDER BY match_percent" in cypher and "as Match_Percent" in cypher:
            cypher = cypher.replace("ORDER BY match_percent", "ORDER BY Match_Percent")
        
        return cypher

    def _clean_cypher_response(self, response):
        """Extract only the Cypher query from AI response"""
        # Remove markdown code blocks
        response = response.replace('```cypher', '').replace('```', '').strip()
        
        # Split by common explanation markers
        lines = response.split('\n')
        cypher_lines = []
        
        for line in lines:
            line = line.strip()
            # Stop at explanation markers
            if any(marker in line.lower() for marker in [
                'explanation:', 'note:', 'this query', 'the query',
                'here\'s', 'i\'ve', 'you can', '* the', '* `', 'however,'
            ]):
                break
            # Skip empty lines at the start
            if not cypher_lines and not line:
                continue
            # Add valid Cypher lines
            if line and not line.startswith('//'):
                cypher_lines.append(line)
        
        # Join and clean up
        cypher = '\n'.join(cypher_lines).strip()
        cypher = cypher.rstrip(';').strip()
        
        # Fix scoping issues
        cypher = self._fix_cypher_scoping(cypher)
        
        return cypher

    def intelligent_fallback(self, query, entities):
        """Intelligent fallback using extracted entities and query type"""
        q = query.lower()
        query_type = entities.get('query_type')
        student = entities.get('student_name')
        company = entities.get('company')
        role = entities.get('role_keywords')
        skill = entities.get('skill')
        threshold = entities.get('threshold', 8)
        
        # MATCHING: Students qualifying for internships
        if query_type == 'matching' and 'student' in q and company:
            return f"""MATCH (i:Internship)
WHERE toLower(i.company) CONTAINS '{company}'
MATCH (i)-[r:REQUIRES]->(req_skill:Skill)
WITH i, collect({{skill: req_skill, min_level: r.min_proficiency}}) as requirements
MATCH (s:Student)
OPTIONAL MATCH (s)-[has:HAS_SKILL]->(skill:Skill)
WITH s, i, requirements, collect({{skill: skill, level: has.proficiency}}) as student_skills
WITH s, i, requirements, student_skills, [req IN requirements WHERE any(ss IN student_skills WHERE ss.skill = req.skill AND ss.level >= req.min_level)] as met_requirements
WITH s, i, size(met_requirements) * 100.0 / size(requirements) as match_percent
WHERE match_percent >= 70
RETURN s.id AS Student_ID, s.name AS Name, s.major AS Major, s.gpa AS GPA, i.company AS Company, i.role AS Role, round(match_percent, 1) AS Match_Percent
ORDER BY Match_Percent DESC, s.gpa DESC
LIMIT 20"""
        
        # RECOMMENDATION: Internships for student
        elif query_type == 'recommendation' and 'internship' in q and student:
            return f"""MATCH (s:Student)-[has:HAS_SKILL]->(skill:Skill)
WHERE toLower(s.name) CONTAINS '{student}'
WITH s, collect({{skill: skill, level: has.proficiency}}) as student_skills
MATCH (i:Internship)-[r:REQUIRES]->(req_skill:Skill)
WITH s, i, student_skills, collect({{skill: req_skill, min_level: r.min_proficiency}}) as requirements
WITH s, i, requirements, student_skills, [req IN requirements WHERE any(ss IN student_skills WHERE ss.skill = req.skill AND ss.level >= req.min_level)] as met_requirements
WITH i, size(met_requirements) * 100.0 / size(requirements) as match_percent
WHERE match_percent >= 40
RETURN i.company AS Company, i.role AS Role, i.location AS Location, round(match_percent, 1) AS Match_Percent
ORDER BY Match_Percent DESC
LIMIT 10"""
        
        # RECOMMENDATION: Courses for internship
        elif query_type == 'recommendation' and 'course' in q and student and company:
            role_filter = f"AND toLower(i.role) CONTAINS '{role}'" if role else ""
            return f"""MATCH (s:Student)
WHERE toLower(s.name) CONTAINS '{student}'
MATCH (i:Internship)
WHERE toLower(i.company) CONTAINS '{company}' {role_filter}
MATCH (i)-[r:REQUIRES]->(needed:Skill)
OPTIONAL MATCH (s)-[has:HAS_SKILL]->(needed)
WHERE has IS NULL OR has.proficiency < r.min_proficiency
WITH s, needed, r.min_proficiency as required_level, COALESCE(has.proficiency, 0) as current_level
MATCH (c:Course)-[:TEACHES]->(needed)
WHERE NOT (s)-[:COMPLETED]->(c) AND NOT (s)-[:ENROLLED_IN]->(c)
WITH c, collect(DISTINCT needed.name) as skills_taught, avg(required_level - current_level) as avg_gap
RETURN DISTINCT c.name AS Course, c.code AS Code, c.credits AS Credits, skills_taught AS Skills_Taught, round(avg_gap, 1) AS Skill_Gap_Filled
ORDER BY Skill_Gap_Filled DESC
LIMIT 10"""
        
        # GAP ANALYSIS
        elif query_type == 'gap_analysis' and student and company:
            role_filter = f"AND toLower(i.role) CONTAINS '{role}'" if role else ""
            return f"""MATCH (s:Student)
WHERE toLower(s.name) CONTAINS '{student}'
MATCH (i:Internship)
WHERE toLower(i.company) CONTAINS '{company}' {role_filter}
MATCH (i)-[r:REQUIRES]->(skill:Skill)
OPTIONAL MATCH (s)-[has:HAS_SKILL]->(skill)
WITH skill, r.min_proficiency as required, COALESCE(has.proficiency, 0) as current
WHERE current < required
RETURN skill.name AS Skill, skill.category AS Category, required AS Required_Level, current AS Current_Level, (required - current) AS Gap, CASE WHEN current = 0 THEN 'Missing' WHEN current < required THEN 'Weak' ELSE 'Sufficient' END AS Status
ORDER BY Gap DESC"""
        
        # RETRIEVAL: Students with specific skill
        elif skill and 'student' in q:
            if threshold:
                return f"""MATCH (s:Student)-[has:HAS_SKILL]->(sk:Skill)
WHERE toLower(sk.name) CONTAINS '{skill}' AND has.proficiency > {threshold}
RETURN s.id AS ID, s.name AS Name, s.major AS Major, s.gpa AS GPA, has.proficiency AS Proficiency
ORDER BY has.proficiency DESC
LIMIT 20"""
            else:
                return f"""MATCH (s:Student)-[has:HAS_SKILL]->(sk:Skill)
WHERE toLower(sk.name) CONTAINS '{skill}'
RETURN s.id AS ID, s.name AS Name, s.major AS Major, s.gpa AS GPA, has.proficiency AS Proficiency
ORDER BY has.proficiency DESC
LIMIT 20"""
        
        # RETRIEVAL: Student's skills
        elif student and 'skill' in q:
            return f"""MATCH (s:Student)-[has:HAS_SKILL]->(sk:Skill)
WHERE toLower(s.name) CONTAINS '{student}'
RETURN sk.name AS Skill, sk.category AS Category, has.proficiency AS Proficiency
ORDER BY has.proficiency DESC"""
        
        # RETRIEVAL: Courses teaching skill
        elif skill and 'course' in q:
            return f"""MATCH (c:Course)-[:TEACHES]->(sk:Skill)
WHERE toLower(sk.name) CONTAINS '{skill}'
RETURN c.name AS Course, c.code AS Code, c.credits AS Credits, c.difficulty AS Difficulty
ORDER BY c.name
LIMIT 20"""
        
        # AGGREGATION: Count by major
        elif query_type == 'aggregation' and 'major' in q:
            return """MATCH (s:Student)
RETURN s.major AS Major, count(s) AS Student_Count
ORDER BY Student_Count DESC"""
        
        # AGGREGATION: Average GPA
        elif query_type == 'aggregation' and 'gpa' in q:
            return """MATCH (s:Student)
RETURN s.major AS Major, round(avg(s.gpa), 2) AS Average_GPA, count(s) AS Students
ORDER BY Average_GPA DESC"""
        
        # DEFAULT: Show all students
        else:
            return """MATCH (s:Student)
RETURN s.id AS ID, s.name AS Name, s.major AS Major, s.year AS Year, s.gpa AS GPA
ORDER BY s.name
LIMIT 20"""


if __name__ == "__main__":
    ai = AIService()

    test_queries = [
        "Find students who qualify for IBM internship",
        "Show Alice Johnson's skills",
        "Students with Python proficiency above 8",
        "Recommend courses for Carol White to qualify for Google Software Engineer",
        "What are the skill gaps for Bob Smith for Amazon ML Engineer",
        "Show all students",
        "Count students by major",
        "What courses teach React",
        "Average GPA by major",
        "Recommend internships for David Brown",
        "Show Computer Science students with GPA > 3.5",
        "Find experts in Machine Learning",
        "Which students can apply to Microsoft",
        "Show me difficult courses"
    ]

    print("\n" + "=" * 80)
    print("TESTING UNIVERSAL AI QUERY GENERATION")
    print("=" * 80)

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}/{len(test_queries)}: {query}")
        print(f"{'='*80}")
        cypher = ai.generate_cypher_query(query)
        print(f"🔍 Generated Query:\n{cypher}")
        print(f"{'='*80}\n")

    print("\n✅ ALL TESTS COMPLETE")
    