# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

import models, database, auth, schemas
from database import engine
from sqlalchemy import text

from typing import List
# This line creates all our database tables the moment the app starts!
models.Base.metadata.create_all(bind=engine)

# Ensure backward-compatible columns exist (useful when schema was changed locally)
def ensure_project_columns():
    try:
        with engine.connect() as conn:
            # For SQLite, inspect pragma table_info
            res = conn.execute(text("PRAGMA table_info('projects')"))
            cols = [r[1] for r in res.fetchall()]
            if 'start_date' not in cols:
                conn.execute(text("ALTER TABLE projects ADD COLUMN start_date DATETIME"))
            if 'end_date' not in cols:
                conn.execute(text("ALTER TABLE projects ADD COLUMN end_date DATETIME"))
            conn.commit()
    except Exception:
        # If anything goes wrong, don't crash the startup; tables will be created for fresh DBs.
        pass

ensure_project_columns()

app = FastAPI(title="Ethara AI Task Manager")

@app.post("/auth/signup", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    # Check if username already exists
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Hash the password and save the user
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_password, role=user.role)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    # Verify the user exists and the password is correct
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate the JWT Token
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- PROJECT ENDPOINTS ---

@app.post("/projects/", response_model=schemas.ProjectResponse)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_admin_user)):
    # Only Admins can hit this endpoint (enforced by get_admin_user)
    # Validate dates if provided
    if project.start_date and project.end_date and project.end_date < project.start_date:
        raise HTTPException(status_code=400, detail="end_date must be the same or after start_date")

    new_project = models.Project(**project.model_dump(), admin_id=current_user.id)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project

@app.get("/projects/", response_model=List[schemas.ProjectResponse])
def get_projects(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role == "Admin":
        # Admins see the projects they created
        return db.query(models.Project).filter(models.Project.admin_id == current_user.id).all()
    else:
        # Members see projects where they have assigned tasks
        tasks = db.query(models.Task).filter(models.Task.assigned_to == current_user.id).all()
        project_ids = {task.project_id for task in tasks}
        return db.query(models.Project).filter(models.Project.id.in_(project_ids)).all()


@app.get("/users/", response_model=List[schemas.UserResponse])
def list_users(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Return all users (used by Admin UI to pick assignees)
    return db.query(models.User).all()

# --- TASK ENDPOINTS ---

@app.post("/projects/{project_id}/tasks/", response_model=schemas.TaskResponse)
def create_task(project_id: int, task: schemas.TaskCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_admin_user)):
    # Verify project exists and belongs to this admin
    project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.admin_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or not authorized")
    
    new_task = models.Task(**task.model_dump(), project_id=project_id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@app.patch("/tasks/{task_id}/status")
def update_task_status(task_id: int, status: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Security Check: Admins can update anything, Members can only update their own tasks
    if current_user.role != "Admin" and task.assigned_to != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this task")
    
    if status not in ["Pending", "In Progress", "Completed"]:
        raise HTTPException(status_code=400, detail="Invalid status. Must be Pending, In Progress, or Completed")
        
    task.status = status
    db.commit()
    db.refresh(task)
    return task