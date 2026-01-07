from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

class ComplexQueries:
    """12 complex queries demonstrating advanced graph database capabilities"""
    
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD")
        
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        print(f"✅ Connected to Neo4j")
    
    def close(self):
        self.driver.close()
    
    def print_results(self, title, description, results, query_number):
        """Pretty print query results"""
        print("\n" + "="*70)
        print(f"QUERY {query_number}: {title}")
        print("="*70)
        print(f"Description: {description}")
        print("-"*70)
        
        if not results:
            print("   ⚠️  No results found")
        else:
            for i, record in enumerate(results, 1):
                print(f"\n   Result {i}:")
                for key, value in record.items():
                    if isinstance(value, list):
                        print(f"      {key}: {json.dumps(value, indent=10)}")
                    else:
                        print(f"      {key}: {value}")
        
        print("-"*70)
        print(f"Total Results: {len(results)}")
        print("="*70)
    
    # QUERY 1: Find students eligible for specific internship - FIXED
    def query_1_eligible_students(self):
        """
        COMPLEXITY: Multi-hop traversal + aggregation + filtering
        Find all students who meet ALL mandatory skill requirements for an internship
        """
        
        query = """
        MATCH (i:Internship {id: 'I001'})-[r:REQUIRES]->(required_skill:Skill)
        WITH i, collect({skill: required_skill, min_level: r.min_proficiency, 
                        mandatory: r.is_mandatory}) AS requirements
        
        MATCH (s:Student)-[has:HAS_SKILL]->(skill:Skill)
        // FIX: Changed list comprehension syntax
        WITH s, i, requirements, skill, has,
             [req IN requirements | req.skill] AS required_skills_list
        WHERE skill IN required_skills_list
        
        WITH s, i, requirements,
             collect({skill: skill, proficiency: has.proficiency}) AS student_skills
        
        // Check if student meets ALL mandatory requirements
        WHERE all(req IN requirements WHERE req.mandatory = false OR
                  any(ss IN student_skills 
                      WHERE ss.skill = req.skill 
                      AND ss.proficiency >= req.min_level))
        
        // Calculate match percentage
        WITH s, i, requirements, student_skills,
             size([req IN requirements WHERE req.mandatory = true AND
                   any(ss IN student_skills 
                       WHERE ss.skill = req.skill 
                       AND ss.proficiency >= req.min_level)]) AS met_mandatory,
             size([req IN requirements WHERE req.mandatory = true]) AS total_mandatory
        
        RETURN s.name AS student_name,
               s.major AS major,
               s.gpa AS gpa,
               i.company + ' - ' + i.role AS internship,
               met_mandatory + '/' + total_mandatory AS mandatory_skills_met,
               round(met_mandatory * 100.0 / total_mandatory, 1) AS match_percentage,
               [ss IN student_skills | ss.skill.name + ' (' + ss.proficiency + '/10)'] AS skills
        ORDER BY match_percentage DESC, s.gpa DESC
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            results = [dict(record) for record in result]
            
            self.print_results(
                "Find Eligible Students for Google Internship",
                "Multi-hop query with aggregation to find students meeting ALL mandatory requirements",
                results,
                1
            )
            
            return results
    
    # QUERY 2: Skill gap analysis
    def query_2_skill_gap_analysis(self):
        """
        COMPLEXITY: Set operations + conditional logic + scoring
        Identify missing and weak skills for student targeting specific internship
        """
        
        query = """
        MATCH (s:Student {id: 'S002'})
        MATCH (i:Internship {id: 'I002'})-[r:REQUIRES]->(req_skill:Skill)
        
        OPTIONAL MATCH (s)-[has:HAS_SKILL]->(req_skill)
        
        WITH s, i, req_skill, 
             r.min_proficiency AS required_level,
             r.is_mandatory AS is_mandatory,
             COALESCE(has.proficiency, 0) AS current_level
        
        WITH s, i,
             collect(CASE 
                     WHEN current_level = 0 THEN {
                         skill: req_skill.name,
                         category: req_skill.category,
                         status: 'Missing',
                         required: required_level,
                         current: 0,
                         gap: required_level,
                         mandatory: is_mandatory,
                         priority: CASE WHEN is_mandatory THEN 'HIGH' ELSE 'MEDIUM' END
                     }
                     WHEN current_level < required_level THEN {
                         skill: req_skill.name,
                         category: req_skill.category,
                         status: 'Weak',
                         required: required_level,
                         current: current_level,
                         gap: required_level - current_level,
                         mandatory: is_mandatory,
                         priority: CASE WHEN is_mandatory THEN 'HIGH' ELSE 'LOW' END
                     }
                     ELSE {
                         skill: req_skill.name,
                         category: req_skill.category,
                         status: 'Sufficient',
                         required: required_level,
                         current: current_level,
                         gap: 0,
                         mandatory: is_mandatory,
                         priority: 'NONE'
                     }
                     END) AS skill_analysis
        
        WITH s, i, skill_analysis,
             [sa IN skill_analysis WHERE sa.status = 'Missing'] AS missing,
             [sa IN skill_analysis WHERE sa.status = 'Weak'] AS weak,
             [sa IN skill_analysis WHERE sa.status = 'Sufficient'] AS sufficient
        
        RETURN s.name AS student,
               i.company + ' - ' + i.role AS target_internship,
               missing,
               weak,
               sufficient,
               size(sufficient) AS skills_ready,
               size(skill_analysis) AS total_skills_required,
               round(size(sufficient) * 100.0 / size(skill_analysis), 1) AS readiness_percentage,
               CASE 
                   WHEN size(sufficient) * 100.0 / size(skill_analysis) >= 80 THEN 'Ready to Apply'
                   WHEN size(sufficient) * 100.0 / size(skill_analysis) >= 60 THEN 'Almost Ready'
                   WHEN size(sufficient) * 100.0 / size(skill_analysis) >= 40 THEN 'Needs Preparation'
                   ELSE 'Significant Gap'
               END AS readiness_status
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            results = [dict(record) for record in result]
            
            self.print_results(
                "Skill Gap Analysis for Target Internship",
                "Set operations to identify missing, weak, and sufficient skills with priority scoring",
                results,
                2
            )
            
            return results
    
    # QUERY 3: Course recommendations to fill gaps
    def query_3_recommend_courses(self):
        """
        COMPLEXITY: Multi-step filtering + ranking + recommendation
        Recommend courses that teach missing/weak skills for target internship
        """
        
        query = """
        // Step 1: Find skill gaps
        MATCH (s:Student {id: 'S004'})
        MATCH (i:Internship {id: 'I001'})-[r:REQUIRES]->(req_skill:Skill)
        OPTIONAL MATCH (s)-[has:HAS_SKILL]->(req_skill)
        
        WITH s, req_skill, r.min_proficiency AS required_level,
             COALESCE(has.proficiency, 0) AS current_level
        WHERE current_level < required_level
        
        // Step 2: Find courses teaching these gap skills
        MATCH (c:Course)-[teaches:TEACHES]->(req_skill)
        
        // Step 3: Exclude already completed/enrolled courses
        WHERE NOT (s)-[:COMPLETED]->(c)
        AND NOT (s)-[:ENROLLED_IN]->(c)
        
        // Step 4: Calculate relevance score
        WITH s, c, 
             collect(DISTINCT {
                 skill: req_skill.name,
                 gap: required_level - current_level,
                 depth: teaches.depth
             }) AS gap_skills,
             count(DISTINCT req_skill) AS gap_skills_count
        
        // Step 5: Get all skills taught by course
        MATCH (c)-[:TEACHES]->(all_skills:Skill)
        
        WITH s, c, gap_skills, gap_skills_count,
             collect(DISTINCT all_skills.name) AS all_course_skills
        
        // Step 6: Calculate difficulty match with student year
        WITH s, c, gap_skills, gap_skills_count, all_course_skills,
             CASE 
                 WHEN s.year = 1 AND c.difficulty = 'Beginner' THEN 1.0
                 WHEN s.year = 2 AND c.difficulty IN ['Beginner', 'Intermediate'] THEN 0.9
                 WHEN s.year = 3 AND c.difficulty IN ['Intermediate', 'Advanced'] THEN 0.9
                 WHEN s.year = 4 AND c.difficulty = 'Advanced' THEN 1.0
                 ELSE 0.5
             END AS difficulty_match
        
        // Step 7: Calculate final score
        WITH s, c, gap_skills, gap_skills_count, all_course_skills, difficulty_match,
             (gap_skills_count * 10 + difficulty_match * 5 - c.credits) AS relevance_score
        
        RETURN c.name AS course_name,
               c.code AS course_code,
               c.department AS department,
               c.credits AS credits,
               c.difficulty AS difficulty,
               gap_skills AS fills_gaps,
               all_course_skills AS teaches_all_skills,
               gap_skills_count AS gap_skills_covered,
               round(difficulty_match * 100, 0) AS difficulty_match_percent,
               round(relevance_score, 2) AS relevance_score
        ORDER BY relevance_score DESC, gap_skills_count DESC, c.credits ASC
        LIMIT 5
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            results = [dict(record) for record in result]
            
            self.print_results(
                "Recommend Courses to Fill Skill Gaps",
                "Multi-criteria ranking: relevance, difficulty match, and credit hours",
                results,
                3
            )
            
            return results
    
    # QUERY 4: Find similar students (Collaborative filtering)
    def query_4_similar_students(self):
        """
        COMPLEXITY: Similarity calculation (Jaccard index) + ranking
        Find students with similar skill profiles using set operations
        """
        
        query = """
        MATCH (s1:Student {id: 'S001'})-[:HAS_SKILL]->(skill:Skill)
        WITH s1, collect(DISTINCT skill) AS s1_skills
        
        MATCH (s2:Student)-[:HAS_SKILL]->(skill2:Skill)
        WHERE s1 <> s2
        WITH s1, s1_skills, s2, collect(DISTINCT skill2) AS s2_skills
        
        // Calculate Jaccard similarity: |A ∩ B| / |A ∪ B|
        WITH s1, s2, s1_skills, s2_skills,
             [skill IN s1_skills WHERE skill IN s2_skills] AS common_skills
        
        WITH s1, s2, common_skills, s1_skills, s2_skills,
             size(common_skills) * 1.0 / 
             (size(s1_skills) + size(s2_skills) - size(common_skills)) AS jaccard_similarity
        
        WHERE jaccard_similarity >= 0.3
        
        // Get skill details
        WITH s1, s2, jaccard_similarity, common_skills,
             [s IN common_skills | s.name] AS common_skill_names,
             size(common_skills) AS common_count
        
        // Check if they took similar courses
        OPTIONAL MATCH (s1)-[:COMPLETED]->(c:Course)<-[:COMPLETED]-(s2)
        WITH s1, s2, jaccard_similarity, common_skill_names, common_count,
             count(DISTINCT c) AS shared_courses
        
        // Calculate final similarity score
        WITH s1, s2, jaccard_similarity, common_skill_names, common_count, shared_courses,
             (jaccard_similarity * 0.7 + (shared_courses * 0.1)) AS final_similarity
        
        RETURN s2.name AS similar_student,
               s2.major AS major,
               s2.year AS year,
               round(jaccard_similarity * 100, 1) AS skill_similarity_percent,
               common_count AS common_skills_count,
               common_skill_names,
               shared_courses,
               round(final_similarity * 100, 1) AS overall_similarity_score
        ORDER BY final_similarity DESC
        LIMIT 5
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            results = [dict(record) for record in result]
            
            self.print_results(
                "Find Similar Students (Collaborative Filtering)",
                "Jaccard similarity on skill sets with course overlap bonus",
                results,
                4
            )
            
            return results
    
    # QUERY 5: Learning path recommendation
    def query_5_learning_path(self):
        """
        COMPLEXITY: Shortest path algorithm + path cost calculation
        Find optimal learning path to acquire a target skill
        """
        
        query = """
        MATCH (s:Student {id: 'S006'})
        MATCH (target_skill:Skill {name: 'Machine Learning'})
        
        // Find if student already has this skill
        OPTIONAL MATCH (s)-[has:HAS_SKILL]->(target_skill)
        
        WITH s, target_skill, COALESCE(has.proficiency, 0) AS current_level
        
        // Find courses teaching this skill
        MATCH (c:Course)-[teaches:TEACHES]->(target_skill)
        WHERE NOT (s)-[:COMPLETED]->(c)
        AND NOT (s)-[:ENROLLED_IN]->(c)
        
        // Get prerequisites if any (simplified - assuming direct)
        OPTIONAL MATCH (c)-[:TEACHES]->(prereq_skill:Skill)<-[:HAS_SKILL]-(s)
        
        WITH s, target_skill, current_level, c, teaches,
             count(prereq_skill) AS prerequisites_met
        
        // Get all skills this course teaches
        MATCH (c)-[:TEACHES]->(all_skills:Skill)
        
        WITH s, target_skill, current_level, c, teaches, prerequisites_met,
             collect(DISTINCT all_skills.name) AS skills_gained
        
        // Calculate learning efficiency
        WITH s, target_skill, current_level, c, teaches, prerequisites_met, skills_gained,
             CASE teaches.depth
                 WHEN 'Mastery' THEN 10
                 WHEN 'Advanced' THEN 8
                 WHEN 'Intermediate' THEN 6
                 WHEN 'Introduction' THEN 4
                 ELSE 3
             END AS skill_gain,
             c.credits AS time_cost
        
        // Calculate efficiency score (skill gain / time cost)
        WITH s, target_skill, current_level, c, teaches, prerequisites_met, 
             skills_gained, skill_gain, time_cost,
             round((skill_gain * 1.0 / time_cost) * (1 + prerequisites_met * 0.1), 2) AS efficiency_score
        
        RETURN c.name AS recommended_course,
               c.code AS course_code,
               c.difficulty AS difficulty,
               c.credits AS credits,
               teaches.depth AS skill_depth,
               teaches.hours AS hours_dedicated,
               skill_gain AS expected_proficiency_gain,
               skills_gained AS bonus_skills,
               prerequisites_met AS prerequisites_already_met,
               efficiency_score,
               current_level AS current_skill_level,
               CASE 
                   WHEN current_level + skill_gain >= 7 THEN 'Will reach target level'
                   ELSE 'May need additional courses'
               END AS outcome
        ORDER BY efficiency_score DESC, skill_gain DESC
        LIMIT 3
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            results = [dict(record) for record in result]
            
            self.print_results(
                "Optimal Learning Path for Target Skill",
                "Efficiency-based course recommendation considering prerequisites and time",
                results,
                5
            )
            
            return results
    
    # QUERY 6: Trending skills analysis
    def query_6_trending_skills(self):
        """
        COMPLEXITY: Aggregation + statistical analysis + ranking
        Identify most in-demand skills across internships with supply-demand gap
        """
        
        query = """
        // Get demand side (internships requiring skills)
        MATCH (i:Internship)-[r:REQUIRES]->(skill:Skill)
        WITH skill, 
             count(DISTINCT i) AS internship_demand,
             avg(r.min_proficiency) AS avg_required_level,
             sum(CASE WHEN r.is_mandatory THEN 1 ELSE 0 END) AS mandatory_count,
             collect(DISTINCT i.company) AS hiring_companies
        
        // Get supply side (students with skills)
        MATCH (s:Student)-[has:HAS_SKILL]->(skill)
        WITH skill, internship_demand, avg_required_level, mandatory_count, hiring_companies,
             count(DISTINCT s) AS students_with_skill,
             avg(has.proficiency) AS avg_student_level,
             collect(DISTINCT s.name) AS qualified_students
        
        // Calculate supply-demand metrics
        WITH skill, internship_demand, avg_required_level, mandatory_count, 
             hiring_companies, students_with_skill, avg_student_level, qualified_students,
             round(avg_required_level - avg_student_level, 2) AS skill_gap,
             round(students_with_skill * 1.0 / internship_demand, 2) AS supply_demand_ratio
        
        // Calculate trend score
        WITH skill, internship_demand, avg_required_level, mandatory_count,
             hiring_companies, students_with_skill, avg_student_level, 
             skill_gap, supply_demand_ratio,
             (internship_demand * 10 + mandatory_count * 5 - supply_demand_ratio * 3) AS trend_score
        
        RETURN skill.name AS skill_name,
               skill.category AS category,
               internship_demand AS companies_requiring,
               round(avg_required_level, 1) AS avg_proficiency_required,
               students_with_skill AS students_have_it,
               round(avg_student_level, 1) AS avg_student_proficiency,
               skill_gap AS proficiency_gap,
               supply_demand_ratio AS students_per_opening,
               mandatory_count AS times_mandatory,
               hiring_companies,
               round(trend_score, 2) AS trend_score,
               CASE 
                   WHEN skill_gap > 2 THEN 'High training need'
                   WHEN supply_demand_ratio < 1 THEN 'Talent shortage'
                   WHEN internship_demand >= 3 THEN 'High demand'
                   ELSE 'Stable'
               END AS market_status
        ORDER BY trend_score DESC
        LIMIT 10
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            results = [dict(record) for record in result]
            
            self.print_results(
                "Trending Skills - Supply & Demand Analysis",
                "Statistical aggregation of skill demand vs student supply with gap analysis",
                results,
                6
            )
            
            return results
    
    # QUERY 7: Students by project demonstration
    def query_7_students_by_projects(self):
        """
        COMPLEXITY: Pattern matching + filtering by multiple criteria
        Find students who demonstrated specific skills through project completion
        """
        
        query = """
        WITH ['Python', 'Machine Learning'] AS target_skills
        
        // Find skills
        UNWIND target_skills AS skill_name
        MATCH (skill:Skill {name: skill_name})
        
        // Find students who completed projects requiring these skills
        MATCH (s:Student)-[comp:COMPLETED]->(p:Project)-[req:REQUIRES]->(skill)
        
        WITH s, skill, p, comp, req
        ORDER BY s.id, comp.completion_date DESC
        
        // Group by student
        WITH s, 
             collect(DISTINCT skill.name) AS demonstrated_skills,
             collect(DISTINCT {
                 project: p.title,
                 difficulty: p.difficulty,
                 date: comp.completion_date,
                 role: comp.role,
                 grade: comp.grade,
                 skill_importance: req.importance
             }) AS projects_completed
        
        // Filter students who demonstrated ALL target skills
        WHERE size(demonstrated_skills) = size(['Python', 'Machine Learning'])
        
        // Get their other skills
        MATCH (s)-[has:HAS_SKILL]->(other_skill:Skill)
        WITH s, demonstrated_skills, projects_completed,
             collect(DISTINCT {
                 skill: other_skill.name,
                 proficiency: has.proficiency,
                 verified: has.verified
             }) AS all_skills
        
        // Get courses they completed
        OPTIONAL MATCH (s)-[:COMPLETED]->(c:Course)
        WITH s, demonstrated_skills, projects_completed, all_skills,
             collect(DISTINCT c.name) AS courses_completed
        
        RETURN s.name AS student_name,
               s.major AS major,
               s.year AS year,
               s.gpa AS gpa,
               demonstrated_skills,
               size(projects_completed) AS projects_count,
               projects_completed,
               all_skills,
               size(courses_completed) AS courses_completed_count,
               CASE 
                   WHEN size(projects_completed) >= 3 THEN 'Highly Experienced'
                   WHEN size(projects_completed) = 2 THEN 'Experienced'
                   ELSE 'Some Experience'
               END AS experience_level
        ORDER BY projects_count DESC, s.gpa DESC
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            results = [dict(record) for record in result]
            
            self.print_results(
                "Students Who Demonstrated Skills Through Projects",
                "Find students with practical experience in specific skills via projects",
                results,
                7
            )
            
            return results
    
    # QUERY 8: Course effectiveness analysis - FIXED
    def query_8_course_effectiveness(self):
        """
        COMPLEXITY: Before/after comparison + statistical aggregation
        Analyze how well a course improves student skills (ROI analysis)
        """
        
        query = """
        MATCH (c:Course {id: 'C002'})-[:TEACHES]->(skill:Skill)
        
        // Students who completed this course
        MATCH (s_completed:Student)-[comp:COMPLETED]->(c)
        OPTIONAL MATCH (s_completed)-[has:HAS_SKILL]->(skill)
        
        WITH c, skill,
             collect(DISTINCT {
                 student: s_completed.name,
                 grade: comp.grade,
                 proficiency: COALESCE(has.proficiency, 0)
             }) AS completed_students,
             avg(COALESCE(has.proficiency, 0)) AS avg_proficiency_after,
             count(DISTINCT s_completed) AS students_completed
        
        // Students who have the skill but haven't taken the course
        MATCH (s_not_taken:Student)-[has2:HAS_SKILL]->(skill)
        WHERE NOT (s_not_taken)-[:COMPLETED]->(c)
        
        WITH c, skill, completed_students, avg_proficiency_after, students_completed,
             avg(has2.proficiency) AS avg_proficiency_without,
             count(DISTINCT s_not_taken) AS students_without_course
        
        // Calculate improvement delta
        WITH c, skill, completed_students, students_completed, students_without_course,
             avg_proficiency_after, avg_proficiency_without,
             round(avg_proficiency_after - avg_proficiency_without, 2) AS improvement_delta,
             round((avg_proficiency_after - avg_proficiency_without) * 100.0 / 
                   CASE WHEN avg_proficiency_without = 0 THEN 1 ELSE avg_proficiency_without END, 1) AS improvement_percent
        
        // Analyze by grade - FIX: Extract proficiency values properly
        WITH c, skill, students_completed, students_without_course,
             avg_proficiency_after, avg_proficiency_without,
             improvement_delta, improvement_percent, completed_students,
             [cs IN completed_students WHERE cs.grade IN ['A', 'A-'] | cs.proficiency] AS top_performers_list,
             [cs IN completed_students WHERE cs.grade IN ['B+', 'B', 'B-'] | cs.proficiency] AS mid_performers_list
        
        // FIX: Use reduce for averages
        WITH c, skill, students_completed, students_without_course,
             avg_proficiency_after, avg_proficiency_without,
             improvement_delta, improvement_percent,
             top_performers_list, mid_performers_list,
             size([cs IN completed_students WHERE cs.grade IN ['A', 'A-']]) AS top_count
        
        RETURN c.name AS course_name,
               skill.name AS skill_taught,
               students_completed,
               students_without_course,
               round(avg_proficiency_after, 2) AS avg_skill_after_course,
               round(avg_proficiency_without, 2) AS avg_skill_without_course,
               improvement_delta,
               improvement_percent,
               CASE WHEN size(top_performers_list) > 0 
                    THEN round(reduce(sum = 0.0, p IN top_performers_list | sum + p) / size(top_performers_list), 2)
                    ELSE null END AS top_performers_avg,
               CASE WHEN size(mid_performers_list) > 0
                    THEN round(reduce(sum = 0.0, p IN mid_performers_list | sum + p) / size(mid_performers_list), 2)
                    ELSE null END AS mid_performers_avg,
               top_count AS students_with_A,
               CASE 
                   WHEN improvement_delta >= 2 THEN 'Highly Effective'
                   WHEN improvement_delta >= 1 THEN 'Effective'
                   WHEN improvement_delta >= 0 THEN 'Somewhat Effective'
                   ELSE 'Not Effective'
               END AS effectiveness_rating
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            results = [dict(record) for record in result]
            
            self.print_results(
                "Course Effectiveness Analysis (ROI)",
                "Compare skill proficiency: students who took course vs. those who didn't",
                results,
                8
            )
            
            return results
    
    # QUERY 9: Career path analysis - FIXED
    def query_9_career_paths(self):
        """
        COMPLEXITY: Multiple pattern matching + multi-criteria scoring
        Show all possible career paths (internships) ranked by feasibility
        """
        
        query = """
        MATCH (s:Student {id: 'S005'})
        
        // Get student's skills
        MATCH (s)-[has:HAS_SKILL]->(student_skill:Skill)
        WITH s, collect({skill: student_skill, level: has.proficiency}) AS student_skills
        
        // Get all internships with requirements
        MATCH (i:Internship)-[r:REQUIRES]->(req_skill:Skill)
        
        WITH s, i, student_skills,
             collect({
                 skill: req_skill, 
                 min_level: r.min_proficiency,
                 is_mandatory: r.is_mandatory
             }) AS internship_requirements
        
        // Calculate match scores
        WITH s, i, student_skills, internship_requirements,
             [req IN internship_requirements WHERE 
              any(ss IN student_skills WHERE ss.skill = req.skill 
                  AND ss.level >= req.min_level)] AS met_requirements,
             [req IN internship_requirements WHERE req.is_mandatory = true] AS mandatory_reqs,
             [req IN internship_requirements WHERE 
              req.is_mandatory = true AND
              any(ss IN student_skills WHERE ss.skill = req.skill 
                  AND ss.level >= req.min_level)] AS met_mandatory
        
        // Calculate percentages
        WITH s, i, student_skills, internship_requirements,
             met_requirements, mandatory_reqs, met_mandatory,
             size(met_requirements) * 100.0 / size(internship_requirements) AS overall_match,
             CASE 
                 WHEN size(mandatory_reqs) = 0 THEN 100.0
                 ELSE size(met_mandatory) * 100.0 / size(mandatory_reqs)
             END AS mandatory_match
        
        // Find skill gaps
        WITH s, i, overall_match, mandatory_match, internship_requirements, student_skills,
             [req IN internship_requirements WHERE
              NOT any(ss IN student_skills WHERE ss.skill = req.skill 
                      AND ss.level >= req.min_level)] AS gaps
        
        // Calculate years of experience equivalent
        MATCH (s)-[:COMPLETED]->(p:Project)
        WITH s, i, overall_match, mandatory_match, gaps,
             count(p) AS projects_completed,
             CASE 
                 WHEN count(p) >= 5 THEN 2
                 WHEN count(p) >= 3 THEN 1
                 ELSE 0
             END AS experience_years
        
        // Final scoring - FIX: Move CASE to WITH clause
        WITH s, i, overall_match, mandatory_match, gaps, projects_completed, experience_years,
             (overall_match * 0.4 + mandatory_match * 0.4 + 
              projects_completed * 3 + experience_years * 5) AS final_score,
             CASE 
                 WHEN mandatory_match >= 100 AND overall_match >= 80 THEN 'Ready to Apply ✅'
                 WHEN mandatory_match >= 100 AND overall_match >= 60 THEN 'Apply with Prep 📚'
                 WHEN mandatory_match >= 80 THEN 'Close - Upskill First 🎯'
                 WHEN overall_match >= 40 THEN 'Future Opportunity 🔮'
                 ELSE 'Not Suitable Yet ⏸️'
             END AS recommendation
        
        RETURN i.company AS company,
               i.role AS role,
               i.location AS location,
               i.type AS internship_type,
               round(overall_match, 1) AS overall_match_percent,
               round(mandatory_match, 1) AS mandatory_skills_percent,
               size(gaps) AS missing_skills_count,
               [g IN gaps | g.skill.name] AS skills_to_develop,
               projects_completed,
               experience_years AS equivalent_years_experience,
               round(final_score, 2) AS readiness_score,
               recommendation
        ORDER BY final_score DESC, mandatory_match DESC
        LIMIT 10
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            results = [dict(record) for record in result]
            
            self.print_results(
                "Career Path Analysis - Personalized Internship Ranking",
                "Multi-criteria scoring: skill match, project experience, and readiness",
                results,
                9
            )
            
            return results
    
    # QUERY 10: Skill cluster discovery
    def query_10_skill_clusters(self):
        """
        COMPLEXITY: Graph algorithms + community detection pattern
        Identify clusters of skills frequently learned/used together
        """
        
        query = """
        // Find skills co-occurring in courses
        MATCH (c:Course)-[:TEACHES]->(s1:Skill)
        MATCH (c)-[:TEACHES]->(s2:Skill)
        WHERE id(s1) < id(s2)
        
        WITH s1, s2, count(DISTINCT c) AS course_cooccurrence
        
        // Find skills co-occurring in projects
        MATCH (p:Project)-[:REQUIRES]->(s1)
        MATCH (p)-[:REQUIRES]->(s2)
        
        WITH s1, s2, course_cooccurrence, count(DISTINCT p) AS project_cooccurrence
        
        // Find skills held together by students
        MATCH (student:Student)-[:HAS_SKILL]->(s1)
        MATCH (student)-[:HAS_SKILL]->(s2)
        
        WITH s1, s2, course_cooccurrence, project_cooccurrence,
             count(DISTINCT student) AS student_cooccurrence
        
        // Calculate cluster strength
        WITH s1, s2, 
             course_cooccurrence, 
             project_cooccurrence,
             student_cooccurrence,
             (course_cooccurrence * 3 + project_cooccurrence * 2 + 
              student_cooccurrence * 1) AS cluster_strength
        
        WHERE cluster_strength >= 5
        
        // Group into clusters (simplified - by category similarity)
        WITH s1, s2, course_cooccurrence, project_cooccurrence, 
             student_cooccurrence, cluster_strength,
             CASE 
                 WHEN s1.category = s2.category THEN 'Same Domain'
                 WHEN s1.category IN ['Programming', 'Web Development'] 
                      AND s2.category IN ['Programming', 'Web Development'] THEN 'Development'
                 WHEN s1.category IN ['AI/ML', 'Analytics'] 
                      AND s2.category IN ['AI/ML', 'Analytics'] THEN 'Data Science'
                 WHEN s1.category IN ['Cloud', 'DevOps'] 
                      AND s2.category IN ['Cloud', 'DevOps'] THEN 'Infrastructure'
                 ELSE 'Cross-Domain'
             END AS cluster_type
        
        RETURN s1.name AS skill_1,
               s1.category AS category_1,
               s2.name AS skill_2,
               s2.category AS category_2,
               cluster_type,
               course_cooccurrence AS courses_together,
               project_cooccurrence AS projects_together,
               student_cooccurrence AS students_with_both,
               cluster_strength,
               CASE 
                   WHEN cluster_strength >= 15 THEN 'Very Strong'
                   WHEN cluster_strength >= 10 THEN 'Strong'
                   WHEN cluster_strength >= 5 THEN 'Moderate'
                   ELSE 'Weak'
               END AS relationship_strength
        ORDER BY cluster_strength DESC
        LIMIT 15
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            results = [dict(record) for record in result]
            
            self.print_results(
                "Skill Cluster Discovery",
                "Identify skills that are frequently learned and used together",
                results,
                10
            )
            
            return results
    
    # QUERY 11: Success prediction
    def query_11_predict_success(self):
        """
        COMPLEXITY: Predictive scoring + historical pattern analysis
        Predict likelihood of student success in internship based on patterns
        """
        
        query = """
        MATCH (s:Student {id: 'S001'})
        MATCH (i:Internship {id: 'I004'})
        
        // Get student profile
        MATCH (s)-[has:HAS_SKILL]->(s_skill:Skill)
        WITH s, i, 
             avg(has.proficiency) AS avg_student_skill_level,
             collect({skill: s_skill.name, level: has.proficiency, 
                     verified: has.verified}) AS student_profile,
             count(s_skill) AS total_skills
        
        // Get internship requirements
        MATCH (i)-[req:REQUIRES]->(i_skill:Skill)
        WITH s, i, avg_student_skill_level, student_profile, total_skills,
             avg(req.min_proficiency) AS avg_required_level,
             count(i_skill) AS required_skills_count,
             collect({skill: i_skill.name, required: req.min_proficiency}) AS internship_profile
        
        // Check GPA factor
        WITH s, i, avg_student_skill_level, avg_required_level, 
             student_profile, internship_profile, total_skills, required_skills_count,
             CASE 
                 WHEN s.gpa >= 3.8 THEN 1.2
                 WHEN s.gpa >= 3.5 THEN 1.1
                 WHEN s.gpa >= 3.0 THEN 1.0
                 ELSE 0.8
             END AS gpa_factor
        
        // Check project experience
        MATCH (s)-[:COMPLETED]->(p:Project)
        OPTIONAL MATCH (p)-[:REQUIRES]->(i_skill:Skill)<-[:REQUIRES]-(i)
        
        WITH s, i, avg_student_skill_level, avg_required_level, 
             student_profile, internship_profile, total_skills, 
             required_skills_count, gpa_factor,
             count(DISTINCT p) AS total_projects,
             count(DISTINCT i_skill) AS relevant_projects_count
        
        // Find similar successful students (simplified pattern)
        OPTIONAL MATCH (similar:Student)-[:HAS_SKILL]->(skill:Skill)<-[:REQUIRES]-(similar_internship:Internship)
        WHERE similar <> s 
        AND similar_internship.company = i.company
        AND similar.major = s.major
        
        WITH s, i, avg_student_skill_level, avg_required_level, 
             student_profile, total_skills, required_skills_count, gpa_factor,
             total_projects, relevant_projects_count,
             count(DISTINCT similar) AS similar_success_count
        
        // Calculate base probability from skill levels
        WITH s, i, student_profile, total_skills, required_skills_count,
             gpa_factor, total_projects, relevant_projects_count, 
             similar_success_count,
             CASE 
                 WHEN avg_student_skill_level >= avg_required_level + 2 THEN 0.95
                 WHEN avg_student_skill_level >= avg_required_level + 1 THEN 0.85
                 WHEN avg_student_skill_level >= avg_required_level THEN 0.70
                 WHEN avg_student_skill_level >= avg_required_level - 1 THEN 0.50
                 ELSE 0.30
             END AS base_probability
        
        // Apply multipliers
        WITH s, i, student_profile, total_skills, required_skills_count,
             total_projects, relevant_projects_count, similar_success_count,
             base_probability * gpa_factor AS skill_gpa_score,
             CASE 
                 WHEN relevant_projects_count >= 2 THEN 1.15
                 WHEN relevant_projects_count >= 1 THEN 1.08
                 ELSE 1.0
             END AS project_bonus,
             CASE 
                 WHEN similar_success_count >= 3 THEN 1.1
                 WHEN similar_success_count >= 1 THEN 1.05
                 ELSE 1.0
             END AS pattern_bonus
        
        // Calculate final probability
        WITH s, i, student_profile, total_skills, required_skills_count,
             total_projects, relevant_projects_count, similar_success_count,
             skill_gpa_score * project_bonus * pattern_bonus AS final_probability
        
        // Cap at 0.99
        WITH s, i, student_profile, total_skills, required_skills_count,
             total_projects, relevant_projects_count, similar_success_count,
             CASE WHEN final_probability > 0.99 THEN 0.99 ELSE final_probability END AS capped_probability
        
        RETURN s.name AS student,
               s.major AS major,
               s.gpa AS gpa,
               i.company AS company,
               i.role AS role,
               total_skills AS student_total_skills,
               required_skills_count AS internship_required_skills,
               total_projects AS total_projects_completed,
               relevant_projects_count AS relevant_projects,
               similar_success_count AS similar_students_succeeded,
               round(capped_probability * 100, 1) AS success_probability_percent,
               CASE 
                   WHEN capped_probability >= 0.85 THEN 'Highly Likely to Succeed 🌟'
                   WHEN capped_probability >= 0.70 THEN 'Likely to Succeed ✅'
                   WHEN capped_probability >= 0.50 THEN 'Moderate Chance ⚖️'
                   WHEN capped_probability >= 0.30 THEN 'Challenging 📈'
                   ELSE 'High Risk ⚠️'
               END AS prediction,
               CASE 
                   WHEN capped_probability >= 0.70 THEN 'Apply now with confidence'
                   WHEN capped_probability >= 0.50 THEN 'Apply but prepare thoroughly'
                   ELSE 'Build more skills before applying'
               END AS recommendation
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            results = [dict(record) for record in result]
            
            self.print_results(
                "Internship Success Prediction",
                "Predictive model based on skills, GPA, projects, and historical patterns",
                results,
                11
            )
            
            return results
    
    # QUERY 12: Comprehensive student recommendation engine - FIXED
    def query_12_comprehensive_recommendations(self):
        """
        COMPLEXITY: Multi-factor recommendation combining multiple graph patterns
        Generate personalized recommendations: courses, projects, and internships
        """
        
        query = """
        MATCH (s:Student {id: 'S003'})
        
        // === COURSE RECOMMENDATIONS ===
        // Find skills student doesn't have but are trending
        MATCH (trending_internship:Internship)-[:REQUIRES]->(trending_skill:Skill)
        WHERE NOT (s)-[:HAS_SKILL]->(trending_skill)
        WITH s, trending_skill, count(DISTINCT trending_internship) AS demand
        ORDER BY demand DESC
        LIMIT 3
        
        WITH s, collect(trending_skill) AS needed_skills
        
        MATCH (c:Course)-[:TEACHES]->(needed_skill:Skill)
        WHERE needed_skill IN needed_skills
        AND NOT (s)-[:COMPLETED]->(c)
        AND NOT (s)-[:ENROLLED_IN]->(c)
        
        WITH s, needed_skills, c, count(needed_skill) AS skills_covered
        ORDER BY skills_covered DESC
        LIMIT 3
        
        WITH s, needed_skills,
             collect({
                 course: c.name,
                 code: c.code,
                 credits: c.credits,
                 skills_covered: skills_covered
             }) AS course_recommendations
        
        // === PROJECT RECOMMENDATIONS ===
        MATCH (s)-[has:HAS_SKILL]->(s_skill:Skill)
        WITH s, needed_skills, course_recommendations,
             collect({skill: s_skill, proficiency: has.proficiency}) AS student_skills
        
        // FIX: Extract skills properly before matching
        WITH s, needed_skills, course_recommendations, student_skills,
             [ss IN student_skills | ss.skill] AS student_skill_list
        
        MATCH (p:Project)-[req:REQUIRES]->(p_skill:Skill)
        WHERE p_skill IN student_skill_list
        AND NOT (s)-[:COMPLETED]->(p)
        
        WITH s, needed_skills, course_recommendations, student_skills, p,
             count(p_skill) AS matching_skills,
             avg(req.min_proficiency) AS avg_difficulty
        
        // Check if student's skill level meets project requirements
        WITH s, needed_skills, course_recommendations, student_skills, p, 
             matching_skills, avg_difficulty,
             [ss IN student_skills WHERE ss.proficiency >= avg_difficulty] AS qualified_skills
        
        WHERE size(qualified_skills) >= 1
        
        WITH s, needed_skills, course_recommendations,
             collect({
                 project: p.title,
                 difficulty: p.difficulty,
                 type: p.type,
                 matching_skills: matching_skills
             }) AS project_recommendations
        ORDER BY size(project_recommendations) DESC
        LIMIT 3
        
        // === INTERNSHIP RECOMMENDATIONS ===
        MATCH (s)-[has:HAS_SKILL]->(s_skill:Skill)
        WITH s, needed_skills, course_recommendations, project_recommendations,
             collect(s_skill) AS student_skill_list
        
        MATCH (i:Internship)-[req:REQUIRES]->(i_skill:Skill)
        WHERE i_skill IN student_skill_list
        
        WITH s, needed_skills, course_recommendations, project_recommendations,
             i, count(i_skill) AS matching_skills_count,
             collect(i_skill) AS matching_skills
        
        // Calculate match percentage
        MATCH (i)-[:REQUIRES]->(all_i_skills:Skill)
        WITH s, needed_skills, course_recommendations, project_recommendations,
             i, matching_skills_count, matching_skills,
             count(all_i_skills) AS total_required,
             matching_skills_count * 100.0 / count(all_i_skills) AS match_percent
        
        WHERE match_percent >= 50
        
        WITH s, needed_skills, course_recommendations, project_recommendations,
             collect({
                 company: i.company,
                 role: i.role,
                 location: i.location,
                 match_percent: round(match_percent, 1)
             }) AS internship_recommendations
        ORDER BY size(internship_recommendations) DESC
        LIMIT 5
        
        // === FINAL COMPREHENSIVE REPORT ===
        RETURN s.name AS student_name,
               s.major AS major,
               s.year AS current_year,
               s.gpa AS gpa,
               [ns IN needed_skills | ns.name] AS skills_to_acquire,
               course_recommendations AS recommended_courses,
               project_recommendations AS recommended_projects,
               internship_recommendations AS matching_internships,
               size(course_recommendations) AS courses_count,
               size(project_recommendations) AS projects_count,
               size(internship_recommendations) AS internships_count,
               CASE 
                   WHEN s.year = 4 THEN 'Focus on internship applications'
                   WHEN s.year = 3 THEN 'Balance courses and projects'
                   WHEN s.year = 2 THEN 'Build foundational skills'
                   ELSE 'Explore different areas'
               END AS strategy
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            results = [dict(record) for record in result]
            
            self.print_results(
                "Comprehensive Personalized Recommendations",
                "Complete recommendation engine: courses, projects, and internships based on student profile",
                results,
                12
            )
            
            return results
    
    def run_all_queries(self):
        """Execute all 12 complex queries"""
        print("\n" + "="*70)
        print("🚀 EXECUTING 12 COMPLEX QUERIES")
        print("="*70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        queries = [
            self.query_1_eligible_students,
            self.query_2_skill_gap_analysis,
            self.query_3_recommend_courses,
            self.query_4_similar_students,
            self.query_5_learning_path,
            self.query_6_trending_skills,
            self.query_7_students_by_projects,
            self.query_8_course_effectiveness,
            self.query_9_career_paths,
            self.query_10_skill_clusters,
            self.query_11_predict_success,
            self.query_12_comprehensive_recommendations
        ]
        
        results_summary = []
        
        for i, query_func in enumerate(queries, 1):
            try:
                print(f"\n\n{'='*70}")
                print(f"Executing Query {i}/12...")
                print(f"{'='*70}")
                
                result = query_func()
                results_summary.append({
                    'query_number': i,
                    'status': 'SUCCESS',
                    'results_count': len(result) if result else 0
                })
                
            except Exception as e:
                print(f"\n❌ Error in Query {i}: {e}")
                results_summary.append({
                    'query_number': i,
                    'status': 'FAILED',
                    'error': str(e)
                })
        
        # Print summary
        print("\n\n" + "="*70)
        print("📊 EXECUTION SUMMARY")
        print("="*70)
        
        for summary in results_summary:
            status_icon = "✅" if summary['status'] == 'SUCCESS' else "❌"
            if summary['status'] == 'SUCCESS':
                print(f"{status_icon} Query {summary['query_number']}: "
                      f"{summary['results_count']} results")
            else:
                print(f"{status_icon} Query {summary['query_number']}: "
                      f"FAILED - {summary.get('error', 'Unknown error')}")
        
        success_count = sum(1 for s in results_summary if s['status'] == 'SUCCESS')
        
        print("\n" + "="*70)
        print(f"✅ Successful Queries: {success_count}/12")
        print(f"❌ Failed Queries: {12 - success_count}/12")
        print("="*70)
        
        if success_count == 12:
            print("\n🎉 ALL QUERIES EXECUTED SUCCESSFULLY!")
        else:
            print("\n⚠️  Some queries failed. Review errors above.")
        
        print("\n")


if __name__ == "__main__":
    queries = ComplexQueries()
    
    try:
        queries.run_all_queries()
    except KeyboardInterrupt:
        print("\n\n⚠️  Execution interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
    finally:
        queries.close()