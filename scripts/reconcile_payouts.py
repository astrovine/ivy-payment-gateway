#!/usr/bin/env python3
"""
Usage:
  python scripts/reconcile_payouts.py           # dry run
  python scripts/reconcile_payouts.py --apply   # actually process them
  python scripts/reconcile_payouts.py --id 123  # dry run single payout
  python scripts/reconcile_payouts.py --id 123 --apply  # process single payout

"""
import argparse

from app.utilities.db_con import SessionLocal
from app.models import db_models
from app.services.payout_service import PayoutService


def find_pending_without_ledger(db, limit=None):
    q = db.query(db_models.Payout).filter(db_models.Payout.status == db_models.PayoutStatus.PENDING)
    if limit:
        q = q.limit(limit)
    payouts = q.all()
    results = []
    for p in payouts:
        ledger_count = db.query(db_models.LedgerTransaction).filter(db_models.LedgerTransaction.payout_id == p.id).count()
        if ledger_count == 0:
            results.append(p)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Actually process the payouts (dangerous)')
    parser.add_argument('--id', type=int, help='Process single payout id')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of payouts to inspect')
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.id:
            payout = db.query(db_models.Payout).filter(db_models.Payout.id == args.id).first()
            if not payout:
                print(f"Payout {args.id} not found")
                return
            ledger_count = db.query(db_models.LedgerTransaction).filter(db_models.LedgerTransaction.payout_id == payout.id).count()
            print(f"Payout {payout.id} status={payout.status} amount={payout.amount} currency={payout.currency} ledger_count={ledger_count}")
            if ledger_count == 0 and args.apply:
                print(f"Processing payout {payout.id} now...")
                PayoutService.process_payout_now(db=db, payout_id=payout.id, triggered_by_user_id=None)
                print("Processed")
            elif ledger_count == 0:
                print("Dry-run: would process this payout (use --apply to apply)")
            else:
                print("Ledger rows exist; nothing to do")
            return

        pending = find_pending_without_ledger(db, limit=args.limit)
        if not pending:
            print("No pending payouts without ledger rows found.")
            return

        print(f"Found {len(pending)} pending payouts with no ledger rows")
        for p in pending:
            print(f"- id={p.id} merchant={p.merchant_id} amount={p.amount} currency={p.currency} created_at={p.created_at}")

        if args.apply:
            print("\nApplying processing to each payout (this will modify DB).")
            for p in pending:
                print(f"Processing payout {p.id}...")
                try:
                    PayoutService.process_payout_now(db=db, payout_id=p.id, triggered_by_user_id=None)
                    print(f"Processed {p.id}")
                except Exception as e:
                    print(f"Failed to process {p.id}: {e}")
        else:
            print('\nDry-run only. Use --apply to process found payouts.')
    finally:
        db.close()


if __name__ == '__main__':
    main()

