from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

class RecommendationEngine:
    """Execute recommendation queries on Neo4j"""
    
    def __init__(self):
        """Initialize connection to Neo4j database"""
        self.uri = None
        self.user = None
        self.password = None
    
        # Try Streamlit secrets first
        try:
            import streamlit as st
            if "NEO4J_URI" in st.secrets:
                self.uri = st.secrets["NEO4J_URI"]
                self.user = st.secrets["NEO4J_USER"]
                self.password = st.secrets["NEO4J_PASSWORD"]
                print("✅ Loaded Neo4j config from Streamlit secrets")
        except Exception as e:
            print(f"⚠️ Could not load from Streamlit secrets: {e}")
    
        # Fallback to environment variables
        if not self.uri:
            self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            self.user = os.getenv("NEO4J_USER", "neo4j")
            self.password = os.getenv("NEO4J_PASSWORD", "password")
            print("✅ Loaded Neo4j config from environment")
    
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            print("✅ Connected to Neo4j successfully!")
        except Exception as e:
            print(f"⚠️ Could not connect to Neo4j: {e}")
            print("📌 App will run in limited mode without database")
            self.driver = None
    
    def execute_query(self, query, params=None):
        """
        Execute any Cypher query and return results
        
        Args:
            query (str): The Cypher query to execute
            params (dict): Parameters for the query
            
        Returns:
            dict: {
                "success": bool,
                "data": list of dicts,
                "count": int,
                "error": str (if failed)
            }
        """
        # Check if database is connected
        if self.driver is None:
            return {
                "success": False,
                "error": "Neo4j database not connected. Please check connection settings.",
                "data": [],
                "count": 0
            }
        
        if params is None:
            params = {}
        
        try:
            with self.driver.session() as session:
                result = session.run(query, params)
                
                # Convert Neo4j records to plain Python dictionaries
                data = []
                for record in result:
                    record_dict = {}
                    for key in record.keys():
                        value = record[key]
                        
                        # Handle different Neo4j data types
                        if value is None:
                            record_dict[key] = None
                        elif isinstance(value, (str, int, float, bool)):
                            record_dict[key] = value
                        elif isinstance(value, list):
                            record_dict[key] = value
                        elif hasattr(value, '_properties'):
                            # Neo4j Node or Relationship
                            record_dict[key] = dict(value._properties)
                        else:
                            # Fallback: convert to string
                            record_dict[key] = str(value)
                    
                    data.append(record_dict)
                
                return {
                    "success": True,
                    "data": data,
                    "count": len(data)
                }
        
        except Exception as e:
            import traceback
            error_msg = f"Query execution failed: {str(e)}"
            print(f"❌ {error_msg}")
            print(traceback.format_exc())
            
            return {
                "success": False,
                "error": error_msg,
                "data": [],
                "count": 0
            }

    def recommend_courses(self, student_id=None, skill_name=None):
        """Recommend courses based on student or skill"""
        if student_id:
            query = """
            MATCH (s:Student {id: $student_id})
            MATCH (i:Internship)-[:REQUIRES]->(req_skill:Skill)
            OPTIONAL MATCH (s)-[has:HAS_SKILL]->(req_skill)
            
            WITH s, req_skill, COALESCE(has.proficiency, 0) AS current_level
            WHERE current_level < 7
            
            MATCH (c:Course)-[:TEACHES]->(req_skill)
            WHERE NOT (s)-[:COMPLETED]->(c)
            AND NOT (s)-[:ENROLLED_IN]->(c)
            
            RETURN DISTINCT c.name as course,
                   c.code as code,
                   c.credits as credits,
                   c.difficulty as difficulty,
                   collect(DISTINCT req_skill.name) as teaches_skills
            ORDER BY c.difficulty
            LIMIT 5
            """
            params = {"student_id": student_id}
        elif skill_name:
            query = """
            MATCH (c:Course)-[:TEACHES]->(sk:Skill)
            WHERE sk.name CONTAINS $skill_name
            RETURN c.name as course,
                   c.code as code,
                   c.credits as credits,
                   c.difficulty as difficulty,
                   c.description as description,
                   collect(sk.name) as teaches_skills
            LIMIT 5
            """
            params = {"skill_name": skill_name}
        else:
            query = """
            MATCH (c:Course)
            RETURN c.name as course, c.credits, c.difficulty
            LIMIT 10
            """
            params = {}
        
        return self.execute_query(query, params)
    
    def recommend_internships(self, student_id):
        """Recommend internships for a student"""
        query = """
        MATCH (s:Student {id: $student_id})-[has:HAS_SKILL]->(student_skill:Skill)
        WITH s, collect({skill: student_skill, level: has.proficiency}) AS student_skills
        
        MATCH (i:Internship)-[r:REQUIRES]->(req_skill:Skill)
        WITH s, i, student_skills,
             collect({skill: req_skill, min_level: r.min_proficiency, 
                     mandatory: r.is_mandatory}) AS requirements
        
        WITH s, i, student_skills, requirements,
             [req IN requirements WHERE 
              any(ss IN student_skills WHERE ss.skill = req.skill 
                  AND ss.level >= req.min_level)] AS met_requirements
        
        WITH s, i, requirements, met_requirements,
             size(met_requirements) * 100.0 / size(requirements) AS match_percentage
        
        WHERE match_percentage >= 50
        
        RETURN i.company AS company,
               i.role AS role,
               i.location AS location,
               i.type AS internship_type,
               round(match_percentage, 1) AS match_percent,
               size(requirements) - size(met_requirements) AS skills_to_develop
        ORDER BY match_percentage DESC
        LIMIT 10
        """
        
        return self.execute_query(query, {"student_id": student_id})
    
    def get_skill_gap(self, student_id, internship_id):
        """Get skill gap for student targeting specific internship"""
        query = """
        MATCH (s:Student {id: $student_id})
        MATCH (i:Internship {id: $internship_id})-[r:REQUIRES]->(req_skill:Skill)
        
        OPTIONAL MATCH (s)-[has:HAS_SKILL]->(req_skill)
        
        WITH s, i, req_skill, r.min_proficiency AS required_level,
             COALESCE(has.proficiency, 0) AS current_level
        
        RETURN req_skill.name AS skill,
               required_level AS required,
               current_level AS current,
               required_level - current_level AS gap,
               CASE 
                   WHEN current_level = 0 THEN 'Missing'
                   WHEN current_level < required_level THEN 'Weak'
                   ELSE 'Sufficient'
               END AS status
        ORDER BY gap DESC
        """
        
        return self.execute_query(query, {
            "student_id": student_id,
            "internship_id": internship_id
        })
    
    def get_student_profile(self, student_id):
        """Get complete student profile"""
        query = """
        MATCH (s:Student {id: $student_id})
        
        OPTIONAL MATCH (s)-[has:HAS_SKILL]->(sk:Skill)
        WITH s, collect({skill: sk.name, proficiency: has.proficiency, 
                        category: sk.category}) AS skills
        
        OPTIONAL MATCH (s)-[:COMPLETED]->(c:Course)
        WITH s, skills, collect(c.name) AS completed_courses
        
        OPTIONAL MATCH (s)-[:COMPLETED]->(p:Project)
        WITH s, skills, completed_courses, collect(p.title) AS completed_projects
        
        RETURN s.name AS name,
               s.major AS major,
               s.year AS year,
               s.gpa AS gpa,
               s.email AS email,
               skills,
               completed_courses,
               completed_projects,
               size(skills) AS total_skills,
               size(completed_courses) AS total_courses,
               size(completed_projects) AS total_projects
        """
        
        return self.execute_query(query, {"student_id": student_id})
    
    def search_students(self, skill_name=None, major=None, min_gpa=None):
        """Search students by various criteria"""
        conditions = []
        params = {}
        
        if skill_name:
            conditions.append("(s)-[:HAS_SKILL]->(:Skill {name: $skill_name})")
            params["skill_name"] = skill_name
        
        if major:
            conditions.append("s.major = $major")
            params["major"] = major
        
        if min_gpa:
            conditions.append("s.gpa >= $min_gpa")
            params["min_gpa"] = float(min_gpa)
        
        where_clause = " AND ".join(conditions) if conditions else "true"
        
        query = f"""
        MATCH (s:Student)
        WHERE {where_clause}
        RETURN s.name AS name,
               s.major AS major,
               s.year AS year,
               s.gpa AS gpa
        ORDER BY s.gpa DESC
        LIMIT 20
        """
        
        return self.execute_query(query, params)
    
    def close(self):
        """Close the database connection"""
        if self.driver:
            self.driver.close()
            print("✅ Neo4j connection closed")


# Test the recommendation engine
if __name__ == "__main__":
    engine = RecommendationEngine()
    
    print("\n" + "="*70)
    print("TESTING RECOMMENDATION ENGINE")
    print("="*70)
    
    # Test 1: Course recommendations
    print("\n1. Course Recommendations for Python:")
    result = engine.recommend_courses(skill_name="Python")
    print(f"   Found {result['count']} courses")
    for course in result['data'][:3]:
        print(f"   - {course}")
    
    # Test 2: Student profile
    print("\n2. Student Profile (S001):")
    result = engine.get_student_profile("S001")
    if result['data']:
        print(f"   {result['data'][0]}")
    
    # Test 3: Internship recommendations
    print("\n3. Internship Recommendations (S002):")
    result = engine.recommend_internships("S002")
    print(f"   Found {result['count']} matching internships")
    for internship in result['data'][:3]:
        print(f"   - {internship}")
    
    engine.close()