from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

class OntologyCreator:
    """Creates ontology structure in Neo4j: constraints, indexes, and validation rules"""
    
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD")
        
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        print(f"✅ Connected to Neo4j at {uri}")
    
    def close(self):
        self.driver.close()
        print("✅ Connection closed")
    
    def clear_database(self):
        """Clear all existing data (use with caution!)"""
        with self.driver.session() as session:
            # Delete all nodes and relationships
            session.run("MATCH (n) DETACH DELETE n")
            
            # Drop all constraints
            constraints = session.run("SHOW CONSTRAINTS").data()
            for constraint in constraints:
                constraint_name = constraint.get('name')
                if constraint_name:
                    session.run(f"DROP CONSTRAINT {constraint_name} IF EXISTS")
            
            # Drop all indexes
            indexes = session.run("SHOW INDEXES").data()
            for index in indexes:
                index_name = index.get('name')
                if index_name and index.get('type') != 'LOOKUP':
                    session.run(f"DROP INDEX {index_name} IF EXISTS")
        
        print("✅ Database cleared")
    
    def create_constraints(self):
        """Create uniqueness constraints for all node types"""
        print("\n📋 Creating Constraints...")
        
        with self.driver.session() as session:
            constraints = [
                # Student constraints
                ("CREATE CONSTRAINT student_id_unique IF NOT EXISTS "
                 "FOR (s:Student) REQUIRE s.id IS UNIQUE"),
                
                # Skill constraints
                ("CREATE CONSTRAINT skill_id_unique IF NOT EXISTS "
                 "FOR (sk:Skill) REQUIRE sk.id IS UNIQUE"),
                
                # Course constraints
                ("CREATE CONSTRAINT course_id_unique IF NOT EXISTS "
                 "FOR (c:Course) REQUIRE c.id IS UNIQUE"),
                
                # Project constraints
                ("CREATE CONSTRAINT project_id_unique IF NOT EXISTS "
                 "FOR (p:Project) REQUIRE p.id IS UNIQUE"),
                
                # Internship constraints
                ("CREATE CONSTRAINT internship_id_unique IF NOT EXISTS "
                 "FOR (i:Internship) REQUIRE i.id IS UNIQUE"),
            ]
            
            for constraint_query in constraints:
                try:
                    session.run(constraint_query)
                    constraint_name = constraint_query.split("FOR")[1].split("REQUIRE")[0].strip()
                    print(f"   ✅ Created constraint for {constraint_name}")
                except Exception as e:
                    print(f"   ⚠️  Constraint may already exist: {e}")
        
        print("✅ All constraints created")
    
    def create_indexes(self):
        """Create indexes for faster querying"""
        print("\n🔍 Creating Indexes...")
        
        with self.driver.session() as session:
            indexes = [
                # Student indexes
                "CREATE INDEX student_name_idx IF NOT EXISTS FOR (s:Student) ON (s.name)",
                "CREATE INDEX student_major_idx IF NOT EXISTS FOR (s:Student) ON (s.major)",
                "CREATE INDEX student_year_idx IF NOT EXISTS FOR (s:Student) ON (s.year)",
                
                # Skill indexes
                "CREATE INDEX skill_name_idx IF NOT EXISTS FOR (sk:Skill) ON (sk.name)",
                "CREATE INDEX skill_category_idx IF NOT EXISTS FOR (sk:Skill) ON (sk.category)",
                
                # Course indexes
                "CREATE INDEX course_name_idx IF NOT EXISTS FOR (c:Course) ON (c.name)",
                "CREATE INDEX course_dept_idx IF NOT EXISTS FOR (c:Course) ON (c.department)",
                
                # Internship indexes
                "CREATE INDEX internship_company_idx IF NOT EXISTS FOR (i:Internship) ON (i.company)",
                "CREATE INDEX internship_role_idx IF NOT EXISTS FOR (i:Internship) ON (i.role)",
            ]
            
            for index_query in indexes:
                try:
                    session.run(index_query)
                    index_name = index_query.split("FOR")[1].split("ON")[0].strip()
                    print(f"   ✅ Created index for {index_name}")
                except Exception as e:
                    print(f"   ⚠️  Index may already exist: {e}")
        
        print("✅ All indexes created")
    
    def validate_ontology_rules(self):
        """Validate that ontology rules are satisfied"""
        print("\n🔍 Validating Ontology Rules...")
        
        with self.driver.session() as session:
            validations = []
            
            # Rule 1: Check for courses without skills
            result = session.run("""
                MATCH (c:Course)
                WHERE NOT (c)-[:TEACHES]->(:Skill)
                RETURN count(c) as orphan_courses
            """)
            orphan_courses = result.single()["orphan_courses"]
            validations.append(("Courses must teach at least one skill", orphan_courses == 0))
            
            # Rule 2: Check for internships without skill requirements
            result = session.run("""
                MATCH (i:Internship)
                WHERE NOT (i)-[:REQUIRES]->(:Skill)
                RETURN count(i) as orphan_internships
            """)
            orphan_internships = result.single()["orphan_internships"]
            validations.append(("Internships must require at least one skill", orphan_internships == 0))
            
            # Rule 3: Check for invalid proficiency values
            result = session.run("""
                MATCH ()-[r:HAS_SKILL]->()
                WHERE r.proficiency < 1 OR r.proficiency > 10
                RETURN count(r) as invalid_proficiency
            """)
            invalid_prof = result.single()["invalid_proficiency"]
            validations.append(("HAS_SKILL proficiency must be 1-10", invalid_prof == 0))
            
            # Rule 4: Check for duplicate student enrollments
            result = session.run("""
                MATCH (s:Student)-[r:ENROLLED_IN]->(c:Course)
                WITH s, c, count(r) as enrollment_count
                WHERE enrollment_count > 1
                RETURN count(*) as duplicates
            """)
            duplicates = result.single()["duplicates"]
            validations.append(("No duplicate course enrollments", duplicates == 0))
            
            # Print validation results
            all_passed = True
            for rule, passed in validations:
                if passed:
                    print(f"   ✅ {rule}")
                else:
                    print(f"   ❌ {rule}")
                    all_passed = False
            
            if all_passed:
                print("\n✅ All ontology rules validated successfully!")
            else:
                print("\n⚠️  Some validation rules failed (this is OK if database is empty)")
            
            return all_passed
    
    def get_statistics(self):
        """Get database statistics"""
        print("\n📊 Database Statistics:")
        
        with self.driver.session() as session:
            # Count nodes
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as label, count(n) as count
                ORDER BY count DESC
            """)
            
            print("\n   Node Counts:")
            total_nodes = 0
            for record in result:
                label = record["label"] if record["label"] else "Unknown"
                count = record["count"]
                total_nodes += count
                print(f"      {label}: {count}")
            
            print(f"   Total Nodes: {total_nodes}")
            
            # Count relationships
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as relationship, count(r) as count
                ORDER BY count DESC
            """)
            
            print("\n   Relationship Counts:")
            total_rels = 0
            for record in result:
                rel_type = record["relationship"]
                count = record["count"]
                total_rels += count
                print(f"      {rel_type}: {count}")
            
            print(f"   Total Relationships: {total_rels}")
    
    def setup_complete_ontology(self):
        """Complete ontology setup process"""
        print("\n" + "="*60)
        print("🚀 SETTING UP ACADEMIC SKILL GRAPH ONTOLOGY")
        print("="*60)
        
        # Step 1: Clear existing data (optional - be careful!)
        response = input("\n⚠️  Clear existing database? (yes/no): ").strip().lower()
        if response == 'yes':
            self.clear_database()
        
        # Step 2: Create constraints
        self.create_constraints()
        
        # Step 3: Create indexes
        self.create_indexes()
        
        # Step 4: Show statistics
        self.get_statistics()
        
        print("\n" + "="*60)
        print("✅ ONTOLOGY SETUP COMPLETE!")
        print("="*60)
        print("\n📋 Next Steps:")
        print("   1. Create sample CSV data files")
        print("   2. Run import_data.py to load data")
        print("   3. Validate ontology rules with data")
        print("\n")


if __name__ == "__main__":
    creator = OntologyCreator()
    
    try:
        creator.setup_complete_ontology()
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        creator.close()