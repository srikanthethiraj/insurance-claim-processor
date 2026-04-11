"""
Demo script to test the Insurance Claim Processor against your AWS account.

Prerequisites:
  1. AWS credentials configured (aws configure or env vars)
  2. Bedrock model access enabled for amazon.titan-text-express-v1
     (AWS Console → Bedrock → Model access → Request access)
  3. An S3 bucket you can write to

Usage:
  python demo.py --bucket YOUR_BUCKET_NAME [--region us-east-1]
"""

import argparse
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

from src.claim_processor import ClaimProcessor
from src.rag_component import PolicyKnowledgeBase


SAMPLE_CLAIM = """
INSURANCE CLAIM FORM

Claimant Name: Jane Smith
Policy Number: POL-2024-78432
Claim Date: 2024-11-15
Claim Amount: $12,500.00

Incident Description:
On November 14, 2024, a severe storm caused a large tree branch to fall onto
the roof of the insured property at 742 Evergreen Terrace. The impact caused
significant damage to the roof shingles and underlying structure, as well as
water damage to the attic and second-floor bedroom. Emergency tarping was
performed the same day to prevent further water intrusion.

Supporting documents attached: photos of damage, contractor estimate, weather report.
"""


def main():
    parser = argparse.ArgumentParser(description="Test Insurance Claim Processor")
    parser.add_argument("--bucket", required=True, help="S3 bucket name")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--model", default="amazon.titan-text-express-v1", help="Primary Bedrock model ID")
    parser.add_argument(
        "--compare-models",
        nargs="*",
        default=["amazon.titan-text-express-v1", "amazon.titan-text-lite-v1"],
        help="Model IDs to compare (default: titan-text-express + titan-text-lite)",
    )
    args = parser.parse_args()

    print(f"Using bucket:  {args.bucket}")
    print(f"Using region:  {args.region}")
    print(f"Using model:   {args.model}")
    print(f"Comparing:     {', '.join(args.compare_models)}")
    print("-" * 60)

    # Set up a knowledge base with sample policy
    kb = PolicyKnowledgeBase()
    kb.add_policy("POL-2024-78432", "Policy type: Homeowner. Coverage: $500,000. Deductible: $1,000. Covers storm damage.")

    processor = ClaimProcessor(
        s3_bucket=args.bucket,
        model_id=args.model,
        region=args.region,
        knowledge_base=kb,
    )

    # Step 1: Upload
    print("\n[1/3] Uploading sample claim document...")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(SAMPLE_CLAIM)
        tmp_path = f.name

    try:
        upload_result = processor.upload_document(tmp_path)
        print(f"  Uploaded to: s3://{upload_result.bucket}/{upload_result.s3_key}")
    finally:
        os.unlink(tmp_path)

    # Step 2: Process
    print("\n[2/3] Processing document (extract + validate + summarize)...")
    summary = processor.process_document(upload_result.s3_key)

    print(f"\n  Extracted Fields:")
    print(f"    Claimant:    {summary.extracted_fields.claimant_name}")
    print(f"    Date:        {summary.extracted_fields.claim_date}")
    print(f"    Amount:      {summary.extracted_fields.claim_amount}")
    print(f"    Policy:      {summary.extracted_fields.policy_number}")
    print(f"    Description: {summary.extracted_fields.incident_description[:80]}...")

    if summary.validation:
        print(f"\n  Validation: {summary.validation.status}")
        if summary.validation.missing_fields:
            print(f"    Missing: {summary.validation.missing_fields}")

    if summary.narrative_summary:
        print(f"\n  Summary ({len(summary.narrative_summary.split())} words):")
        print(f"    {summary.narrative_summary[:200]}...")

    if summary.warnings:
        print(f"\n  Warnings: {summary.warnings}")

    # Step 3: Compare models
    print(f"\n[3/3] Model comparison — running {len(args.compare_models)} models on the same claim...")
    print(f"  Models: {', '.join(args.compare_models)}")
    comparison = processor.compare_models(upload_result.s3_key, args.compare_models)

    print(f"\n  {'Model':<40} {'Latency':>10} {'Output':>10} {'Status':>10}")
    print(f"  {'-'*40} {'-'*10} {'-'*10} {'-'*10}")
    for r in comparison.results:
        if r.error:
            print(f"  {r.model_id:<40} {'—':>10} {'—':>10} {'FAILED':>10}")
            print(f"    Error: {r.error[:80]}")
        else:
            latency = f"{r.latency_ms:.0f}ms"
            chars = f"{len(r.response_text or '')} chars"
            print(f"  {r.model_id:<40} {latency:>10} {chars:>10} {'OK':>10}")

    # Show a side-by-side snippet of each model's output
    successful = [r for r in comparison.results if not r.error]
    if len(successful) > 1:
        print(f"\n  Output comparison (first 150 chars each):")
        for r in successful:
            snippet = (r.response_text or "")[:150].replace("\n", " ")
            print(f"\n  [{r.model_id}]")
            print(f"    {snippet}...")

    print("\n" + "=" * 60)
    print("Demo complete. Your claim processor is working.")


if __name__ == "__main__":
    main()
