from fastapi import APIRouter, Depends, BackgroundTasks
from app.services.inventory_alert_service import InventoryAlertService
from app.database import get_db
from app.models.user import User

router = APIRouter()
@router.post("/daily")
def trigger_daily_alerts(
    background_tasks: BackgroundTasks,
    db = Depends(get_db),
):
    """Trigger daily inventory alerts manually (can be used by cronjob or admin)."""
    background_tasks.add_task(InventoryAlertService.send_daily_report, db,)
    return {"message": "Daily inventory alert is being processed"}

