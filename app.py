from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import os


app = Flask(__name__)

MCQ_QUESTIONS = [
    {
        "skill": "Python",
        "question": "What is Python?",
        "options": [
            "A database",
            "A programming language",
            "An operating system",
            "A web browser"
        ],
        "answer": 1
    },
    {
        "skill": "Python",
        "question": "Which brackets are used to create a list in Python?",
        "options": ["()", "{}", "[]", "<>"],
        "answer": 2
    },
    {
        "skill": "Python",
        "question": "Which keyword is used to define a function?",
        "options": ["function", "define", "def", "fun"],
        "answer": 2
    },
    {
        "skill": "SQL",
        "question": "What is the full form of SQL?",
        "options": [
            "Simple Query Language",
            "Structured Query Language",
            "Standard Question Language",
            "System Query Logic"
        ],
        "answer": 1
    },
    {
        "skill": "SQL",
        "question": "Which SQL command retrieves data from a table?",
        "options": ["GET", "OPEN", "SELECT", "FETCH ALL"],
        "answer": 2
    },
    {
        "skill": "SQL",
        "question": "Which SQL clause filters grouped results?",
        "options": ["WHERE", "ORDER BY", "HAVING", "SELECT"],
        "answer": 2
    },
    {
        "skill": "Power BI",
        "question": "What is Power BI mainly used for?",
        "options": [
            "Creating operating systems",
            "Data analysis and visualization",
            "Writing HTML only",
            "Managing computer hardware"
        ],
        "answer": 1
    },
    {
        "skill": "Power BI",
        "question": "What does DAX stand for?",
        "options": [
            "Data Analysis Expressions",
            "Digital Application Extension",
            "Data Access Exchange",
            "Direct Analysis XML"
        ],
        "answer": 0
    },
    {
        "skill": "HTML",
        "question": "What is the full form of HTML?",
        "options": [
            "HighText Machine Language",
            "HyperText Markup Language",
            "Hyper Transfer Main Language",
            "Home Tool Markup Language"
        ],
        "answer": 1
    },
    {
        "skill": "HTML",
        "question": "Which language is used to style a web page?",
        "options": ["SQL", "Python", "CSS", "DAX"],
        "answer": 2
    },
    {
        "skill": "HTML",
        "question": "Which HTML tag creates a hyperlink?",
        "options": ["<p>", "<h1>", "<a>", "<img>"],
        "answer": 2
    }
]


