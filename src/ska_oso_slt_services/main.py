from fastapi import Depends, FastAPI

from ska_oso_slt_services.routers.shift_router import router

app = FastAPI()

app.include_router(router)
