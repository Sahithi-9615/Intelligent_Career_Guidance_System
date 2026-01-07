import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import json
import time

# Import our existing services
from ai_service import AIService
from recommender import RecommendationEngine

# Page configuration
st.set_page_config(
    page_title="Academic Skill Graph Recommender",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment
load_dotenv()

# Initialize services
@st.cache_resource
def init_services():
    """Initialize AI and Recommendation services (cached)"""
    ai = AIService()
    recommender = RecommendationEngine()
    return ai, recommender

ai_service, recommender = init_services()

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .query-box {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1E88E5;
        margin: 1rem 0;
    }
    .success-box {
        background: #d4edda;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
    }
    .complex-query-section {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
    }
    .manual-query-section {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        margin-top: 1.5rem;
    }
    </style>
""", unsafe_allow_html=True)


def get_database_stats():
    """Get database statistics"""
    stats = {}
    
    with recommender.driver.session() as session:
        # Count nodes
        result = session.run("""
            MATCH (n)
            RETURN labels(n)[0] as label, count(n) as count
        """)
        for record in result:
            label = record["label"]
            if label:
                stats[label] = record["count"]
        
        # Count relationships
        result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
        stats["Relationships"] = result.single()["count"]
    
    return stats


def show_entity_data(entity_type):
    """Show data for clicked entity button"""
    st.markdown(f"### 📊 {entity_type} Data")
    
    queries = {
        "Student": """
            MATCH (s:Student)
            RETURN s.id as ID, s.name as Name, s.major as Major, 
                   s.year as Year, s.gpa as GPA, s.email as Email
            ORDER BY s.name
        """,
        "Skill": """
            MATCH (sk:Skill)
            RETURN sk.id as ID, sk.name as Name, sk.category as Category, 
                   sk.level as Level, sk.description as Description
            ORDER BY sk.category, sk.name
        """,
        "Course": """
            MATCH (c:Course)
            RETURN c.id as ID, c.name as Name, c.code as Code, 
                   c.credits as Credits, c.department as Department, 
                   c.difficulty as Difficulty
            ORDER BY c.department, c.name
        """,
        "Project": """
            MATCH (p:Project)
            RETURN p.id as ID, p.title as Title, p.difficulty as Difficulty,
                   p.duration_weeks as Duration_Weeks, p.type as Type
            ORDER BY p.difficulty, p.title
        """,
        "Internship": """
            MATCH (i:Internship)
            RETURN i.id as ID, i.company as Company, i.role as Role,
                   i.location as Location, i.duration_months as Duration_Months,
                   i.type as Type
            ORDER BY i.company
        """
    }
    
    query = queries.get(entity_type)
    
    if query:
        with recommender.driver.session() as session:
            result = session.run(query)
            data = [dict(record) for record in result]
            
            if data:
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True, height=500)
                
                # Download button
                csv = df.to_csv(index=False)
                st.download_button(
                    label=f"📥 Download {entity_type} Data",
                    data=csv,
                    file_name=f"{entity_type.lower()}_data.csv",
                    mime="text/csv"
                )
            else:
                st.info(f"No {entity_type} data found")


def show_dashboard():
    """Display dashboard with statistics"""
    st.markdown('<p class="main-header">🎓 Academic Skill Graph Recommender</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Career Guidance System using Graph Database</p>', unsafe_allow_html=True)
    
    # Get statistics
    stats = get_database_stats()
    
    # Display stats in columns
    st.markdown("### 📊 Database Overview")
    st.markdown("*Click on any card to view detailed data*")
    
    cols = st.columns(5)
    
    stat_configs = [
        ("Student", "👨‍🎓", "#667eea"),
        ("Skill", "💡", "#f093fb"),
        ("Course", "📚", "#4facfe"),
        ("Project", "🚀", "#43e97b"),
        ("Internship", "💼", "#fa709a")
    ]
    
    # Store clicked entity in session state
    if 'clicked_entity' not in st.session_state:
        st.session_state.clicked_entity = None
    
    for col, (label, emoji, color) in zip(cols, stat_configs):
        count = stats.get(label, 0)
        with col:
            if st.button(f"{emoji}\n\n{count}\n\n{label}s", key=f"btn_{label}", use_container_width=True):
                st.session_state.clicked_entity = label
    
    st.markdown("---")
    
    # Show entity data if button clicked
    if st.session_state.clicked_entity:
        show_entity_data(st.session_state.clicked_entity)
        if st.button("← Back to Dashboard"):
            st.session_state.clicked_entity = None
            st.rerun()

def get_complex_query_mapping():
    """Returns mapping of complex query descriptions to actual Cypher queries with REAL data"""
    return {
        "🎯 Recommend courses for Alice Johnson to qualify for Google Software Engineering Intern": """
            // Find skills required by Google SWE internship that Alice lacks or is weak in
            MATCH (i:Internship {id: 'I001'})-[r:REQUIRES]->(needed:Skill)
            OPTIONAL MATCH (s:Student {id: 'S001'})-[has:HAS_SKILL]->(needed)
            WHERE has IS NULL OR has.proficiency < r.min_proficiency
            
            WITH s, i, needed, r.min_proficiency as required_level, 
                 COALESCE(has.proficiency, 0) as current_level
            
            // Find courses that teach these missing skills
            MATCH (c:Course)-[teaches:TEACHES]->(needed)
            WHERE NOT (s)-[:COMPLETED]->(c) AND NOT (s)-[:ENROLLED_IN]->(c)
            
            WITH c, needed, required_level, current_level,
                 (required_level - current_level) as skill_gap
            ORDER BY skill_gap DESC
            
            RETURN DISTINCT
                c.name as Course,
                c.code as Code,
                c.credits as Credits,
                c.difficulty as Difficulty,
                collect(DISTINCT needed.name)[0..3] as Teaches_Critical_Skills,
                round(avg(skill_gap), 1) as Avg_Skill_Gap_Filled
            ORDER BY Avg_Skill_Gap_Filled DESC
            LIMIT 5
        """,
        
        "💼 Recommend top internships for Bob Smith based on his current skill match": """
            MATCH (s:Student {id: 'S002'})-[has:HAS_SKILL]->(skill:Skill)
            WITH s, collect({skill: skill, level: has.proficiency}) as student_skills
            
            MATCH (i:Internship)-[r:REQUIRES]->(req_skill:Skill)
            
            WITH s, i, student_skills,
                 collect({skill: req_skill, min_level: r.min_proficiency, 
                         mandatory: r.is_mandatory}) as requirements
            
            WITH s, i, student_skills, requirements,
                 [req IN requirements WHERE 
                  any(ss IN student_skills WHERE ss.skill = req.skill 
                      AND ss.level >= req.min_level)] as met_requirements
            
            WITH i, requirements, met_requirements,
                 size(met_requirements) * 100.0 / size(requirements) as match_percent,
                 [mr IN met_requirements | mr.skill.name] as matched_skills,
                 [req IN requirements WHERE NOT req IN met_requirements | req.skill.name] as missing_skills
            
            WHERE match_percent >= 30
            
            RETURN i.company as Company,
                   i.role as Role,
                   i.location as Location,
                   i.type as Type,
                   round(match_percent, 1) as Match_Percent,
                   size(matched_skills) as Skills_Matched,
                   size(missing_skills) as Skills_Gap
            ORDER BY match_percent DESC
            LIMIT 8
        """,
        
        "📊 Show all missing skills for Carol White to qualify for Microsoft Cloud Engineer Intern": """
            MATCH (s:Student {id: 'S003'})
            MATCH (i:Internship {id: 'I003'})-[r:REQUIRES]->(skill:Skill)
            
            OPTIONAL MATCH (s)-[has:HAS_SKILL]->(skill)
            
            WITH s, i, skill, r.min_proficiency as required,
                 COALESCE(has.proficiency, 0) as current,
                 r.is_mandatory as mandatory
            
            WHERE current < required
            
            RETURN skill.name as Skill,
                   skill.category as Category,
                   required as Required_Level,
                   current as Current_Level,
                   (required - current) as Gap,
                   CASE WHEN mandatory THEN 'Yes' ELSE 'No' END as Mandatory,
                   CASE 
                       WHEN current = 0 THEN 'Missing'
                       WHEN current < required THEN 'Weak'
                       ELSE 'Sufficient'
                   END as Status
            ORDER BY mandatory DESC, Gap DESC
        """,
        
        "🏆 Find students who completed Python (C001) course and qualify for Google or Amazon internships": """
            // Find students who completed Introduction to Python
            MATCH (s:Student)-[comp:COMPLETED]->(c:Course {id: 'C001'})
            
            // Get their current skills
            MATCH (s)-[has:HAS_SKILL]->(skill:Skill)
            WITH s, comp, collect({skill: skill.name, level: has.proficiency}) as student_skills
            
            // Check qualification for Google or Amazon internships
            MATCH (i:Internship)-[r:REQUIRES]->(req_skill:Skill)
            WHERE i.company IN ['Google', 'Amazon']
            
            WITH s, comp, student_skills, i,
                 collect({skill: req_skill.name, min_prof: r.min_proficiency}) as requirements
            
            // Calculate match percentage
            WITH s, comp, student_skills, i, requirements,
                 size([req IN requirements WHERE 
                      any(ss IN student_skills WHERE ss.skill = req.skill 
                          AND ss.level >= req.min_prof)]) * 100.0 / size(requirements) as match_pct
            
            WHERE match_pct >= 50
            
            WITH s, comp, 
                 collect({company: i.company, role: i.role, match: round(match_pct, 1)}) as qualified_internships
            
            WHERE size(qualified_internships) > 0
            
            RETURN s.name as Student,
                   s.major as Major,
                   s.gpa as GPA,
                   comp.grade as Python_Grade,
                   comp.semester as Semester,
                   [qi IN qualified_internships | qi.company + ' - ' + qi.role + ' (' + toString(qi.match) + '%)'] as Qualified_Internships
            ORDER BY s.gpa DESC
        """,
        
        "📚 Which courses teach the most in-demand skills across all internships?": """
            // Find skills most demanded by internships
            MATCH (i:Internship)-[r:REQUIRES]->(skill:Skill)
            WITH skill, count(DISTINCT i) as internship_demand, 
                 avg(r.min_proficiency) as avg_required_level
            ORDER BY internship_demand DESC
            
            // Find courses teaching these high-demand skills
            MATCH (c:Course)-[teaches:TEACHES]->(skill)
            
            WITH c, skill, internship_demand, teaches.depth as teaching_depth
            
            RETURN c.name as Course,
                   c.code as Code,
                   c.difficulty as Difficulty,
                   collect(DISTINCT skill.name) as High_Demand_Skills,
                   round(avg(internship_demand), 1) as Avg_Internship_Demand,
                   count(DISTINCT skill) as Num_Valuable_Skills
            ORDER BY Avg_Internship_Demand DESC, Num_Valuable_Skills DESC
            LIMIT 10
        """,
        
        "🔍 Find students with Python proficiency >= 8 who haven't taken Machine Learning Basics (C002)": """
            MATCH (s:Student)-[has:HAS_SKILL]->(python:Skill {id: 'SK001'})
            WHERE has.proficiency >= 8
            
            // Check they haven't taken Machine Learning Basics course
            MATCH (ml_course:Course {id: 'C002'})
            WHERE NOT (s)-[:COMPLETED|ENROLLED_IN]->(ml_course)
            
            WITH DISTINCT s, has.proficiency as python_level
            
            // Get their other AI/ML and Data Science skills
            OPTIONAL MATCH (s)-[other_has:HAS_SKILL]->(other_skill:Skill)
            WHERE other_skill.category IN ['AI/ML', 'Data Science']
            
            RETURN s.name as Student,
                   s.major as Major,
                   s.year as Year,
                   python_level as Python_Proficiency,
                   collect(DISTINCT other_skill.name) as Other_Data_Skills,
                   s.gpa as GPA
            ORDER BY python_level DESC, s.gpa DESC
        """,
        
        "💡 Find students who completed Web Development (C004) course and analyze their project readiness": """
            // Find students who completed Web Development course
            MATCH (s:Student)-[comp:COMPLETED]->(c:Course {id: 'C004'})
            
            // Get skills they learned from this course
            MATCH (c)-[:TEACHES]->(course_skill:Skill)
            WITH s, comp, collect(DISTINCT course_skill.name) as skills_from_course
            
            // Get their current skill levels in web-related areas
            MATCH (s)-[has:HAS_SKILL]->(skill:Skill)
            WHERE skill.category IN ['Web Development', 'Programming']
            WITH s, comp, skills_from_course,
                 collect({skill: skill.name, level: has.proficiency}) as current_skills
            
            // Find web development projects they could work on
            MATCH (p:Project)-[:REQUIRES]->(proj_skill:Skill)
            WHERE proj_skill.category = 'Web Development'
            
            WITH s, comp, skills_from_course, current_skills, p,
                 collect({skill: proj_skill.name, min_prof: 
                         CASE WHEN exists((p)-[:REQUIRES {min_proficiency: proj_skill}]->()) 
                         THEN 6 ELSE 5 END}) as project_requirements
            
            // Calculate readiness for each project
            WITH s, comp, skills_from_course, current_skills, p, project_requirements,
                 size([req IN project_requirements WHERE 
                      any(cs IN current_skills WHERE cs.skill = req.skill 
                          AND cs.level >= 5)]) as skills_ready,
                 size(project_requirements) as total_required
            
            WHERE skills_ready > 0
            
            WITH s, comp, skills_from_course, current_skills,
                 collect({project: p.title, difficulty: p.difficulty,
                         readiness: round((skills_ready * 100.0 / total_required), 1)}) as available_projects
            
            RETURN s.name as Student,
                   s.major as Major,
                   s.gpa as GPA,
                   comp.grade as Web_Dev_Course_Grade,
                   size(current_skills) as Total_Web_Skills,
                   [cs IN current_skills | cs.skill + '(' + toString(cs.level) + ')'] as Current_Web_Skills,
                   [ap IN available_projects WHERE ap.readiness >= 50 | 
                    ap.project + ' - ' + toString(ap.readiness) + '% ready'] as Ready_For_Projects
            ORDER BY size([ap IN available_projects WHERE ap.readiness >= 70]) DESC, s.gpa DESC
        """,
        
        "🎓 Recommend a learning path for David Brown targeting Meta Frontend Developer Intern": """
            // Target: Meta Frontend Developer Internship
            MATCH (target_i:Internship {id: 'I004'})
            
            // Get required skills
            MATCH (target_i)-[r:REQUIRES]->(needed:Skill)
            
            // Find David Brown's current skill levels
            MATCH (s:Student {id: 'S004'})
            OPTIONAL MATCH (s)-[has:HAS_SKILL]->(needed)
            
            WITH s, needed, r.min_proficiency as required,
                 COALESCE(has.proficiency, 0) as current,
                 (r.min_proficiency - COALESCE(has.proficiency, 0)) as gap
            WHERE gap > 0
            
            // Find courses teaching these skills
            MATCH (c:Course)-[teaches:TEACHES]->(needed)
            WHERE NOT (s)-[:COMPLETED|ENROLLED_IN]->(c)
            
            WITH c, needed, gap, teaches.depth as depth,
                 CASE c.difficulty
                     WHEN 'Beginner' THEN 1
                     WHEN 'Intermediate' THEN 2
                     WHEN 'Advanced' THEN 3
                     ELSE 2
                 END as difficulty_order
            
            RETURN c.name as Course,
                   c.code as Code,
                   c.difficulty as Difficulty,
                   collect(DISTINCT needed.name) as Skills_Covered,
                   round(avg(gap), 1) as Avg_Skill_Gap_Filled,
                   difficulty_order as Recommended_Order
            ORDER BY difficulty_order, Avg_Skill_Gap_Filled DESC
            LIMIT 6
        """,
        
        "🌟 Find students who completed projects, their project skills, and matching internship opportunities": """
            // Find students who completed projects
            MATCH (s:Student)-[comp:COMPLETED]->(p:Project)
            
            // Get skills required by the projects they completed
            MATCH (p)-[:REQUIRES]->(proj_skill:Skill)
            
            WITH s, 
                 collect(DISTINCT {project: p.title, difficulty: p.difficulty, 
                         grade: comp.grade, role: comp.role}) as projects,
                 collect(DISTINCT proj_skill) as skills_from_projects
            
            // Find internships that require these project skills
            MATCH (i:Internship)-[r:REQUIRES]->(int_skill:Skill)
            WHERE int_skill IN skills_from_projects
            
            WITH s, projects, skills_from_projects, i,
                 collect(DISTINCT int_skill.name) as matching_skills
            
            // Get total skills required by internship
            MATCH (i)-[:REQUIRES]->(all_int_skills:Skill)
            WITH s, projects, i, matching_skills,
                 count(DISTINCT all_int_skills) as total_int_skills
            
            // Calculate match percentage
            WITH s, projects, i, matching_skills, total_int_skills,
                 round((size(matching_skills) * 100.0 / total_int_skills), 1) as match_percentage
            
            WHERE match_percentage >= 40
            
            WITH s, projects,
                 collect({company: i.company, role: i.role, match: match_percentage, 
                         skills: matching_skills}) as matching_internships
            
            RETURN s.name as Student,
                   s.major as Major,
                   s.gpa as GPA,
                   size(projects) as Projects_Completed,
                   [p IN projects | p.project + ' (' + p.difficulty + ', Grade: ' + p.grade + ')'] as Project_Details,
                   [mi IN matching_internships | 
                    mi.company + ' - ' + mi.role + ' (' + toString(mi.match) + '% match)'] as Matching_Internships,
                   [mi IN matching_internships | mi.skills][0] as Sample_Matching_Skills
            ORDER BY size(matching_internships) DESC, s.gpa DESC
        """,
        
        "📈 Rank students by readiness for Software Engineering internships (Google, Microsoft, Apple)": """
            // Get Software Engineering internships from top companies
            MATCH (i:Internship)
            WHERE i.company IN ['Google', 'Microsoft', 'Apple']
               AND (i.role CONTAINS 'Software Engineer' OR i.role CONTAINS 'Developer')
            
            // Get all required skills across these internships
            MATCH (i)-[r:REQUIRES]->(skill:Skill)
            
            WITH DISTINCT skill, 
                 avg(r.min_proficiency) as avg_required,
                 count(DISTINCT i) as demand
            
            // For each student, check their proficiency in these skills
            MATCH (s:Student)
            OPTIONAL MATCH (s)-[has:HAS_SKILL]->(skill)
            
            WITH s, skill, avg_required, demand,
                 COALESCE(has.proficiency, 0) as student_level
            
            // Calculate readiness score
            WITH s,
                 sum(CASE WHEN student_level >= avg_required THEN demand ELSE 0 END) as qualified_for,
                 sum(demand) as total_demand,
                 avg(student_level) as avg_skill_level,
                 count(DISTINCT CASE WHEN student_level >= avg_required THEN skill END) as skills_mastered
            
            WITH s, qualified_for, total_demand, avg_skill_level, skills_mastered,
                 round((qualified_for * 100.0 / total_demand), 1) as readiness_score
            
            WHERE readiness_score > 0
            
            RETURN s.name as Student,
                   s.major as Major,
                   s.gpa as GPA,
                   readiness_score as Readiness_Score,
                   skills_mastered as SE_Skills_Mastered,
                   round(avg_skill_level, 1) as Avg_Skill_Level
            ORDER BY readiness_score DESC, s.gpa DESC
            LIMIT 15
        """,
        
        "🔗 Find common skills required by top tech company internships (Google, Amazon, Microsoft, Apple)": """
            // Top tech companies
            MATCH (i:Internship)
            WHERE i.company IN ['Google', 'Amazon', 'Microsoft', 'Apple']
            
            // Get skills they require
            MATCH (i)-[r:REQUIRES]->(skill:Skill)
            
            WITH skill, 
                 collect(DISTINCT i.company) as companies,
                 count(DISTINCT i) as internship_count,
                 avg(r.min_proficiency) as avg_required_level,
                 sum(CASE WHEN r.is_mandatory THEN 1 ELSE 0 END) as mandatory_count
            
            WHERE internship_count >= 2
            
            RETURN skill.name as Skill,
                   skill.category as Category,
                   companies as Tech_Companies,
                   internship_count as Internships_Requiring,
                   round(avg_required_level, 1) as Avg_Required_Level,
                   mandatory_count as Times_Mandatory
            ORDER BY internship_count DESC, mandatory_count DESC, avg_required_level DESC
        """,
        
        "⚡ Suggest next best course for Emma Davis based on completed courses and current skills": """
            MATCH (s:Student {id: 'S005'})
            
            // Get completed courses and current skills
            OPTIONAL MATCH (s)-[:COMPLETED]->(completed:Course)
            OPTIONAL MATCH (s)-[has:HAS_SKILL]->(current_skill:Skill)
            
            WITH s, 
                 collect(DISTINCT completed) as completed_courses,
                 collect({skill: current_skill, level: has.proficiency}) as current_skills
            
            // Find courses not yet taken
            MATCH (c:Course)
            WHERE NOT c IN completed_courses 
              AND NOT (s)-[:ENROLLED_IN]->(c)
            
            // Get skills taught by these courses
            MATCH (c)-[teaches:TEACHES]->(skill:Skill)
            
            WITH s, c, current_skills, 
                 collect({skill: skill, depth: teaches.depth}) as course_skills,
                 CASE c.difficulty
                     WHEN 'Beginner' THEN 1
                     WHEN 'Intermediate' THEN 2
                     WHEN 'Advanced' THEN 3
                     ELSE 2
                 END as difficulty_level
            
            // Calculate relevance: how many new skills vs building on existing
            WITH c, course_skills, current_skills, difficulty_level,
                 size([cs IN course_skills WHERE 
                       any(curr IN current_skills WHERE curr.skill = cs.skill)]) as builds_on_current,
                 size([cs IN course_skills WHERE 
                       NOT any(curr IN current_skills WHERE curr.skill = cs.skill)]) as teaches_new
            
            // Calculate score: prefer courses that build on current skills and teach new ones
            WITH c, difficulty_level, builds_on_current, teaches_new,
                 (builds_on_current * 2 + teaches_new * 3) as relevance_score
            
            WHERE relevance_score > 0
            
            RETURN c.name as Course,
                   c.code as Code,
                   c.difficulty as Difficulty,
                   c.credits as Credits,
                   builds_on_current as Builds_On_Skills,
                   teaches_new as New_Skills,
                   relevance_score as Relevance_Score
            ORDER BY relevance_score DESC, difficulty_level
            LIMIT 8
        """
    }

def execute_and_display_query(query_description, cypher_query, is_manual=False):
    """Execute query and display results"""
    try:
        # Display generated query
        st.markdown("#### 🔍 Generated Cypher Query:")
        st.code(cypher_query, language="cypher")
        
        # Execute query
        with st.spinner("⚙️ Executing query..."):
            result = recommender.execute_query(cypher_query)
        
        if result["success"]:
            if result["data"]:
                # Clean and format the data
                cleaned_data = []
                for record in result["data"]:
                    cleaned_record = {}
                    for key, value in record.items():
                        # Handle Neo4j node objects
                        if hasattr(value, '__class__') and 'Node' in value.__class__.__name__:
                            if hasattr(value, '_properties'):
                                cleaned_record[key] = str(dict(value._properties))
                            else:
                                cleaned_record[key] = str(value)
                        # Handle Neo4j relationship objects
                        elif hasattr(value, '__class__') and 'Relationship' in value.__class__.__name__:
                            if hasattr(value, '_properties'):
                                cleaned_record[key] = str(dict(value._properties))
                            else:
                                cleaned_record[key] = str(value)
                        else:
                            cleaned_record[key] = value
                    cleaned_data.append(cleaned_record)
                
                # Convert to DataFrame
                df = pd.DataFrame(cleaned_data)
                
                # Display results
                st.markdown("#### ✅ Query Results:")
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Show result count
                st.success(f"📊 Found {len(df)} result(s)")
                
                # Download button
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Results as CSV",
                    data=csv,
                    file_name="query_results.csv",
                    mime="text/csv"
                )
            else:
                st.info("ℹ️ Query executed successfully but returned no results.")
        else:
            st.error(f"❌ Query execution failed: {result.get('error', 'Unknown error')}")
            st.info("💡 Tip: The query might need adjustment for your specific data.")
                    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.info("💡 Try a simpler query or check if Neo4j is running.")


def show_natural_query():
    """Natural language query interface with improved UI"""
    st.markdown("### 🤖 Natural Language Query Interface")
    
    # Initialize session state for tracking which query to execute
    if 'execute_query' not in st.session_state:
        st.session_state.execute_query = None
    if 'query_source' not in st.session_state:
        st.session_state.query_source = None
    
    # Complex Queries Section
    st.markdown("#### 💡 Try These Complex Pre-Built Queries")
    
    # Get complex queries mapping
    complex_queries = get_complex_query_mapping()
    query_options = ["-- Select a query to see instant results --"] + list(complex_queries.keys())
    
    selected_complex = st.selectbox(
        "Choose a complex analytical query:",
        query_options,
        key="complex_query_select",
        label_visibility="collapsed"
    )
    
    # Handle complex query selection
    if selected_complex != "-- Select a query to see instant results --":
        if st.session_state.query_source != 'complex' or st.session_state.execute_query != selected_complex:
            st.session_state.execute_query = selected_complex
            st.session_state.query_source = 'complex'
            st.rerun()
    
    # Manual Query Section
    st.markdown("#### ✍️ Or Enter Your Own Query")
    
    manual_query = st.text_input(
        "Type your question in natural language:",
        placeholder="e.g., Show me students who know both Python and Java with proficiency > 7",
        key="manual_query_input",
        label_visibility="collapsed"
    )
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        search_clicked = st.button("🔍 Search", type="primary", use_container_width=True)
    with col2:
        if st.button("🔄 Clear Results", use_container_width=True):
            st.session_state.execute_query = None
            st.session_state.query_source = None
            st.rerun()
    
    # Handle manual query search
    if search_clicked and manual_query:
        st.session_state.execute_query = manual_query
        st.session_state.query_source = 'manual'
        st.rerun()
    elif search_clicked and not manual_query:
        st.warning("⚠️ Please enter a question!")
    
    # Execute the selected query
    if st.session_state.execute_query and st.session_state.query_source:
        if st.session_state.query_source == 'complex':
            # Execute pre-built complex query
            query_desc = st.session_state.execute_query
            cypher_query = complex_queries[query_desc]
            
            st.markdown(f"### 📊 Results for: {query_desc}")
            execute_and_display_query(query_desc, cypher_query, is_manual=False)
            
        elif st.session_state.query_source == 'manual':
            # Generate and execute AI query
            user_question = st.session_state.execute_query
            
            st.markdown(f"### 📊 Results for: *{user_question}*")
            
            with st.spinner("🤖 Generating Cypher query with AI..."):
                try:
                    cypher_query = ai_service.generate_cypher_query(user_question)
                    execute_and_display_query(user_question, cypher_query, is_manual=True)
                except Exception as e:
                    st.error(f"❌ AI query generation failed: {str(e)}")
                    st.info("💡 Try using one of the pre-built complex queries above.")


def show_student_profiles():
    """Student profile viewer"""
    st.markdown("### 👨‍🎓 Student Profiles")
    
    # Get all students
    with recommender.driver.session() as session:
        result = session.run("""
            MATCH (s:Student)
            RETURN s.id as id, s.name as name, s.major as major, 
                   s.year as year, s.gpa as gpa
            ORDER BY s.name
        """)
        students = [dict(record) for record in result]
    
    if students:
        student_names = {s["name"]: s["id"] for s in students}
        
        selected_name = st.selectbox("Select a student:", list(student_names.keys()))
        
        if selected_name:
            student_id = student_names[selected_name]
            
            # Get full profile
            profile_result = recommender.get_student_profile(student_id)
            
            if profile_result["success"] and profile_result["data"]:
                profile = profile_result["data"][0]
                
                # Display profile
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("👤 Name", profile["name"])
                with col2:
                    st.metric("🎓 Major", profile["major"])
                with col3:
                    st.metric("📅 Year", profile["year"])
                with col4:
                    st.metric("⭐ GPA", f"{profile['gpa']:.2f}")
                
                st.markdown("---")
                
                # Skills
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 💡 Skills")
                    if profile["skills"]:
                        skills_df = pd.DataFrame(profile["skills"])
                        
                        # Create skill chart
                        fig = px.bar(
                            skills_df,
                            x="proficiency",
                            y="skill",
                            orientation="h",
                            color="category",
                            title="Skill Proficiency Levels",
                            labels={"proficiency": "Proficiency (1-10)", "skill": "Skill"}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No skills recorded")
                
                with col2:
                    st.markdown("#### 📚 Completed Courses")
                    if profile["completed_courses"]:
                        for course in profile["completed_courses"]:
                            st.write(f"• {course}")
                    else:
                        st.info("No courses completed yet")
                    
                    st.markdown("#### 🚀 Completed Projects")
                    if profile["completed_projects"]:
                        for project in profile["completed_projects"]:
                            st.write(f"• {project}")
                    else:
                        st.info("No projects completed yet")


def show_recommendations():
    """Course and internship recommendations - IMPROVED"""
    st.markdown("### 🎯 Personalized Recommendations")
    
    tab1, tab2 = st.tabs(["📚 Course Recommendations", "💼 Internship Recommendations"])
    
    with tab1:
        st.markdown("#### Course Recommendations")
        st.info("💡 Courses are recommended based on: missing skills for trending internships, skill gaps, and student's current level")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Get all students
            with recommender.driver.session() as session:
                result = session.run("MATCH (s:Student) RETURN s.id as id, s.name as name ORDER BY s.name")
                students = [dict(record) for record in result]
            
            student_names = {s["name"]: s["id"] for s in students}
            selected_student = st.selectbox("Select Student:", [""] + list(student_names.keys()))
        
        with col2:
            skill_input = st.text_input("Or enter skill name:", placeholder="e.g., Python, Machine Learning")
        
        if st.button("Get Course Recommendations", type="primary"):
            student_id = student_names.get(selected_student) if selected_student else None
            
            if student_id:
                # IMPROVED QUERY - Shows WHY course is recommended
                with st.spinner("Analyzing student profile and generating recommendations..."):
                    with recommender.driver.session() as session:
                        result = session.run("""
                            // Get student's current skills
                            MATCH (s:Student {id: $student_id})-[has:HAS_SKILL]->(student_skill:Skill)
                            WITH s, collect({skill: student_skill, prof: has.proficiency}) as current_skills
                            
                            // Find skills needed for internships that student lacks
                            MATCH (i:Internship)-[:REQUIRES]->(needed:Skill)
                            WHERE NOT any(cs IN current_skills WHERE cs.skill = needed AND cs.prof >= 7)
                            
                            WITH s, current_skills, needed, count(i) as demand
                            ORDER BY demand DESC
                            LIMIT 5
                            
                            // Find courses teaching these skills
                            MATCH (c:Course)-[:TEACHES]->(needed)
                            WHERE NOT (s)-[:COMPLETED]->(c)
                            AND NOT (s)-[:ENROLLED_IN]->(c)
                            
                            WITH s, c, needed, demand, current_skills
                            
                            // Get all skills taught by course
                            MATCH (c)-[:TEACHES]->(all_skills:Skill)
                            
                            RETURN DISTINCT 
                                c.name as course,
                                c.code as code,
                                c.credits as credits,
                                c.difficulty as difficulty,
                                collect(DISTINCT needed.name) as fills_skill_gaps,
                                demand as internships_requiring_this,
                                collect(DISTINCT all_skills.name) as all_skills_taught
                            ORDER BY internships_requiring_this DESC, c.difficulty
                            LIMIT 5
                        """, student_id=student_id)
                        
                        recommendations = [dict(record) for record in result]
                
                if recommendations:
                    st.success(f"✅ Found {len(recommendations)} personalized recommendations!")
                    
                    # Show WHY each course is recommended
                    for idx, rec in enumerate(recommendations, 1):
                        with st.expander(f"📚 {idx}. {rec['course']} ({rec['code']})"):
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("Credits", rec['credits'])
                            with col2:
                                st.metric("Difficulty", rec['difficulty'])
                            with col3:
                                st.metric("Internship Demand", rec['internships_requiring_this'])
                            
                            st.markdown("**📊 Why recommended:**")
                            st.write(f"• Fills {len(rec['fills_skill_gaps'])} skill gap(s): **{', '.join(rec['fills_skill_gaps'])}**")
                            st.write(f"• Required by **{rec['internships_requiring_this']}** internships")
                            
                            st.markdown("**💡 All Skills Taught:**")
                            st.write(", ".join(rec['all_skills_taught']))
                else:
                    st.info("Student has strong skill coverage! Consider advanced courses.")
                    
            elif skill_input:
                result = recommender.recommend_courses(skill_name=skill_input)
                
                if result["success"] and result["data"]:
                    st.success(f"✅ Found {result['count']} courses!")
                    df = pd.DataFrame(result["data"])
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No courses found for this skill.")
            else:
                st.warning("Please select a student or enter a skill!")
    
    with tab2:
        st.markdown("#### Internship Recommendations")
        st.info("💡 Internships are matched based on your current skills and proficiency levels")
        
        # Get all students
        with recommender.driver.session() as session:
            result = session.run("MATCH (s:Student) RETURN s.id as id, s.name as name ORDER BY s.name")
            students = [dict(record) for record in result]
        
        student_names = {s["name"]: s["id"] for s in students}
        selected_student = st.selectbox("Select Student for Internship Recommendations:", list(student_names.keys()))
        
        if st.button("Get Internship Recommendations", type="primary"):
            if selected_student:
                student_id = student_names[selected_student]
                
                with st.spinner("Analyzing skills and matching internships..."):
                    # IMPROVED QUERY - Shows WHICH skills matched
                    with recommender.driver.session() as session:
                        result = session.run("""
                            MATCH (s:Student {id: $student_id})-[has:HAS_SKILL]->(student_skill:Skill)
                            WITH s, collect({skill: student_skill, level: has.proficiency}) AS student_skills
                            
                            MATCH (i:Internship)-[r:REQUIRES]->(req_skill:Skill)
                            
                            WITH s, i, student_skills,
                                 collect({skill: req_skill, min_level: r.min_proficiency, 
                                         mandatory: r.is_mandatory}) AS requirements
                            
                            // Find which skills student has that match
                            WITH s, i, student_skills, requirements,
                                 [req IN requirements WHERE 
                                  any(ss IN student_skills WHERE ss.skill = req.skill 
                                      AND ss.level >= req.min_level)] AS met_requirements
                            
                            WITH s, i, requirements, met_requirements,
                                 size(met_requirements) * 100.0 / size(requirements) AS match_percentage,
                                 [mr IN met_requirements | mr.skill.name] as matched_skills,
                                 [req IN requirements WHERE NOT req IN met_requirements | req.skill.name] as missing_skills
                            
                            WHERE match_percentage >= 40
                            
                            RETURN i.company AS company,
                                   i.role AS role,
                                   i.location AS location,
                                   i.type AS internship_type,
                                   round(match_percentage, 1) AS match_percent,
                                   matched_skills,
                                   missing_skills,
                                   size(missing_skills) AS skills_gap_count
                            ORDER BY match_percentage DESC
                            LIMIT 10
                        """, student_id=student_id)
                        
                        internships = [dict(record) for record in result]
                
                if internships:
                    st.success(f"✅ Found {len(internships)} matching internships!")
                    
                    for internship in internships:
                        match_color = "🟢" if internship['match_percent'] >= 80 else "🟡" if internship['match_percent'] >= 60 else "🟠"
                        
                        with st.expander(f"{match_color} {internship['company']} - {internship['role']} ({internship['match_percent']}% match)"):
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("Match Score", f"{internship['match_percent']}%")
                            with col2:
                                st.metric("Location", internship['location'])
                            with col3:
                                st.metric("Type", internship['internship_type'])
                            
                            st.markdown("**✅ Your Matching Skills:**")
                            if internship['matched_skills']:
                                st.success(", ".join(internship['matched_skills']))
                            else:
                                st.info("None yet")
                            
                            st.markdown("**⚠️ Skills You Need to Develop:**")
                            if internship['missing_skills']:
                                st.warning(", ".join(internship['missing_skills']))
                            else:
                                st.success("You have all required skills!")
                else:
                    st.info("No matching internships found. Build more skills!")


def show_skill_gap():
    """Skill gap analysis"""
    st.markdown("### 📊 Skill Gap Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Get students
        with recommender.driver.session() as session:
            result = session.run("MATCH (s:Student) RETURN s.id as id, s.name as name ORDER BY s.name")
            students = [dict(record) for record in result]
        
        student_names = {s["name"]: s["id"] for s in students}
        selected_student = st.selectbox("Select Student:", list(student_names.keys()))
    
    with col2:
        # Get internships
        with recommender.driver.session() as session:
            result = session.run("MATCH (i:Internship) RETURN i.id as id, i.company + ' - ' + i.role as name ORDER BY i.company")
            internships = [dict(record) for record in result]
        
        internship_names = {i["name"]: i["id"] for i in internships}
        selected_internship = st.selectbox("Select Target Internship:", list(internship_names.keys()))
    
    if st.button("Analyze Skill Gap", type="primary"):
        if selected_student and selected_internship:
            student_id = student_names[selected_student]
            internship_id = internship_names[selected_internship]
            
            result = recommender.get_skill_gap(student_id, internship_id)
            
            if result["success"] and result["data"]:
                gaps = result["data"]
                
                # Categorize
                missing = [g for g in gaps if g["status"] == "Missing"]
                weak = [g for g in gaps if g["status"] == "Weak"]
                sufficient = [g for g in gaps if g["status"] == "Sufficient"]
                
                # Readiness score
                readiness = len(sufficient) * 100 / len(gaps) if gaps else 0
                
                # Display readiness
                st.markdown("#### 🎯 Readiness Score")
                
                fig = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=readiness,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Ready to Apply"},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 75], 'color': "yellow"},
                            {'range': [75, 100], 'color': "lightgreen"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 80
                        }
                    }
                ))
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Display gaps
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("#### ❌ Missing Skills")
                    if missing:
                        for skill in missing:
                            st.error(f"**{skill['skill']}** (need: {skill['required']})")
                    else:
                        st.success("No missing skills!")
                
                with col2:
                    st.markdown("#### ⚠️ Weak Skills")
                    if weak:
                        for skill in weak:
                            st.warning(f"**{skill['skill']}**: {skill['current']}/{skill['required']} (gap: {skill['gap']})")
                    else:
                        st.success("No weak skills!")
                
                with col3:
                    st.markdown("#### ✅ Sufficient Skills")
                    if sufficient:
                        for skill in sufficient:
                            st.success(f"**{skill['skill']}**: {skill['current']}/{skill['required']}")
                    else:
                        st.info("Build your skills!")


def show_analytics():
    """Analytics and visualizations"""
    st.markdown("### 📈 Analytics & Insights")
    
    tab1, tab2, tab3 = st.tabs(["Skill Distribution", "Student Performance", "Market Trends"])
    
    with tab1:
        st.markdown("#### Skill Distribution by Category")
        
        with recommender.driver.session() as session:
            result = session.run("""
                MATCH (sk:Skill)
                RETURN sk.category as category, count(sk) as count
                ORDER BY count DESC
            """)
            skill_data = [dict(record) for record in result]
        
        if skill_data:
            df = pd.DataFrame(skill_data)
            
            fig = px.pie(df, values='count', names='category', title='Skills by Category')
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.markdown("#### Student GPA Distribution")
        
        with recommender.driver.session() as session:
            result = session.run("""
                MATCH (s:Student)
                RETURN s.name as student, s.gpa as gpa, s.major as major
                ORDER BY s.gpa DESC
            """)
            student_data = [dict(record) for record in result]
        
        if student_data:
            df = pd.DataFrame(student_data)
            
            fig = px.bar(df, x='student', y='gpa', color='major',
                        title='Student GPA Comparison',
                        labels={'gpa': 'GPA', 'student': 'Student'})
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.markdown("#### Most In-Demand Skills")
        
        with recommender.driver.session() as session:
            result = session.run("""
                MATCH (i:Internship)-[:REQUIRES]->(sk:Skill)
                RETURN sk.name as skill, count(i) as demand
                ORDER BY demand DESC
                LIMIT 10
            """)
            demand_data = [dict(record) for record in result]
        
        if demand_data:
            df = pd.DataFrame(demand_data)
            
            fig = px.bar(df, x='skill', y='demand',
                        title='Top 10 Most Demanded Skills by Internships',
                        labels={'demand': 'Number of Internships', 'skill': 'Skill'},
                        color='demand',
                        color_continuous_scale='Blues')
            st.plotly_chart(fig, use_container_width=True)


def main():
    """Main Streamlit app"""
    
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/000000/education.png", width=80)
        st.markdown("## Navigation")
        
        page = st.radio(
            "Go to:",
            ["🏠 Dashboard", "🤖 Natural Query", "👨‍🎓 Student Profiles", 
             "🎯 Recommendations", "📊 Skill Gap Analysis", "📈 Analytics"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### About")
        st.info("""
        **Academic Skill Graph Recommender**
        
        AI-powered system using:
        - 🗄️ Neo4j Graph Database
        - 🤖 Groq AI (FREE & Fast)
        - ⚡ FastAPI Backend
        - 🎨 Streamlit UI
        
        Built for career guidance and skill development.
        """)
        
        st.markdown("---")
        st.markdown("### Quick Stats")
        stats = get_database_stats()
        st.metric("Total Nodes", sum([v for k, v in stats.items() if k != "Relationships"]))
        st.metric("Total Relationships", stats.get("Relationships", 0))
    
    # Main content based on selected page
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "🤖 Natural Query":
        show_natural_query()
    elif page == "👨‍🎓 Student Profiles":
        show_student_profiles()
    elif page == "🎯 Recommendations":
        show_recommendations()
    elif page == "📊 Skill Gap Analysis":
        show_skill_gap()
    elif page == "📈 Analytics":
        show_analytics()


if __name__ == "__main__":
    main()