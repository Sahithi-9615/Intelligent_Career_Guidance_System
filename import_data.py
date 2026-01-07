from neo4j import GraphDatabase
import csv
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class DataImporter:
    """Import CSV data into Neo4j graph database"""
    
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD")
        
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.data_dir = Path("data")
        
        print(f"✅ Connected to Neo4j at {uri}")
    
    def close(self):
        self.driver.close()
        print("✅ Connection closed")
    
    def clear_all_data(self):
        """Clear all nodes and relationships (keeps schema)"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("✅ All existing data cleared")
    
    # ==================== IMPORT NODES ====================
    
    def import_students(self):
        """Import students from CSV"""
        print("\n📚 Importing Students...")
        
        csv_path = self.data_dir / "students.csv"
        
        with self.driver.session() as session:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                count = 0
                
                for row in reader:
                    session.run("""
                        CREATE (s:Student {
                            id: $id,
                            name: $name,
                            year: toInteger($year),
                            major: $major,
                            email: $email,
                            gpa: toFloat($gpa)
                        })
                    """, 
                    id=row['student_id'],
                    name=row['name'],
                    year=row['year'],
                    major=row['major'],
                    email=row['email'],
                    gpa=row['gpa'])
                    count += 1
                
        print(f"   ✅ Imported {count} students")
    
    def import_skills(self):
        """Import skills from CSV"""
        print("\n💡 Importing Skills...")
        
        csv_path = self.data_dir / "skills.csv"
        
        with self.driver.session() as session:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                count = 0
                
                for row in reader:
                    session.run("""
                        CREATE (sk:Skill {
                            id: $id,
                            name: $name,
                            category: $category,
                            level: $level,
                            description: $description
                        })
                    """,
                    id=row['skill_id'],
                    name=row['name'],
                    category=row['category'],
                    level=row['level'],
                    description=row['description'])
                    count += 1
        
        print(f"   ✅ Imported {count} skills")
    
    def import_courses(self):
        """Import courses from CSV"""
        print("\n📖 Importing Courses...")
        
        csv_path = self.data_dir / "courses.csv"
        
        with self.driver.session() as session:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                count = 0
                
                for row in reader:
                    session.run("""
                        CREATE (c:Course {
                            id: $id,
                            name: $name,
                            code: $code,
                            credits: toInteger($credits),
                            department: $department,
                            description: $description,
                            difficulty: $difficulty
                        })
                    """,
                    id=row['course_id'],
                    name=row['name'],
                    code=row['code'],
                    credits=row['credits'],
                    department=row['department'],
                    description=row['description'],
                    difficulty=row['difficulty'])
                    count += 1
        
        print(f"   ✅ Imported {count} courses")
    
    def import_projects(self):
        """Import projects from CSV"""
        print("\n🚀 Importing Projects...")
        
        csv_path = self.data_dir / "projects.csv"
        
        with self.driver.session() as session:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                count = 0
                
                for row in reader:
                    session.run("""
                        CREATE (p:Project {
                            id: $id,
                            title: $title,
                            description: $description,
                            difficulty: $difficulty,
                            duration_weeks: toInteger($duration_weeks),
                            type: $type
                        })
                    """,
                    id=row['project_id'],
                    title=row['title'],
                    description=row['description'],
                    difficulty=row['difficulty'],
                    duration_weeks=row['duration_weeks'],
                    type=row['type'])
                    count += 1
        
        print(f"   ✅ Imported {count} projects")
    
    def import_internships(self):
        """Import internships from CSV"""
        print("\n💼 Importing Internships...")
        
        csv_path = self.data_dir / "internships.csv"
        
        with self.driver.session() as session:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                count = 0
                
                for row in reader:
                    session.run("""
                        CREATE (i:Internship {
                            id: $id,
                            company: $company,
                            role: $role,
                            location: $location,
                            duration_months: toInteger($duration_months),
                            type: $type,
                            description: $description
                        })
                    """,
                    id=row['internship_id'],
                    company=row['company'],
                    role=row['role'],
                    location=row['location'],
                    duration_months=row['duration_months'],
                    type=row['type'],
                    description=row['description'])
                    count += 1
        
        print(f"   ✅ Imported {count} internships")
    
    # ==================== IMPORT RELATIONSHIPS ====================
    
    def import_student_skills(self):
        """Import student HAS_SKILL relationships"""
        print("\n🔗 Creating Student → Skill relationships...")
        
        csv_path = self.data_dir / "student_skills.csv"
        
        with self.driver.session() as session:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                count = 0
                
                for row in reader:
                    session.run("""
                        MATCH (s:Student {id: $student_id})
                        MATCH (sk:Skill {id: $skill_id})
                        CREATE (s)-[:HAS_SKILL {
                            proficiency: toInteger($proficiency),
                            acquired_date: $acquired_date,
                            verified: $verified = 'true'
                        }]->(sk)
                    """,
                    student_id=row['student_id'],
                    skill_id=row['skill_id'],
                    proficiency=row['proficiency'],
                    acquired_date=row['acquired_date'],
                    verified=row['verified'])
                    count += 1
        
        print(f"   ✅ Created {count} HAS_SKILL relationships")
    
    def import_course_skills(self):
        """Import course TEACHES relationships"""
        print("\n🔗 Creating Course → Skill relationships...")
        
        csv_path = self.data_dir / "course_skills.csv"
        
        with self.driver.session() as session:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                count = 0
                
                for row in reader:
                    session.run("""
                        MATCH (c:Course {id: $course_id})
                        MATCH (sk:Skill {id: $skill_id})
                        CREATE (c)-[:TEACHES {
                            depth: $depth,
                            hours: toInteger($hours)
                        }]->(sk)
                    """,
                    course_id=row['course_id'],
                    skill_id=row['skill_id'],
                    depth=row['depth'],
                    hours=row['hours'])
                    count += 1
        
        print(f"   ✅ Created {count} TEACHES relationships")
    
    def import_project_skills(self):
        """Import project REQUIRES relationships"""
        print("\n🔗 Creating Project → Skill relationships...")
        
        csv_path = self.data_dir / "project_skills.csv"
        
        with self.driver.session() as session:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                count = 0
                
                for row in reader:
                    session.run("""
                        MATCH (p:Project {id: $project_id})
                        MATCH (sk:Skill {id: $skill_id})
                        CREATE (p)-[:REQUIRES {
                            importance: $importance,
                            min_proficiency: toInteger($min_proficiency)
                        }]->(sk)
                    """,
                    project_id=row['project_id'],
                    skill_id=row['skill_id'],
                    importance=row['importance'],
                    min_proficiency=row['min_proficiency'])
                    count += 1
        
        print(f"   ✅ Created {count} REQUIRES relationships (Projects)")
    
    def import_student_courses(self):
        """Import student COMPLETED/ENROLLED_IN relationships"""
        print("\n🔗 Creating Student → Course relationships...")
        
        csv_path = self.data_dir / "student_courses.csv"
        
        with self.driver.session() as session:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                completed_count = 0
                enrolled_count = 0
                
                for row in reader:
                    status = row['status']
                    
                    if status == 'Completed':
                        session.run("""
                            MATCH (s:Student {id: $student_id})
                            MATCH (c:Course {id: $course_id})
                            CREATE (s)-[:COMPLETED {
                                grade: $grade,
                                semester: $semester,
                                completion_date: $completion_date
                            }]->(c)
                        """,
                        student_id=row['student_id'],
                        course_id=row['course_id'],
                        grade=row['grade'],
                        semester=row['semester'],
                        completion_date=row['completion_date'])
                        completed_count += 1
                    
                    elif status == 'Active':
                        session.run("""
                            MATCH (s:Student {id: $student_id})
                            MATCH (c:Course {id: $course_id})
                            CREATE (s)-[:ENROLLED_IN {
                                semester: $semester,
                                status: $status
                            }]->(c)
                        """,
                        student_id=row['student_id'],
                        course_id=row['course_id'],
                        semester=row['semester'],
                        status=row['status'])
                        enrolled_count += 1
        
        print(f"   ✅ Created {completed_count} COMPLETED relationships")
        print(f"   ✅ Created {enrolled_count} ENROLLED_IN relationships")
    
    def import_student_projects(self):
        """Import student COMPLETED project relationships"""
        print("\n🔗 Creating Student → Project relationships...")
        
        csv_path = self.data_dir / "student_projects.csv"
        
        with self.driver.session() as session:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                count = 0
                
                for row in reader:
                    session.run("""
                        MATCH (s:Student {id: $student_id})
                        MATCH (p:Project {id: $project_id})
                        CREATE (s)-[:COMPLETED {
                            completion_date: $completion_date,
                            role: $role,
                            grade: $grade
                        }]->(p)
                    """,
                    student_id=row['student_id'],
                    project_id=row['project_id'],
                    completion_date=row['completion_date'],
                    role=row['role'],
                    grade=row['grade'])
                    count += 1
        
        print(f"   ✅ Created {count} COMPLETED relationships (Projects)")
    
    def import_internship_skills(self):
        """Import internship REQUIRES relationships"""
        print("\n🔗 Creating Internship → Skill relationships...")
        
        csv_path = self.data_dir / "internship_skills.csv"
        
        with self.driver.session() as session:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                count = 0
                
                for row in reader:
                    session.run("""
                        MATCH (i:Internship {id: $internship_id})
                        MATCH (sk:Skill {id: $skill_id})
                        CREATE (i)-[:REQUIRES {
                            min_proficiency: toInteger($min_proficiency),
                            is_mandatory: $is_mandatory = 'true'
                        }]->(sk)
                    """,
                    internship_id=row['internship_id'],
                    skill_id=row['skill_id'],
                    min_proficiency=row['min_proficiency'],
                    is_mandatory=row['is_mandatory'])
                    count += 1
        
        print(f"   ✅ Created {count} REQUIRES relationships (Internships)")
    
    def get_statistics(self):
        """Display database statistics"""
        print("\n" + "="*60)
        print("📊 DATABASE STATISTICS")
        print("="*60)
        
        with self.driver.session() as session:
            # Count nodes by type
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as label, count(n) as count
                ORDER BY count DESC
            """)
            
            print("\n   NODE COUNTS:")
            total_nodes = 0
            for record in result:
                label = record["label"]
                count = record["count"]
                total_nodes += count
                print(f"      {label:.<20} {count:>5}")
            print(f"      {'TOTAL':.<20} {total_nodes:>5}")
            
            # Count relationships by type
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as relationship, count(r) as count
                ORDER BY count DESC
            """)
            
            print("\n   RELATIONSHIP COUNTS:")
            total_rels = 0
            for record in result:
                rel_type = record["relationship"]
                count = record["count"]
                total_rels += count
                print(f"      {rel_type:.<20} {count:>5}")
            print(f"      {'TOTAL':.<20} {total_rels:>5}")
        
        print("="*60)
    
    def validate_data(self):
        """Validate imported data"""
        print("\n" + "="*60)
        print("✅ VALIDATING DATA")
        print("="*60)
        
        with self.driver.session() as session:
            # Check for orphaned nodes
            result = session.run("""
                MATCH (n)
                WHERE NOT (n)--()
                RETURN labels(n)[0] as label, count(n) as count
            """)
            
            orphan_found = False
            for record in result:
                if record["count"] > 0:
                    orphan_found = True
                    print(f"   ⚠️  Found {record['count']} orphaned {record['label']} nodes")
            
            if not orphan_found:
                print("   ✅ No orphaned nodes found")
            
            # Validate ontology rules
            print("\n   ONTOLOGY RULES:")
            
            # Rule 1: Courses must teach skills
            result = session.run("""
                MATCH (c:Course)
                WHERE NOT (c)-[:TEACHES]->(:Skill)
                RETURN count(c) as count
            """)
            count = result.single()["count"]
            if count == 0:
                print("      ✅ All courses teach at least one skill")
            else:
                print(f"      ❌ {count} courses don't teach any skills")
            
            # Rule 2: Internships must require skills
            result = session.run("""
                MATCH (i:Internship)
                WHERE NOT (i)-[:REQUIRES]->(:Skill)
                RETURN count(i) as count
            """)
            count = result.single()["count"]
            if count == 0:
                print("      ✅ All internships require at least one skill")
            else:
                print(f"      ❌ {count} internships don't require any skills")
            
            # Rule 3: Valid proficiency levels
            result = session.run("""
                MATCH ()-[r:HAS_SKILL]->()
                WHERE r.proficiency < 1 OR r.proficiency > 10
                RETURN count(r) as count
            """)
            count = result.single()["count"]
            if count == 0:
                print("      ✅ All skill proficiencies are valid (1-10)")
            else:
                print(f"      ❌ {count} invalid proficiency values found")
        
        print("="*60)
    
    def import_all(self):
        """Complete data import process"""
        print("\n" + "="*60)
        print("🚀 STARTING DATA IMPORT")
        print("="*60)
        
        try:
            # Clear existing data
            response = input("\n⚠️  Clear existing data before import? (yes/no): ").strip().lower()
            if response == 'yes':
                self.clear_all_data()
            
            # Import all nodes
            print("\n" + "="*60)
            print("STEP 1: IMPORTING NODES")
            print("="*60)
            self.import_students()
            self.import_skills()
            self.import_courses()
            self.import_projects()
            self.import_internships()
            
            # Import all relationships
            print("\n" + "="*60)
            print("STEP 2: IMPORTING RELATIONSHIPS")
            print("="*60)
            self.import_student_skills()
            self.import_course_skills()
            self.import_project_skills()
            self.import_student_courses()
            self.import_student_projects()
            self.import_internship_skills()
            
            # Show statistics
            self.get_statistics()
            
            # Validate data
            self.validate_data()
            
            print("\n" + "="*60)
            print("✅ DATA IMPORT COMPLETE!")
            print("="*60)
            print("\n📋 Next Steps:")
            print("   1. Open Neo4j Browser")
            print("   2. Run: MATCH (n) RETURN n LIMIT 50")
            print("   3. Visualize your graph!")
            print("\n")
            
        except Exception as e:
            print(f"\n❌ Error during import: {e}")
            raise


if __name__ == "__main__":
    importer = DataImporter()
    
    try:
        importer.import_all()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
    finally:
        importer.close()