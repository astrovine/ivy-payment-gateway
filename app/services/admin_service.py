from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_

from ..models import db_models
from ..utilities.exceptions import (
    MerchantAccountNotFoundError,
    PermissionDeniedError,
    VerificationError,
)
from ..utilities.logger import setup_logger

logger = setup_logger(__name__)


class AdminService:
    @staticmethod
    def verify_admin(user: db_models.User):
        if not user.is_superadmin:
            logger.warning(f'Non-admin user {user.id} ({user.email}) attempted to access admin functionality')
            raise PermissionDeniedError("Admin access required")
        return True

    @staticmethod
    def get_all_merchants(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None):
        try:
            logger.info(f'Fetching merchants list (skip={skip}, limit={limit}, search={search})')

            query = db.query(db_models.MerchantAccount).options(
                joinedload(db_models.MerchantAccount.user_info)
            )

            if search:
                query = query.join(db_models.User).filter(
                    or_(
                        db_models.User.email.ilike(f'%{search}%'),
                        db_models.User.name.ilike(f'%{search}%'),
                        db_models.MerchantAccount.merchant_id.ilike(f'%{search}%')
                    )
                )

            total = query.count()
            merchants = query.order_by(desc(db_models.MerchantAccount.created_at)).offset(skip).limit(limit).all()

            logger.info(f'Retrieved {len(merchants)} merchants (total: {total})')
            return {"total": total, "merchants": merchants}

        except Exception as e:
            logger.error(f'Error fetching merchants list: {e}', exc_info=True)
            raise

    @staticmethod
    def get_merchant_by_id(db: Session, merchant_id: str):
        try:
            logger.info(f'Fetching merchant details for {merchant_id}')

            merchant = db.query(db_models.MerchantAccount).options(
                joinedload(db_models.MerchantAccount.user_info)
            ).filter_by(merchant_id=merchant_id).first()

            if not merchant:
                logger.warning(f'Merchant {merchant_id} not found')
                raise MerchantAccountNotFoundError(f"Merchant {merchant_id} not found")

            user = merchant.user_info
            verified_info = db.query(db_models.UserVerified).filter_by(user_id=user.id).first()
            kyc_status = db.query(db_models.KYCVerification).filter_by(user_id=user.id).first()
            kyc_documents = db.query(db_models.KYCDocument).filter_by(user_id=user.id).all()
            identity = db.query(db_models.IdentityVerification).filter_by(user_id=user.id).first()
            business = db.query(db_models.BusinessVerification).filter_by(user_id=user.id).first()

            logger.info(f'Successfully retrieved merchant {merchant_id} details')
            return {
                "merchant": merchant,
                "user": user,
                "verified_info": verified_info,
                "kyc_status": kyc_status,
                "kyc_documents": kyc_documents,
                "identity_verification": identity,
                "business_verification": business
            }

        except Exception as e:
            logger.error(f'Error fetching merchant {merchant_id}: {e}', exc_info=True)
            raise

    @staticmethod
    def update_merchant_status(db: Session, merchant_id: str, status: str, admin_user: db_models.User):
        try:
            AdminService.verify_admin(admin_user)
            logger.info(f'Admin {admin_user.id} updating merchant {merchant_id} status to {status}')

            merchant = db.query(db_models.MerchantAccount).filter_by(merchant_id=merchant_id).first()
            if not merchant:
                raise MerchantAccountNotFoundError(f"Merchant {merchant_id} not found")

            old_status = merchant.account_status.value
            merchant.account_status = db_models.AccountStatus[status]
            db.commit()

            logger.info(f'Merchant {merchant_id} status updated from {old_status} to {status} by admin {admin_user.id}')
            return merchant

        except Exception as e:
            db.rollback()
            logger.error(f'Error updating merchant {merchant_id} status: {e}', exc_info=True)
            raise

    @staticmethod
    def update_risk_assessment(db: Session, merchant_id: str, risk_data: dict, admin_user: db_models.User):
        try:
            AdminService.verify_admin(admin_user)
            logger.info(f'Admin {admin_user.id} updating risk assessment for merchant {merchant_id}')

            merchant = db.query(db_models.MerchantAccount).filter_by(merchant_id=merchant_id).first()
            if not merchant:
                raise MerchantAccountNotFoundError(f"Merchant {merchant_id} not found")

            risk_assessment = db_models.RiskAssessment(
                merchant_id=merchant_id,
                risk_level=db_models.RiskLevel[risk_data['risk_level']],
                risk_factors=','.join(risk_data.get('risk_factors', [])),
                review_required=risk_data.get('review_required', False),
                notes=risk_data.get('notes'),
                assessed_by=admin_user.id
            )

            merchant.risk_level = db_models.RiskLevel[risk_data['risk_level']]

            db.add(risk_assessment)
            db.commit()
            db.refresh(risk_assessment)

            logger.info(f'Risk assessment updated for merchant {merchant_id} by admin {admin_user.id}')
            return risk_assessment

        except Exception as e:
            db.rollback()
            logger.error(f'Error updating risk assessment for merchant {merchant_id}: {e}', exc_info=True)
            raise

    @staticmethod
    def approve_kyc(db: Session, user_id: int, admin_user: db_models.User):
        try:
            AdminService.verify_admin(admin_user)
            logger.info(f'Admin {admin_user.id} approving KYC for user {user_id}')

            kyc_verification = db.query(db_models.KYCVerification).filter_by(user_id=user_id).first()
            if not kyc_verification:
                raise VerificationError("No KYC verification found for this user")

            kyc_verification.kyc_status = db_models.KYCStatus.verified
            kyc_verification.verified_at = datetime.now()
            kyc_verification.reviewed_by = admin_user.id
            kyc_verification.rejection_reason = None

            merchant = db.query(db_models.MerchantAccount).filter_by(user_id=user_id).first()
            if merchant:
                merchant.kyc_status = db_models.KYCStatus.verified
                merchant.kyc_verified_at = datetime.now()
                merchant.verification_status = db_models.VerificationStatus.verified
                logger.info(f'Updated merchant {merchant.merchant_id} KYC and verification status to verified')

            db.commit()
            logger.info(f'KYC approved for user {user_id} by admin {admin_user.id}')
            return kyc_verification

        except Exception as e:
            db.rollback()
            logger.error(f'Error approving KYC for user {user_id}: {e}', exc_info=True)
            raise

    @staticmethod
    def reject_kyc(db: Session, user_id: int, rejection_reason: str, admin_user: db_models.User):
        try:
            AdminService.verify_admin(admin_user)
            logger.info(f'Admin {admin_user.id} rejecting KYC for user {user_id}')

            kyc_verification = db.query(db_models.KYCVerification).filter_by(user_id=user_id).first()
            if not kyc_verification:
                raise VerificationError("No KYC verification found for this user")

            kyc_verification.kyc_status = db_models.KYCStatus.failed
            kyc_verification.rejection_reason = rejection_reason
            kyc_verification.reviewed_by = admin_user.id

            merchant = db.query(db_models.MerchantAccount).filter_by(user_id=user_id).first()
            if merchant:
                merchant.kyc_status = db_models.KYCStatus.failed
                merchant.verification_status = db_models.VerificationStatus.rejected
                logger.info(f'Updated merchant {merchant.merchant_id} KYC status to failed')

            db.commit()
            logger.info(f'KYC rejected for user {user_id} by admin {admin_user.id}. Reason: {rejection_reason}')
            return kyc_verification

        except Exception as e:
            db.rollback()
            logger.error(f'Error rejecting KYC for user {user_id}: {e}', exc_info=True)
            raise

    @staticmethod
    def get_all_transactions(db: Session, skip: int = 0, limit: int = 100, merchant_id: Optional[str] = None):
        try:
            logger.info(f'Admin fetching transactions (skip={skip}, limit={limit}, merchant_id={merchant_id})')

            query = db.query(db_models.Charge).options(joinedload(db_models.Charge.user))

            if merchant_id:
                user = db.query(db_models.User).join(db_models.MerchantAccount).filter(
                    db_models.MerchantAccount.merchant_id == merchant_id
                ).first()
                if user:
                    query = query.filter(db_models.Charge.user_id == user.id)

            total = query.count()
            transactions = query.order_by(desc(db_models.Charge.created_at)).offset(skip).limit(limit).all()

            logger.info(f'Retrieved {len(transactions)} transactions (total: {total})')
            return {"total": total, "transactions": transactions}

        except Exception as e:
            logger.error(f'Error fetching transactions: {e}', exc_info=True)
            raise

    @staticmethod
    def get_all_payouts(db: Session, skip: int = 0, limit: int = 100, merchant_id: Optional[str] = None):
        try:
            logger.info(f'Admin fetching payouts (skip={skip}, limit={limit}, merchant_id={merchant_id})')

            query = db.query(db_models.Payout)

            if merchant_id:
                query = query.filter(db_models.Payout.merchant_id == merchant_id)

            total = query.count()
            payouts = query.order_by(desc(db_models.Payout.created_at)).offset(skip).limit(limit).all()

            logger.info(f'Retrieved {len(payouts)} payouts (total: {total})')
            return {"total": total, "payouts": payouts}

        except Exception as e:
            logger.error(f'Error fetching payouts: {e}', exc_info=True)
            raise

    @staticmethod
    def get_audit_logs(db: Session, skip: int = 0, limit: int = 100, user_id: Optional[int] = None, action: Optional[str] = None):
        try:
            logger.info(f'Admin fetching audit logs (skip={skip}, limit={limit}, user_id={user_id}, action={action})')

            query = db.query(db_models.AuditLog)

            if user_id:
                query = query.filter(db_models.AuditLog.user_id == user_id)
            if action:
                query = query.filter(db_models.AuditLog.action.ilike(f'%{action}%'))

            total = query.count()
            logs = query.order_by(desc(db_models.AuditLog.created_at)).offset(skip).limit(limit).all()

            logger.info(f'Retrieved {len(logs)} audit logs (total: {total})')
            return {"total": total, "logs": logs}

        except Exception as e:
            logger.error(f'Error fetching audit logs: {e}', exc_info=True)
            raise
