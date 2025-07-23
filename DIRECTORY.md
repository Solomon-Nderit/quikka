quikka/
├── app/
│   ├── main.py          # FastAPI entrypoint
│   ├── models.py        # DB models
│   ├── schemas.py       # Pydantic schemas
│   ├── crud.py          # DB queries
│   ├── routes/          # FastAPI routers (auth, bookings, stylists)
│   └── services/        # External service integrations (M-Pesa)
├── frontend/
│   ├── public/          # Static assets
│   └── templates/       # Jinja2 HTML pages (for simplicity)
├── tests/               # Unit and integration tests
├── .env.example         # Env variables placeholder
├── requirements.txt     # Python dependencies
├── DIRECTORY.md         # This file
└── README.md            # This file