# =========================================================
# DATABASE CONNECTION
# =========================================================
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "defaultdb"),
        connection_timeout=15
    )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("Please fill all fields.")
            return redirect(url_for("register"))

        db = None
        cursor = None

        try:

            db = get_db_connection()
            cursor = db.cursor(buffered=True)

            # Check existing email
            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE email=%s
                """,
                (email,)
            )

            if cursor.fetchone():

                flash("Email already registered. Please login.")
                return redirect(url_for("login"))

            # Hash password
            hashed_password = generate_password_hash(password)

            # Insert user
            cursor.execute(
                """
                INSERT INTO users
                (name, email, password)
                VALUES (%s, %s, %s)
                """,
                (
                    name,
                    email,
                    hashed_password
                )
            )

            db.commit()

            flash("Registration successful. Please login.")

            return redirect(url_for("login"))

        except Error as e:

            return f"Registration error: {e}"

        finally:

            if cursor:
                cursor.close()

            if db:
                db.close()

    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:

            flash("Please enter email and password.")

            return redirect(url_for("login"))

        db = None
        cursor = None

        try:

            db = get_db_connection()

            cursor = db.cursor(
                dictionary=True,
                buffered=True
            )

            cursor.execute(
                """
                SELECT *
                FROM users
                WHERE email=%s
                """,
                (email,)
            )

            user = cursor.fetchone()

           
            if not user:

                flash("Email not found. Please check your email.")

                return redirect(url_for("login"))

            # Correct password checking
            try:

                password_correct = check_password_hash(
                    user["password"],
                    password
                )

            except Exception:

                password_correct = False

            if not password_correct:

                flash("Incorrect password. Please try again.")

                return redirect(url_for("login"))

            # Create session
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]

            return redirect(url_for("dashboard"))

        except Error as e:

            return f"Login error: {e}"

        finally:

            if cursor:
                cursor.close()

            if db:
                db.close()

    return render_template("login.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# =========================================================
# DASHBOARD
# =========================================================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    hour = datetime.now().hour

    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor(buffered=True)

        user_id = session["user_id"]

        # Count the skills saved by this user
        cursor.execute(
            "SELECT COUNT(*) FROM user_skills WHERE user_id = %s",
            (user_id,)
        )
        total_skills = cursor.fetchone()[0]

        # Count completed roadmap steps for this user
        cursor.execute(
            """
            SELECT COUNT(DISTINCT CONCAT(LOWER(TRIM(skill)), '-', step_number))
            FROM user_progress
            WHERE user_id = %s AND completed = TRUE
            """,
            (user_id,)
        )
        completed_steps = cursor.fetchone()[0]

        # Each supported roadmap contains 8 steps
        total_steps = total_skills * 8

        if total_steps > 0:
            progress_percentage = round(
                (completed_steps / total_steps) * 100
            )
            progress_percentage = min(100, progress_percentage)
        else:
            progress_percentage = 0

        return render_template(
            "dashboard.html",
            greeting=greeting,
            progress_percentage=progress_percentage
        )

    except Exception as e:
        print("Dashboard error:", e)
        return "Unable to load dashboard. Please check the Flask terminal."

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()
# =========================================================
# PROFILE
# =========================================================

@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    db = None
    cursor = None

    try:

        db = get_db_connection()

        cursor = db.cursor(
            dictionary=True,
            buffered=True
        )

        cursor.execute(
            """
            SELECT
                id,
                name,
                email,
                created_at
            FROM users
            WHERE id=%s
            """,
            (session["user_id"],)
        )

        user = cursor.fetchone()

        return render_template(
            "profile.html",
            user=user
        )

    except Error as e:

        return f"Profile error: {e}"

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()


# =========================================================
# SKILLS
# =========================================================

@app.route("/skills", methods=["GET", "POST"])
def skills():

    if "user_id" not in session:
        return redirect(url_for("login"))

    db = None
    cursor = None

    try:

        db = get_db_connection()

        cursor = db.cursor(
            dictionary=True,
            buffered=True
        )

        # -----------------------------
        # ADD SKILL
        # -----------------------------

        if request.method == "POST":

            skill_name = request.form.get(
                "skill_name",
                ""
            ).strip()

            category = request.form.get(
                "category",
                ""
            ).strip()

            skill_level = request.form.get(
                "skill_level",
                ""
            ).strip()

            if not skill_name or not category or not skill_level:

                flash(
                    "Please select category, skill and skill level."
                )

                return redirect(
                    url_for("skills")
                )

            # Check duplicate
            cursor.execute(
                """
                SELECT user_skill_id
                FROM user_skills
                WHERE user_id=%s
                AND skill_name=%s
                """,
                (
                    session["user_id"],
                    skill_name
                )
            )

            existing_skill = cursor.fetchone()

            if existing_skill:

                flash("This skill is already added.")

            else:

                cursor.execute(
                    """
                    INSERT INTO user_skills
                    (
                        user_id,
                        skill_name,
                        category,
                        skill_level
                    )
                    VALUES (%s,%s,%s,%s)
                    """,
                    (
                        session["user_id"],
                        skill_name,
                        category,
                        skill_level
                    )
                )

                db.commit()

                flash("Skill added successfully.")

        # -----------------------------
        # GET USER SKILLS
        # -----------------------------

        cursor.execute(
            """
            SELECT
                user_skill_id,
                skill_name,
                category,
                skill_level
            FROM user_skills
            WHERE user_id=%s
            ORDER BY skill_name
            """,
            (session["user_id"],)
        )

        user_skills = cursor.fetchall()

        return render_template(
            "skills.html",
            skills=user_skills
        )

    except Error as e:

        return f"Skills error: {e}"

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()


# =========================================================
# DELETE SKILL
# =========================================================
@app.route("/delete_skill/<int:skill_id>", methods=["POST"])
def delete_skill(skill_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor()

        user_id = session["user_id"]

        # Find the skill belonging to the logged-in user
        cursor.execute(
            """
            SELECT skill_name
            FROM user_skills
            WHERE user_skill_id = %s
              AND user_id = %s
            """,
            (skill_id, user_id)
        )

        result = cursor.fetchone()

        if not result:
            flash("Skill not found.")
            return redirect(url_for("skills"))

        skill_name = result[0]

        # Delete this skill's saved roadmap progress
        cursor.execute(
            """
            DELETE FROM user_progress
            WHERE user_id = %s
              AND LOWER(TRIM(skill)) = LOWER(TRIM(%s))
            """,
            (user_id, skill_name)
        )

        # Delete the skill itself
        cursor.execute(
            """
            DELETE FROM user_skills
            WHERE user_skill_id = %s
              AND user_id = %s
            """,
            (skill_id, user_id)
        )

        db.commit()

        flash("Skill and its associated roadmap progress deleted successfully.")
        return redirect(url_for("skills"))

    except Error as e:
        if db:
            db.rollback()
        return f"Delete skill error: {e}"

    finally:
        if cursor:
            cursor.close()

        if db:
            db.close()

# =========================================================
# CAREERS
# =========================================================

@app.route("/careers")
def careers():

    if "user_id" not in session:
        return redirect(url_for("login"))

    db = None
    cursor = None

    try:

        db = get_db_connection()

        cursor = db.cursor(
            dictionary=True,
            buffered=True
        )

        cursor.execute(
            """
            SELECT
                career_id,
                career_name,
                category,
                required_skills,
                description,
                qualification
            FROM careers
            ORDER BY career_name
            """
        )

        career_list = cursor.fetchall()

        return render_template(
            "careers.html",
            careers=career_list
        )

    except Error as e:

        return f"Careers error: {e}"

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()


# =========================================================
# CAREER ADVISOR
# =========================================================

@app.route("/career_advisor")
def career_advisor():

    if "user_id" not in session:
        return redirect(url_for("login"))

    db = None
    cursor = None

    try:

        db = get_db_connection()

        cursor = db.cursor(
            dictionary=True,
            buffered=True
        )

        # Get user's skills
        cursor.execute(
            """
            SELECT skill_name
            FROM user_skills
            WHERE user_id=%s
            """,
            (session["user_id"],)
        )

        user_skill_rows = cursor.fetchall()

        user_skills = [
            row["skill_name"].strip().lower()
            for row in user_skill_rows
        ]

        # Get careers
        cursor.execute(
            """
            SELECT
                career_id,
                career_name,
                category,
                required_skills,
                description,
                qualification
            FROM careers
            """
        )

        careers_data = cursor.fetchall()

        recommendations = []

        for career in careers_data:

            required = [
                item.strip().lower()
                for item in career["required_skills"].split(",")
                if item.strip()
            ]

            matched = [
                skill
                for skill in required
                if skill in user_skills
            ]

            percentage = (
                int(
                    (len(matched) / len(required)) * 100
                )
                if required
                else 0
            )

            recommendations.append(
                {
                    "career_name": career["career_name"],
                    "category": career["category"],
                    "description": career["description"],
                    "qualification": career["qualification"],
                    "percentage": percentage,
                    "matched": matched
                }
            )

        recommendations.sort(
            key=lambda item: item["percentage"],
            reverse=True
        )

        return render_template(
            "career_advisor.html",
            user_skills=user_skills,
            recommendations=recommendations
        )

    except Error as e:

        return f"Career advisor error: {e}"

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()


# =========================================================
# SKILL GAP
# =========================================================

@app.route("/skill_gap")
def skill_gap():

    if "user_id" not in session:
        return redirect(url_for("login"))

    db = None
    cursor = None

    try:

        db = get_db_connection()

        cursor = db.cursor(
            dictionary=True,
            buffered=True
        )

        cursor.execute(
            """
            SELECT
                skill_name,
                category,
                skill_level
            FROM user_skills
            WHERE user_id=%s
            ORDER BY skill_name
            """,
            (session["user_id"],)
        )

        rows = cursor.fetchall()

        level_value = {
            "Beginner": 1,
            "Intermediate": 2,
            "Advanced": 3,
            "Expert": 4
        }

        result = []

        for row in rows:

            current = level_value.get(
                row["skill_level"],
                1
            )

            gap_value = 3 - min(
                current,
                3
            )

            if gap_value == 0:

                gap = "No Gap"

            elif gap_value == 1:

                gap = "Medium"

            else:

                gap = "High"

            result.append(
                {
                    "skill_name": row["skill_name"],
                    "category": row["category"],
                    "current": row["skill_level"],
                    "required": "Advanced",
                    "gap": gap
                }
            )

        return render_template(
            "skill_gap.html",
            skills=result
        )

    except Error as e:

        return f"Skill gap error: {e}"

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()


# =========================================================
# COURSES
# =========================================================
# IMPORTANT:
# There is ONLY ONE /courses route in this file.
# =========================================================

@app.route("/courses")
def courses():

    if "user_id" not in session:
        return redirect(url_for("login"))

    skill = request.args.get(
        "skill",
        ""
    ).strip()

    db = None
    cursor = None

    try:

        db = get_db_connection()

        cursor = db.cursor(
            dictionary=True,
            buffered=True
        )

        if skill:

            cursor.execute(
                """
                SELECT
                    course_id,
                    course_name,
                    level,
                    provider,
                    skill
                FROM courses
                WHERE LOWER(TRIM(skill))
                      =
                      LOWER(TRIM(%s))
                ORDER BY course_name
                """,
                (skill,)
            )

        else:

            cursor.execute(
                """
                SELECT
                    course_id,
                    course_name,
                    level,
                    provider,
                    skill
                FROM courses
                ORDER BY skill, course_name
                """
            )

        courses_data = cursor.fetchall()

        return render_template(
            "courses.html",
            courses=courses_data,
            selected_skill=skill
        )

    except Error as e:

        return f"Courses error: {e}"

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()


# =========================================================
# ROADMAP DATA
# =========================================================

ROADMAPS = {

    "Python": [

        "Learn Python Basics",

        "Practice Variables and Data Types",

        "Learn Conditions and Loops",

        "Learn Functions",

        "Learn Lists, Tuples and Dictionaries",

        "Learn Object-Oriented Programming",

        "Build Python Projects",

        "Learn Advanced Python"

    ],

    "SQL": [

        "Learn Database Fundamentals",

        "Learn SELECT Queries",

        "Practice WHERE and ORDER BY",

        "Learn GROUP BY and Aggregate Functions",

        "Learn SQL JOIN Operations",

        "Practice Subqueries",

        "Learn Advanced SQL",

        "Build Database Projects"

    ],

    "HTML": [

        "Learn HTML Basics",

        "Learn HTML Tags",

        "Create Forms and Tables",

        "Learn Semantic HTML",

        "Learn CSS Basics",

        "Build Simple Web Pages",

        "Create Responsive Websites",

        "Build Web Development Projects"

    ],

    "Power BI": [

        "Learn Power BI Interface",

        "Import Data",

        "Clean Data Using Power Query",

        "Create Data Visualizations",

        "Learn Data Modeling",

        "Learn DAX",

        "Build Interactive Dashboards",

        "Create Professional Power BI Projects"

    ]

}


# =========================================================
# ROADMAP
# =========================================================

@app.route("/roadmap")
def roadmap():

    if "user_id" not in session:
        return redirect(url_for("login"))

    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor(buffered=True)

        user_id = session["user_id"]

        # Get skills saved by the logged-in user
        cursor.execute(
            """
            SELECT skill_name
            FROM user_skills
            WHERE user_id = %s
            ORDER BY skill_name
            """,
            (user_id,)
        )

        user_skills = [row[0] for row in cursor.fetchall()]

        # Do not show a roadmap when no skills are saved
        if not user_skills:
            flash("Please add a skill before opening your learning roadmap.")
            return redirect(url_for("skills"))

        # Use the requested skill, or the user's first saved skill
        requested_skill = request.args.get("skill", "").strip()

        if requested_skill:
            skill = next(
                (
                    saved_skill
                    for saved_skill in user_skills
                    if saved_skill.lower() == requested_skill.lower()
                ),
                None
            )
        else:
            skill = user_skills[0]

        # Prevent opening a roadmap for a skill not saved by this user
        if skill is None:
            flash("Please select one of your saved skills.")
            return redirect(url_for("skills"))

        # Check whether a roadmap exists for this skill
        steps = ROADMAPS.get(skill)

        if steps is None:
            flash(f"No learning roadmap is available for {skill} yet.")
            return redirect(url_for("skills"))

        # Get completed steps for this user and skill
        cursor.execute(
            """
            SELECT step_number
            FROM user_progress
            WHERE user_id = %s
              AND skill = %s
              AND completed = TRUE
            """,
            (user_id, skill)
        )

        completed_steps = [row[0] for row in cursor.fetchall()]

        completed_count = len(set(completed_steps))

        progress_percentage = (
            int((completed_count / len(steps)) * 100)
            if steps else 0
        )

        return render_template(
            "roadmap.html",
            skill=skill,
            steps=steps,
            completed_steps=completed_steps,
            progress_percentage=progress_percentage
        )

    except Error as e:
        return f"Roadmap error: {e}"

    finally:
        if cursor:
            cursor.close()

        if db:
            db.close()

# =========================================================
# UPDATE ROADMAP PROGRESS
# =========================================================

@app.route(
    "/update_progress",
    methods=["POST"]
)
def update_progress():

    if "user_id" not in session:
        return redirect(url_for("login"))

    skill = request.form.get(
        "skill",
        ""
    ).strip()

    step_number = request.form.get(
        "step_number",
        ""
    ).strip()

    if not skill or not step_number:

        return redirect(
            url_for("roadmap")
        )

    db = None
    cursor = None

    try:

        db = get_db_connection()

        cursor = db.cursor(
            buffered=True
        )

        cursor.execute(
            """
            SELECT progress_id
            FROM user_progress
            WHERE user_id=%s
            AND skill=%s
            AND step_number=%s
            """,
            (
                session["user_id"],
                skill,
                step_number
            )
        )

        existing = cursor.fetchone()

        if existing:

            cursor.execute(
                """
                UPDATE user_progress
                SET completed=TRUE
                WHERE user_id=%s
                AND skill=%s
                AND step_number=%s
                """,
                (
                    session["user_id"],
                    skill,
                    step_number
                )
            )

        else:

            cursor.execute(
                """
                INSERT INTO user_progress
                (
                    user_id,
                    skill,
                    step_number,
                    completed
                )
                VALUES (%s,%s,%s,TRUE)
                """,
                (
                    session["user_id"],
                    skill,
                    step_number
                )
            )

        db.commit()

        return redirect(
            url_for(
                "roadmap",
                skill=skill
            )
        )

    except Error as e:

        return f"Progress error: {e}"

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()


# =========================================================
# INTERVIEW
# =========================================================

@app.route(
    "/interview",
    methods=["GET", "POST"]
)
def interview():

    if "user_id" not in session:
        return redirect(url_for("login"))

    db = None
    cursor = None

    try:

        db = get_db_connection()

        cursor = db.cursor(
            dictionary=True,
            buffered=True
        )

        cursor.execute(
            """
            SELECT
                question_id,
                question,
                skill
            FROM interview_questions
            ORDER BY question_id
            """
        )

        questions = cursor.fetchall()

        if request.method == "POST":

            score = 0

            answered = 0

            feedback_parts = []

            for q in questions:

                answer = request.form.get(
                    f"answer_{q['question_id']}",
                    ""
                ).strip()

                if answer:

                    answered += 1

                    words = len(
                        answer.split()
                    )

                    if words >= 15:

                        score += 10

                    elif words >= 7:

                        score += 7

                    elif words >= 3:

                        score += 5

                    else:

                        score += 2

                    feedback_parts.append(
                        f"{q['skill']}: Answer provided."
                    )

                else:

                    feedback_parts.append(
                        f"{q['skill']}: No answer provided."
                    )

            max_score = len(questions) * 10

            final_score = (

                round(
                    (score / max_score) * 100,
                    2
                )

                if max_score

                else 0
            )

            feedback = (

                f"You answered {answered} "

                f"out of {len(questions)} questions. "

                "Try to give clear answers with "

                "definitions, examples and practical points. "

                + " ".join(feedback_parts)
            )

            cursor.execute(
                """
                INSERT INTO interviews
                (
                    user_id,
                    interview_type,
                    score,
                    feedback,
                    interview_date
                )
                VALUES (%s,%s,%s,%s,%s)
                """,
                (
                    session["user_id"],
                    "Technical Mock Interview",
                    final_score,
                    feedback,
                    date.today()
                )
            )

            db.commit()

            return redirect(
                url_for("interview_results")
            )

        return render_template(
            "interview.html",
            questions=questions
        )

    except Error as e:

        return f"Interview error: {e}"

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()


# =========================================================
# INTERVIEW RESULTS
# =========================================================

@app.route("/interview_results")
def interview_results():

    if "user_id" not in session:
        return redirect(url_for("login"))

    db = None
    cursor = None

    try:

        db = get_db_connection()

        cursor = db.cursor(
            dictionary=True,
            buffered=True
        )

        cursor.execute(
            """
            SELECT
                interview_id,
                interview_type,
                score,
                feedback,
                interview_date
            FROM interviews
            WHERE user_id=%s
            ORDER BY interview_id DESC
            """,
            (session["user_id"],)
        )

        results = cursor.fetchall()

        return render_template(
            "interview_results.html",
            results=results
        )

    except Error as e:

        return f"Interview results error: {e}"

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()


# =========================================================
# PROGRESS DASHBOARD
# =========================================================

@app.route("/progress")
def progress():

    if "user_id" not in session:
        return redirect(url_for("login"))

    db = None
    cursor = None

    try:

        db = get_db_connection()

        cursor = db.cursor(
            dictionary=True,
            buffered=True
        )

        # Total skills

        cursor.execute(
            """
            SELECT COUNT(*) AS total_skills
            FROM user_skills
            WHERE user_id=%s
            """,
            (session["user_id"],)
        )

        total_skills = cursor.fetchone()[
            "total_skills"
        ]

        # Completed roadmap steps

        cursor.execute(
            """
            SELECT COUNT(*) AS completed_steps
            FROM user_progress
            WHERE user_id=%s
            AND completed=TRUE
            """,
            (session["user_id"],)
        )

        completed_steps = cursor.fetchone()[
            "completed_steps"
        ]

        # Interviews

        cursor.execute(
            """
            SELECT COUNT(*) AS interviews
            FROM interviews
            WHERE user_id=%s
            """,
            (session["user_id"],)
        )

        interviews_count = cursor.fetchone()[
            "interviews"
        ]

        # Average score

        cursor.execute(
            """
            SELECT AVG(score) AS average_score
            FROM interviews
            WHERE user_id=%s
            """,
            (session["user_id"],)
        )

        avg_row = cursor.fetchone()

        average_score = (

            round(
                float(avg_row["average_score"]),
                2
            )

            if avg_row["average_score"] is not None

            else 0
        )

        return render_template(
            "progress.html",
            total_skills=total_skills,
            completed_steps=completed_steps,
            interviews_count=interviews_count,
            average_score=average_score
        )

    except Error as e:

        return f"Progress dashboard error: {e}"

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()


# =========================================================
# ADMIN
# =========================================================

@app.route("/admin")
def admin():

    if "user_id" not in session:
        return redirect(url_for("login"))

    db = None
    cursor = None

    try:

        db = get_db_connection()

        cursor = db.cursor(
            dictionary=True,
            buffered=True
        )

        cursor.execute(
            "SELECT COUNT(*) AS total FROM users"
        )

        users_count = cursor.fetchone()[
            "total"
        ]

        cursor.execute(
            "SELECT COUNT(*) AS total FROM careers"
        )

        careers_count = cursor.fetchone()[
            "total"
        ]

        cursor.execute(
            "SELECT COUNT(*) AS total FROM courses"
        )

        courses_count = cursor.fetchone()[
            "total"
        ]

        cursor.execute(
            "SELECT COUNT(*) AS total FROM interviews"
        )

        interviews_count = cursor.fetchone()[
            "total"
        ]

        return render_template(
            "admin.html",
            users_count=users_count,
            careers_count=careers_count,
            courses_count=courses_count,
            interviews_count=interviews_count
        )

    except Error as e:

        return f"Admin error: {e}"

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()


@app.route("/mcq_interview")
def mcq_interview():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "mcq_interview.html",
        questions=MCQ_QUESTIONS
    )



# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)
