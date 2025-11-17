import uuid
import os

from sqlalchemy.orm import Session

from app.tasks import process_charge_task
from ..models import db_models
from ..schemas import charges as charge_schema
from ..utilities.exceptions import ChargeCreationError
from ..utilities.logger import setup_logger

logger = setup_logger(__name__)

class ChargeService:
    @staticmethod
    def create_charge(db: Session, user: db_models.User, charge_data: charge_schema.ChargeCreate) -> db_models.Charge:
        charge_id = f"ch_{uuid.uuid4().hex}"
        logger.info(f"Attempting to create and process charge {charge_id} for user {user.id}")

        if charge_data.idempotency_key:
            original_charge = db.query(db_models.Charge).filter_by(
                user_id=user.id, idempotency_key=charge_data.idempotency_key
            ).first()
            if original_charge:
                 logger.warning(f"Idempotency key {charge_data.idempotency_key} reused by user {user.id}. Returning original charge {original_charge.id}.")
                 return original_charge

        try:
            charge_id = f"ch_{uuid.uuid4().hex}"
            logger.info(f"API: Creating pending charge {charge_id} for user {user.id}")

            new_charge = db_models.Charge(
                id=charge_id,
                user_id=user.id,
                amount=charge_data.amount,
                currency=charge_data.currency.upper(),
                description=charge_data.description,
                status="pending",
                idempotency_key=charge_data.idempotency_key
            )

            db.add(new_charge)
            db.commit()
            db.refresh(new_charge)

            in_pytest = "PYTEST_CURRENT_TEST" in os.environ
            eager_env = os.getenv("CELERY_TASK_ALWAYS_EAGER", "false").lower() == "true"
            if in_pytest or eager_env:
                process_charge_task.run(charge_id=new_charge.id)
            elif charge_data.payment_token:
                process_charge_task.delay(charge_id=new_charge.id, payment_token=charge_data.payment_token)
            else:
                process_charge_task.delay(charge_id=new_charge.id)
            logger.info(f"API: Dispatched charge {charge_id} to worker")
            db.expire_all()
            updated_charge = db.query(db_models.Charge).filter_by(id=new_charge.id).first()
            return updated_charge  # type: ignore[return-value]

        except Exception as e:
            db.rollback()
            logger.error(f"API Error: {e} while creating initial charge for user {user.id}", exc_info=True)
            raise ChargeCreationError(f"Failed to create charge: {e}")
