from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler , Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.background import BackgroundScheduler
import os 

from .core.config import settings
from .database import Base, engine, SessionLocal
from .core.middleware import  register_middlewares 
from .routers.role_router import router as role_router
from .routers.permission_router import router as permission_router
from .routers.user_route import router as user_router
from .routers.auth_router import router as auth_router
from .routers.audit_log_router import router as audit_log_router
from .routers.brand_router import router as brand_router
from .routers.category_router import router as category_router
from .routers.product_router import router as product_router
from .routers.catalog_router import router as catalog_router
from .routers.inventory_router import router as inventory_router
from .routers.telegram_router import router as telegram_router
from .routers.order_router import router as order_router
from .routers.cart_router import router as cart_router
from .routers.payment_router import router as payment_router
from .routers.review_router import router as review_router
from .routers.wishlist_router import router as wishlist_router
from .routers.variant_router import router as variant_router
from .routers.email_router import router as email_router
from .routers.discount_router import router as discount_router
from .routers.banner_router import router as banner_router
from .routers.coupon_reward_router import router as coupon_reward_router
from .routers.report_router import router as report_router
from app.services.inventory_alert_service import InventoryAlertService
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    print("Database tables created")
    yield
    print("Shutting down...")

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="FastAPI Application",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#static folder store image 
os.makedirs("app/static/images", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
# Register rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth_router, prefix="/api", tags=["Auth"])
app.include_router(user_router, prefix="/api", tags=["Users"])
app.include_router(role_router, prefix="/api", tags=["Roles"])
app.include_router(permission_router, prefix="/api", tags=["Permissions"])
app.include_router(audit_log_router, prefix="/api", tags=["Audit Logs"])
app.include_router(brand_router, prefix="/api", tags=["Brands"])
app.include_router(category_router, prefix="/api", tags=["Categories"])
app.include_router(product_router, prefix="/api", tags=["Products"])
app.include_router(catalog_router, prefix="/api", tags=["Catalog"])
app.include_router(variant_router, prefix="/api", tags=["Product Variants"])
app.include_router(inventory_router, prefix="/api", tags=["Inventory"])
app.include_router(telegram_router, prefix="/api/alerts", tags=["Inventory Alerts"])
app.include_router(order_router, prefix="/api", tags=["Orders"])
app.include_router(cart_router, prefix="/api", tags=["Cart"])
app.include_router(payment_router, prefix="/api", tags=["Payments"])
app.include_router(review_router, prefix="/api", tags=["Reviews"])
app.include_router(wishlist_router, prefix="/api", tags=["Wishlist"])
app.include_router(email_router,prefix="/api", tags=["Email"])
app.include_router(banner_router, prefix="/api", tags=["Banners"])
app.include_router(discount_router, prefix="/api", tags=["Discounts"])
app.include_router(coupon_reward_router, prefix="/api/coupons", tags=["Coupon Rewards"])
app.include_router(report_router, prefix="/api", tags=["Reports & Analytics"])

@app.get("/", tags=["health"])
def health():
    return {"status": "ok"}


# ==============================
# 🕒 Daily Inventory Alert Scheduler
# ==============================
def send_daily_inventory_alerts():
    """Automatically send daily inventory alerts."""
    db = SessionLocal()
    try:
        InventoryAlertService.send_daily_report(db)
        print("✅ Daily inventory alert sent successfully.")
    except Exception as e:
        print(f"❌ Error sending daily alert: {str(e)}")
    finally:
        db.close()


scheduler = BackgroundScheduler()
# Every day at 9:00 AM
scheduler.add_job(send_daily_inventory_alerts, "cron", hour=9, minute=0)
scheduler.start()
print("Daily inventory alert scheduler started (Every day 9AM)")