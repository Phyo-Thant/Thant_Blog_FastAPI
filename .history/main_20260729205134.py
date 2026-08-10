from fastapi import FastAPI, Request, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from schemas import PostResponse, PostCreate, PostBase

app = FastAPI()

templates = Jinja2Templates(directory = "templates",)

app.mount("/static", StaticFiles(directory= "static"), name = "static")


posts: list[dict] = [
    {
        "id": 1,
        "author": "Phyo Thant",
        "title": "FastAPI is Awesome",
        "content": "This framework is really easy to use and super fast.",
        "date_posted": "April 20, 2025",
    },
    {
        "id": 2,
        "author": "Chan Lin Thaw",
        "title": "Python is Great for Web Development",
        "content": "Python is a great language for web development, and FastAPI makes it even better.",
        "date_posted": "April 21, 2025",
    },
    {
        "id": 3,
        "author": "Thiha Zaw",
        "title": "Getting Started with APIs",
        "content": "APIs allow different applications to communicate with each other efficiently.",
        "date_posted": "April 22, 2025",
    },
    {
        "id": 4,
        "author": "Alice Johnson",
        "title": "Why Learn Python?",
        "content": "Python is beginner-friendly, powerful, and widely used in many industries.",
        "date_posted": "April 23, 2025",
    },
    {
        "id": 5,
        "author": "Michael Brown",
        "title": "Understanding Databases",
        "content": "Databases help applications store, organize, and retrieve data effectively.",
        "date_posted": "April 24, 2025",
    },
    {
        "id": 6,
        "author": "Emily Davis",
        "title": "Introduction to PostgreSQL",
        "content": "PostgreSQL is a robust open-source relational database system.",
        "date_posted": "April 25, 2025",
    },
    {
        "id": 7,
        "author": "David Wilson",
        "title": "Building RESTful Services",
        "content": "RESTful APIs provide a standard way for clients and servers to exchange data.",
        "date_posted": "April 26, 2025",
    },    
]


@app.get("/", include_in_schema=False, name="home")

@app.get("/posts", include_in_schema=False, name="post")
def home(request: Request):
    return templates.TemplateResponse(request, "home.html", {"posts": posts, "title": "Index"})

@app.get("/posts/{post_id}", include_in_schema=False, name="post_detail")
def post_detail(request: Request, post_id: int):
    for post in posts:
        if post["id"] == post_id:
            return templates.TemplateResponse(request, "post.html", {"post": post, "title": post["title"]})
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id {post_id} not found")

@app.get("/api/posts", responnse_model=list[PostResponse])
def get_posts():
    return posts


@app.get("/api/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: int):
    for post in posts:
        if post["id"] == post_id:
            return post
        
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id {post_id} not found")


 
@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
    )

    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exception.status_code,
            content={"detail": message},
        )
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code,
    )
        
        
        
@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": exception.errors()},
        )
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )        