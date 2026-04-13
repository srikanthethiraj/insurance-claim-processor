# Insurance Claim Processor

An AI-powered insurance claim processing application built with Python and Amazon Bedrock. This project automates document ingestion, information extraction, content validation, and summary generation for insurance claims.

This is **Part 1** of a hands-on series on building AI applications with AWS.

## Hey, I'm Srikanth 👋

I'm a cloud engineer at AWS based in Austin, Texas. I've spent years building scalable systems and helping teams ship to production. When generative AI started changing how we build software, I wanted to learn it the way I learn everything — by building real things.

So I created this series. Not slides. Not theory. Just real projects you can clone, run, and learn from.

This first project is an insurance claim processor. It's the kind of thing a real company would need — take messy documents, extract structured data, validate it, and generate summaries using AI. By the time you finish it, you'll understand how to call foundation models, build prompt templates, set up basic RAG, and compare models side by side.

Each article in the series builds on the last. By the end, you'll have built 6 complete projects covering everything from your first Bedrock API call to production-grade RAG systems with governance controls.

Let's get started.

> Follow along on my blog: [blog.srikanthethiraj.com](https://blog.srikanthethiraj.com/)
> Connect with me: [LinkedIn](https://www.linkedin.com/in/srikanthethiraj/)

---

## Why This Matters — Before vs After

Insurance companies process thousands of claims every day. Here's what that looks like with and without AI:

| | Without AI (Manual) | With This System |
|---|---|---|
| **Read a claim document** | Analyst reads the full document (5-10 min) | AI extracts key fields in seconds |
| **Enter data into a form** | Manually type each field — prone to typos | Structured data returned automatically |
| **Handle missing info** | Might not notice a missing field until later | Missing fields flagged instantly as "not found" |
| **Protect sensitive data** | Relies on human judgment to catch SSNs, card numbers | Automatic redaction — sensitive patterns replaced with [REDACTED] |
| **Write a summary** | Analyst writes a paragraph by hand (5-10 min) | AI generates a 300-word summary instantly |
| **Use policy context** | Analyst looks up the policy in another system | RAG automatically pulls in policy details |
| **Process 100 claims** | A full day of repetitive work | Minutes |

### The Pattern You're Learning

This project teaches a pattern that goes far beyond insurance:

> **Unstructured data → AI extraction → Validation → Enrichment → Structured output**

The same approach works for medical records, legal contracts, invoices, support tickets, resumes — any scenario where you need to turn messy documents into clean, usable data. Once you understand this pattern, you can apply it to almost any industry.

## What You'll Learn

- How to call Amazon Bedrock foundation models from Python
- Prompt engineering with reusable templates
- Retrieval-Augmented Generation (RAG) basics
- Structured data extraction from unstructured documents
- Building a component-based AI application

## Architecture

```
┌─────────────────────────────────────────────────┐
│              Claim Processor (Orchestrator)       │
│  upload_document → process_document → compare    │
└──────┬──────────┬───────────┬───────────┬────────┘
       │          │           │           │
  ┌────▼───┐ ┌───▼────┐ ┌───▼────┐ ┌───▼──────┐
  │ Prompt  │ │ Model  │ │Content │ │   RAG    │
  │Template │ │Invoker │ │Validat.│ │Component │
  │Manager  │ │        │ │        │ │          │
  └────────┘ └───┬────┘ └────────┘ └──────────┘
                  │
           ┌──────▼──────┐
           │Amazon Bedrock│
           └─────────────┘
```

## How It Works — The Claim Processing Pipeline

When you upload an insurance claim document, it goes through a 5-step AI pipeline. Here's what happens at each step and why it matters.

```
📄 Claim Document
       │
       ▼
┌──────────────┐
│  1. UPLOAD   │  Store the document safely in Amazon S3
└──────┬───────┘
       ▼
┌──────────────┐
│  2. EXTRACT  │  AI reads the document and pulls out key fields
└──────┬───────┘  (claimant name, date, amount, policy number, description)
       ▼
┌──────────────┐
│  3. VALIDATE │  Check all required fields were found
└──────┬───────┘  Redact sensitive data (SSNs, credit cards, bank accounts)
       ▼
┌──────────────┐
│  4. ENRICH   │  Look up the policy in a knowledge base
└──────┬───────┘  Give the AI extra context for better results (RAG)
       ▼
┌──────────────┐
│ 5. SUMMARIZE │  AI generates a concise narrative summary
└──────┬───────┘  (max 300 words — just the key facts)
       ▼
📋 Claim Summary
```

### Step 1: Upload — Safe Document Storage

The claim document (PDF, image, or text file) gets uploaded to Amazon S3 with a unique timestamped key. This gives you a centralized, durable store for all claim documents.

**What you get:** A reliable record of every document submitted, with a unique identifier for tracking.

### Step 2: Extract — AI Reads the Document

The document text is sent to Amazon Bedrock (an AI foundation model) with a carefully crafted extraction prompt. The AI reads the unstructured text and returns structured data.

**What you get:** Instead of a human reading every claim and typing fields into a form, the AI does it in seconds. It extracts:
- Claimant name
- Claim date
- Claim amount
- Incident description
- Policy number

If a field can't be found, it's marked as "not found" rather than guessed — so you always know what's missing.

### Step 3: Validate — Quality and Privacy Check

The extracted fields are checked for completeness. Then the text is scanned for sensitive patterns (Social Security numbers, credit card numbers, bank account numbers) and any matches are replaced with `[REDACTED]`.

**What you get:** Confidence that every claim has the required information, and that sensitive data never leaks into summaries or reports.

### Step 4: Enrich — Smarter AI with Policy Context (RAG)

This is where Retrieval-Augmented Generation (RAG) comes in. The system looks up the policy number in a knowledge base and feeds that policy context back to the AI along with the claim data.

**What you get:** More accurate and relevant results. Without RAG, the AI only sees the claim document. With RAG, it also knows the policy details (coverage type, deductible, limits) — so it can produce better summaries and flag relevant details.

### Step 5: Summarize — A Concise Narrative

The AI generates a plain-language summary of the claim, capped at 300 words. If summarization fails for any reason, you still get the extracted fields — the system never loses data.

**What you get:** A quick-read summary that a claims analyst can review in 30 seconds instead of reading a multi-page document.

### Bonus: Model Comparison

You can also run the same claim through multiple AI models side-by-side to compare their speed and output quality. This helps you pick the right model for production.

---

## Example Output — What You Get

Here's a real example using the sample water damage claim (`samples/claim_home_water_damage.txt`). This is what the system produces after processing:

### 1. Extracted Fields

The AI reads the raw document and pulls out structured data:

```
Extracted Fields:
  Claimant:    Sarah Chen
  Date:        2024-11-03
  Amount:      $15,200.00
  Policy:      POL-2024-78432
  Description: On November 2, 2024, a pipe burst in the upstairs bathroom...
```

**Why this matters:** A human would spend 5-10 minutes reading the document and typing these into a form. The AI does it in seconds, and the output is consistent every time.

### 2. Validation Report

The system checks that all required fields were found and scans for sensitive data:

```
Validation:
  Status: pass
  Missing fields: none
  Redacted fields: none
```

If the document contained a Social Security number like `123-45-6789`, the system would automatically replace it:

```
Original:  "SSN: 123-45-6789"
After:     "SSN: [REDACTED]"

Validation:
  Status: pass
  Redacted fields: [ssn]
```

If a required field was missing from the document:

```
Extracted Fields:
  Amount: not found

Validation:
  Status: fail
  Missing fields: [claim_amount]
```

**Why this matters:** You never have to worry about incomplete data slipping through or sensitive information ending up in reports. The system catches both automatically.

### 3. Narrative Summary

The AI generates a concise, readable summary (max 300 words):

```
Summary:
  Sarah Chen filed a homeowner insurance claim on November 3, 2024, for
  $15,200 in damages resulting from a burst pipe in the upstairs bathroom
  of her property at 1847 Maple Drive. The incident occurred on November 2
  when a pipe failure caused water to flood the bathroom floor and seep
  through to the kitchen below, damaging the ceiling and cabinets. An
  emergency plumber and water mitigation company were engaged immediately.
  The claim covers plumbing repair, water mitigation, bathroom floor
  replacement, kitchen ceiling repair, and cabinet replacement. Policy
  POL-2024-78432 provides homeowner coverage with a $1,000 deductible.
```

**Why this matters:** A claims analyst can review this in 30 seconds instead of reading a multi-page document. Notice how the summary includes the policy context (coverage type, deductible) — that came from the RAG enrichment step.

### 4. Model Comparison

Run the same claim through multiple AI models to compare performance:

```
Model                                      Latency     Output     Status
---------------------------------------- ---------- ---------- ----------
amazon.nova-lite-v1:0                        705ms  539 chars         OK
amazon.nova-micro-v1:0                       517ms  527 chars         OK

Output comparison (first 150 chars each):

[amazon.nova-lite-v1:0]
  Jane Smith filed a homeowner insurance claim on November 15, 2024, for $12,500
  in damages resulting from a severe storm...

[amazon.nova-micro-v1:0]
  Claim filed by Jane Smith on 2024-11-15 for storm damage totaling $12,500.
  A large tree branch fell onto the roof...
```

**Why this matters:** Different models have different strengths. Nova Lite gives more detailed output, while Nova Micro is faster and cheaper. This comparison helps you make an informed choice for production use.

---

## Prerequisites

Before you start, you'll need:

1. **Python 3.10+** installed on your machine
2. **An AWS account** with access to Amazon Bedrock
3. **AWS CLI** installed and configured

If you don't have these yet, follow the steps below.

---

## Step-by-Step Setup Guide

### Step 1: Install Python

Check if Python is installed:

```bash
python3 --version
```

If not installed, download from [python.org](https://www.python.org/downloads/) or use Homebrew on macOS:

```bash
brew install python@3.13
```

### Step 2: Install the AWS CLI

Check if the AWS CLI is installed:

```bash
aws --version
```

If not installed, follow the [AWS CLI installation guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).

On macOS:

```bash
brew install awscli
```

### Step 3: Configure AWS Credentials

Run the configure command and enter your Access Key ID, Secret Access Key, and preferred region:

```bash
aws configure
```

```
AWS Access Key ID [None]: YOUR_ACCESS_KEY
AWS Secret Access Key [None]: YOUR_SECRET_KEY
Default region name [None]: us-east-1
Default output format [None]: json
```

> **Don't have an access key?** Go to the AWS Console → IAM → Users → your user → Security credentials → Create access key.

Verify it works:

```bash
aws sts get-caller-identity
```

You should see your account ID and user ARN.

### Step 4: Enable Amazon Bedrock Model Access

This is the step most people miss. You need to explicitly enable the models you want to use.

1. Go to the [AWS Console](https://console.aws.amazon.com/)
2. Navigate to **Amazon Bedrock** (search for it in the top bar)
3. Make sure you're in the **us-east-1** region (top-right dropdown)
4. In the left sidebar, click **Model access**
5. Click **Manage model access**
6. Find **Amazon → Nova Lite** and **Amazon → Nova Micro** and check both boxes
7. Click **Save changes**
8. Wait 1-2 minutes for it to activate — the status should change to **Access granted**

### Step 5: Create an S3 Bucket

The processor stores claim documents in S3. Create a bucket:

```bash
aws s3 mb s3://my-claim-docs-test --region us-east-1
```

> **Note:** Bucket names must be globally unique. Replace `my-claim-docs-test` with something unique like `claim-docs-YOURINITIALS-2024`.

### Step 6: Clone and Set Up the Project

```bash
git clone https://github.com/YOUR_USERNAME/insurance-claim-processor.git
cd insurance-claim-processor
```

Create a virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 7: Run the Demo

The project includes sample claim files in the `samples/` folder that you can use to test:

```
samples/
├── claim_auto_accident.txt      # Car rear-ended at intersection
├── claim_home_water_damage.txt  # Burst pipe with water damage
└── claim_medical.txt            # Slip-and-fall injury claim
```

Run the demo with the built-in sample claim:

```bash
python3 demo.py --bucket YOUR_BUCKET_NAME
```

Replace `YOUR_BUCKET_NAME` with the bucket you created in Step 5.

You should see output like:

```
Using bucket:  my-claim-docs-test
Using region:  us-east-1
Using model:   amazon.nova-lite-v1:0
Comparing:     amazon.nova-lite-v1:0, amazon.nova-micro-v1:0
------------------------------------------------------------

[1/3] Uploading sample claim document...
  Uploaded to: s3://my-claim-docs-test/claims/20241115T143022Z/claim.txt

[2/3] Processing document (extract + validate + summarize)...

  Extracted Fields:
    Claimant:    Jane Smith
    Date:        2024-11-15
    Amount:      $12,500.00
    Policy:      POL-2024-78432
    Description: On November 14, 2024, a severe storm caused a large tree branch...

  Validation: pass

  Summary (87 words):
    Jane Smith filed a homeowner insurance claim on November 15, 2024...

[3/3] Model comparison — running 2 models on the same claim...
  Models: amazon.nova-lite-v1:0, amazon.nova-micro-v1:0

  Model                                      Latency     Output     Status
  ---------------------------------------- ---------- ---------- ----------
  amazon.nova-lite-v1:0                        705ms  539 chars         OK
  amazon.nova-micro-v1:0                       517ms  527 chars         OK

============================================================
Demo complete. Your claim processor is working.
```

---

## Troubleshooting

| Error | Fix |
|---|---|
| `NoCredentialError` | Run `aws configure` and enter your credentials |
| `AccessDeniedException` on Bedrock | Enable model access in the Bedrock console (Step 4) |
| `NoSuchBucket` | Create the S3 bucket first (Step 5) |
| `AccessDenied` on S3 | Your IAM user needs `s3:PutObject` and `s3:GetObject` permissions |
| `ModuleNotFoundError` | Activate your venv and run `pip install -r requirements.txt` |

## Project Structure

```
insurance-claim-processor/
├── samples/                      # Sample claim documents for testing
│   ├── claim_auto_accident.txt
│   ├── claim_home_water_damage.txt
│   └── claim_medical.txt
├── src/
│   ├── claim_processor.py        # Main orchestrator
│   ├── prompt_template_manager.py # Prompt template management
│   ├── model_invoker.py          # Bedrock model invocation with retry
│   ├── content_validator.py      # Field validation and PII redaction
│   ├── rag_component.py          # RAG enrichment with policy context
│   ├── models.py                 # Data classes
│   ├── exceptions.py             # Error hierarchy
│   ├── web_interface.py          # Optional Flask UI
│   └── feedback.py               # Optional feedback mechanism
├── tests/                        # Test directories
├── demo.py                       # Demo script to test with your AWS account
├── requirements.txt              # Python dependencies
└── README.md
```

## What's Next in the Series

This is Part 1 of a hands-on series where you'll build progressively more complex AI applications on AWS. Each project teaches new skills while building on what you learned before.

| Part | Project | What You'll Build | Skills You'll Gain |
|---|---|---|---|
| **1** | **Insurance Claim Processor** (this project) | AI-powered document extraction and summarization | Bedrock basics, prompt templates, simple RAG, model comparison |
| **2** | **Financial Services AI Assistant** | Customer service assistant with dynamic model selection | Model benchmarking, Lambda abstraction layers, AppConfig, circuit breakers, cross-region resilience |
| **3** | **Customer Feedback Pipeline** | Multimodal data processing from text, images, audio, and surveys | Glue Data Quality, Comprehend, Textract, Transcribe, data formatting for FMs |
| **4** | **Knowledge Base RAG System** | Full RAG system with vector stores and embeddings | Bedrock Knowledge Bases, OpenSearch, DynamoDB, document chunking, embedding pipelines, data maintenance |
| **5** | **Advanced Search & Retrieval** | Optimized search with hybrid strategies and reranking | Chunking strategies, embedding model comparison, hybrid search, query expansion, function calling |
| **6** | **AI Support Assistant with Governance** | Production AI assistant with safety controls and prompt management | Bedrock Guardrails, Prompt Management, Prompt Flows, conversation workflows, QA testing, feedback loops |

Each project is a standalone GitHub repo you can clone and run. Start with Part 1 and work your way through, or jump to whichever topic interests you most.

## License

MIT
