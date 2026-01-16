import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime


class TestProcessChargeTask:
    @patch('app.tasks.SessionLocal')
    def test_process_charge_success(self, mock_session_local):
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        mock_charge = MagicMock()
        mock_charge.id = "ch_test123"
        mock_charge.status = "pending"
        mock_charge.amount = Decimal("100.00")
        mock_charge.currency = "NGN"
        mock_charge.user_id = 1
        mock_db.query.return_value.filter_by.return_value.with_for_update.return_value.first.return_value = mock_charge
        
        mock_merchant = MagicMock()
        mock_merchant.merchant_id = "m_test"
        mock_merchant.currency = "NGN"
        mock_merchant.user_id = 1
        
        mock_system_holding = MagicMock()
        mock_system_holding.id = 1
        mock_system_holding.balance = Decimal("0")
        
        mock_platform_revenue = MagicMock()
        mock_platform_revenue.id = 2
        mock_platform_revenue.balance = Decimal("0")
        
        mock_merchant_pending = MagicMock()
        mock_merchant_pending.id = 3
        mock_merchant_pending.balance = Decimal("0")
        
        from app.tasks import process_charge_task
        
        with patch.object(mock_db, 'query') as mock_query:
            mock_query.return_value.filter_by.return_value.with_for_update.return_value.first.side_effect = [
                mock_charge,
                mock_merchant,
                mock_system_holding,
                mock_platform_revenue,
                mock_merchant_pending
            ]
            mock_query.return_value.filter_by.return_value.all.return_value = []
            
    def test_process_charge_not_found(self):
        with patch('app.tasks.SessionLocal') as mock_session_local:
            mock_db = MagicMock()
            mock_session_local.return_value = mock_db
            mock_db.query.return_value.filter_by.return_value.with_for_update.return_value.first.return_value = None
            
            from app.tasks import process_charge_task
            result = process_charge_task("nonexistent", "tok_valid_success")

    def test_process_charge_already_processed(self):
        with patch('app.tasks.SessionLocal') as mock_session_local:
            mock_db = MagicMock()
            mock_session_local.return_value = mock_db
            
            mock_charge = MagicMock()
            mock_charge.status = "succeeded"
            mock_db.query.return_value.filter_by.return_value.with_for_update.return_value.first.return_value = mock_charge
            
            from app.tasks import process_charge_task
            result = process_charge_task("ch_test", "tok_valid_success")


class TestSettlePendingFundsTask:
    @patch('app.tasks.SessionLocal')
    def test_settle_no_merchants(self, mock_session_local):
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.all.return_value = []
        
        from app.tasks import settle_pending_funds_task
        settle_pending_funds_task()
        mock_db.commit.assert_called()


class TestProcessPayoutTask:
    @patch('app.tasks.SessionLocal')
    def test_payout_not_found(self, mock_session_local):
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter_by.return_value.with_for_update.return_value.first.return_value = None
        
        from app.tasks import process_payout_task
        result = process_payout_task("nonexistent")


class TestProcessWebhookDelivery:
    @patch('app.tasks.SessionLocal')
    @patch('app.tasks.httpx.Client')
    def test_webhook_delivery_success(self, mock_client, mock_session_local):
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        mock_delivery = MagicMock()
        mock_delivery.id = 1
        mock_delivery.webhook_id = 1
        mock_delivery.event = "charge.succeeded"
        mock_delivery.payload = '{"test": "data"}'
        mock_delivery.attempts = 0
        
        mock_webhook = MagicMock()
        mock_webhook.id = 1
        mock_webhook.enabled = True
        mock_webhook.url = "https://example.com/webhook"
        mock_webhook.merchant_id = "m_test"
        
        mock_db.query.return_value.filter_by.return_value.with_for_update.return_value.first.return_value = mock_delivery
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_webhook
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response
        
        from app.tasks import process_webhook_delivery
        process_webhook_delivery(1)
        
        assert mock_delivery.status == 'success'
        mock_db.commit.assert_called()

    @patch('app.tasks.SessionLocal')
    def test_webhook_delivery_not_found(self, mock_session_local):
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter_by.return_value.with_for_update.return_value.first.return_value = None
        
        from app.tasks import process_webhook_delivery
        result = process_webhook_delivery(999)
