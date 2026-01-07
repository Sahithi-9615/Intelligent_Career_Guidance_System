from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

class QueryTester:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD")
        
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def test_query_1(self):
        """Find all students with Python skill"""
        print("\n🔍 Query 1: Students who know Python")
        print("-" * 50)
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (s:Student)-[r:HAS_SKILL]->(sk:Skill {name: 'Python'})
                RETURN s.name as student, r.proficiency as proficiency
                ORDER BY r.proficiency DESC
            """)
            
            for record in result:
                print(f"   {record['student']}: Proficiency {record['proficiency']}/10")
    
    def test_query_2(self):
        """Find courses that teach Machine Learning"""
        print("\n🔍 Query 2: Courses teaching Machine Learning")
        print("-" * 50)
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Course)-[:TEACHES]->(sk:Skill {name: 'Machine Learning'})
                RETURN c.name as course, c.department as department
            """)
            
            for record in result:
                print(f"   {record['course']} ({record['department']})")
    
    def test_query_3(self):
        """Find students eligible for specific internship"""
        print("\n🔍 Query 3: Students eligible for Amazon Data Science Intern")
        print("-" * 50)
    
        with self.driver.session() as session:
            result = session.run("""
                MATCH (i:Internship {id: 'I002'})-[r:REQUIRES {is_mandatory: true}]->(req_skill:Skill)
                WITH i, collect({skill: req_skill, min_level: r.min_proficiency}) AS requirements
            
                MATCH (s:Student)-[has:HAS_SKILL]->(skill:Skill)
                WHERE skill IN [req IN requirements | req.skill]
            
                WITH s, i, requirements,
                    collect({skill: skill, proficiency: has.proficiency}) AS student_skills
            
                WHERE all(req IN requirements 
                        WHERE any(ss IN student_skills 
                                WHERE ss.skill = req.skill 
                                AND ss.proficiency >= req.min_level))
            
                RETURN s.name AS student
            """)
        
            count = 0
            for record in result:
                print(f"   ✅ {record['student']}")
                count += 1
        
            if count == 0:
                print("   ❌ No students currently eligible")

    
    def run_all_tests(self):
        print("\n" + "="*60)
        print("🧪 TESTING SAMPLE QUERIES")
        print("="*60)
        
        self.test_query_1()
        self.test_query_2()
        self.test_query_3()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETE")
        print("="*60 + "\n")


if __name__ == "__main__":
    tester = QueryTester()
    try:
        tester.run_all_tests()
    finally:
        tester.close()