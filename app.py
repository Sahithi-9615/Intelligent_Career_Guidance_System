from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from contextlib import asynccontextmanager
import uvicorn

from ai_service import AIService
from recommender import RecommendationEngine

# =====================================================
# Lifespan: Controls startup & shutdown events
# =====================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🔄 Initializing AI Service and Recommendation Engine...")
    global ai_service, recommender
    ai_service = AIService()
    recommender = RecommendationEngine()
    print("✅ Services ready!")
    yield
    recommender.close()
    print("✅ Connections closed, shutting down cleanly.")


# =====================================================
# Initialize FastAPI app
# =====================================================
app = FastAPI(
    title="Academic Skill Graph API",
    description="AI-powered recommendation system for students",
    version="1.0.0",
    lifespan=lifespan
)

# Allow frontend to access API (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# Request/Response Models
# =====================================================
class NaturalLanguageQuery(BaseModel):
    query: str
    student_id: Optional[str] = None

class QueryResponse(BaseModel):
    success: bool
    generated_cypher: Optional[str] = None
    results: List[dict]
    count: int
    message: Optional[str] = None

# =====================================================
# ROUTES / ENDPOINTS
# =====================================================

@app.get("/")
def read_root():
    """API Health Check"""
    return {
        "status": "running",
        "message": "Academic Skill Graph API",
        "version": "1.0.0",
        "endpoints": {
            "natural_query": "/api/query",
            "courses": "/api/courses",
            "internships": "/api/internships/{student_id}",
            "student": "/api/student/{student_id}",
            "skill_gap": "/api/skill-gap"
        }
    }

@app.post("/api/query", response_model=QueryResponse)
def natural_language_query(request: NaturalLanguageQuery):
    """Convert natural language to Cypher query and execute it."""
    try:
        cypher_query = ai_service.generate_cypher_query(request.query)
        result = recommender.execute_query(cypher_query)

        if result["success"]:
            return QueryResponse(
                success=True,
                generated_cypher=cypher_query,
                results=result["data"],
                count=result["count"],
                message="Query executed successfully"
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/courses")
def get_course_recommendations(
    student_id: Optional[str] = Query(None, description="Student ID"),
    skill: Optional[str] = Query(None, description="Skill name")
):
    """Get course recommendations based on skill or student profile."""
    try:
        result = recommender.recommend_courses(student_id=student_id, skill_name=skill)
        if result["success"]:
            return {"success": True, "courses": result["data"], "count": result["count"]}
        else:
            raise HTTPException(status_code=500, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/internships/{student_id}")
def get_internship_recommendations(student_id: str):
    """Get personalized internship recommendations for a student."""
    try:
        result = recommender.recommend_internships(student_id)
        if result["success"]:
            return {
                "success": True,
                "student_id": student_id,
                "internships": result["data"],
                "count": result["count"]
            }
        else:
            raise HTTPException(status_code=404, detail="Student not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/student/{student_id}")
def get_student_profile(student_id: str):
    """Get full student profile (skills, courses, projects)."""
    try:
        result = recommender.get_student_profile(student_id)
        if result["success"] and result["data"]:
            return {"success": True, "student": result["data"][0]}
        else:
            raise HTTPException(status_code=404, detail="Student not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/skill-gap")
def get_skill_gap(
    student_id: str = Query(..., description="Student ID"),
    internship_id: str = Query(..., description="Internship ID")
):
    """Analyze skill gap between student and internship."""
    try:
        result = recommender.get_skill_gap(student_id, internship_id)
        if result["success"]:
            missing = [s for s in result["data"] if s["status"] == "Missing"]
            weak = [s for s in result["data"] if s["status"] == "Weak"]
            sufficient = [s for s in result["data"] if s["status"] == "Sufficient"]

            return {
                "success": True,
                "student_id": student_id,
                "internship_id": internship_id,
                "missing_skills": missing,
                "weak_skills": weak,
                "sufficient_skills": sufficient,
                "readiness": round(len(sufficient) * 100 / len(result["data"]), 1)
                if result["data"] else 0
            }
        else:
            raise HTTPException(status_code=404, detail="Student or internship not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/students/search")
def search_students(
    skill: Optional[str] = Query(None, description="Filter by skill"),
    major: Optional[str] = Query(None, description="Filter by major"),
    min_gpa: Optional[float] = Query(None, description="Minimum GPA")
):
    """Search students by filters."""
    try:
        result = recommender.search_students(skill_name=skill, major=major, min_gpa=min_gpa)
        if result["success"]:
            return {"success": True, "students": result["data"], "count": result["count"]}
        else:
            raise HTTPException(status_code=500, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# Run the Server
# =====================================================
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🚀 STARTING ACADEMIC SKILL GRAPH API")
    print("=" * 70)
    print("\n📍 API will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("\n" + "=" * 70 + "\n")

    # Proper reload-enabled startup
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
