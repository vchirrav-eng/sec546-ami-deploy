# SEC546 Lab VM — Deploy to Your Own AWS Account

This repository lets a SEC546 student launch the official SANS SEC546 lab VM in
their **own AWS account** using a GitHub Actions workflow. No local AWS CLI, no
Terraform, no manual console clicking beyond the initial setup.

You run one workflow, wait a couple of minutes, and download a **connection
package** containing your SmartProxy config, the lab CA certificate, and your
personal SSH key. You then set Firefox up with those artifacts by following the
**lab setup guide provided during class** — that guide, not this repository, is
the reference for actually running the labs.

> **Region: `us-east-2` (US East / Ohio) throughout.**
> AMIs are region-scoped. SANS shares the SEC546 AMI in `us-east-2`, so the VM
> must be launched in `us-east-2`. Both workflows default to this region — do
> not change it unless SANS tells you the AMI lives elsewhere.

---

## Before you start — prerequisites

| # | Requirement | Notes |
|---|-------------|-------|
| 1 | An AWS account you control | Personal or employer-sanctioned. You pay for the EC2 instance. |
| 2 | Your 12-digit AWS account ID | Top-right of the AWS console, or `aws sts get-caller-identity` |
| 3 | **SANS has shared the SEC546 AMI with that account ID in `us-east-2`** | See [Step 1](#step-1--get-the-ami-shared-with-your-aws-account). Nothing works without this. |
| 4 | A GitHub account | Free tier is fine. Actions minutes on a public repo are unlimited. |
| 5 | Firefox with the SmartProxy extension | How you reach the lab targets. Configure it per your class lab setup guide. |
| 6 | An SSH client | *Optional* — only for troubleshooting a broken setup. Built into Windows 10+, macOS, and Linux. |

**Cost warning.** The VM is an `m6i.2xlarge` (8 vCPU / 32 GB) with a 100 GB gp3
root volume, in `us-east-2`. That is roughly **$0.38/hour** for compute plus
about **$8/month** for storage — call it **~$3–4 for an 8-hour class day**.
The VM **keeps running after the workflow finishes**. You are billed until you
terminate it. See [Step 6](#step-6--tear-the-lab-down-when-youre-done).

---

## Step 1 — Get the AMI shared with your AWS account

This is the one step you cannot do yourself.

1. Find your **12-digit AWS account ID**:
   - AWS Console → click your account name (top right) → the number under *Account ID*, or
   - `aws sts get-caller-identity --query Account --output text`
2. Send that account ID to your SANS instructor or course support contact and
   ask them to share the **latest SEC546 lab AMI** in region **`us-east-2`**.
3. SANS replies with an **AMI ID** that looks like `ami-0a1b2c3d4e5f67890`.
   **Save it — you need it in Step 5.**
4. Confirm the share reached you. In the AWS Console, switch the region selector
   to **US East (Ohio) us-east-2**, then go to
   **EC2 → Images → AMIs** and change the filter dropdown from *Owned by me* to
   **Private images**. The SEC546 AMI should be listed with state `available`.

   Or from a terminal:

   ```bash
   aws ec2 describe-images \
     --image-ids ami-0a1b2c3d4e5f67890 \
     --region us-east-2 \
     --query "Images[0].[ImageId,Name,State]" --output table
   ```

> **`InvalidAMIID.NotFound`?** The share has not been applied. Go back to SANS —
> do not continue, the workflow will fail at its AMI validation step.

---

## Step 2 — Create an IAM user for the workflow

GitHub Actions needs AWS credentials. Create a dedicated IAM user so you can
delete it after class without touching anything else.

1. AWS Console → **IAM → Users → Create user**.
2. Name it `sec546-github-actions`. **Do not** enable console access.
3. On the permissions screen choose **Attach policies directly**, then
   **Create policy → JSON**, and paste the contents of
   [`infra/iam/sec546-lab-policy.json`](infra/iam/sec546-lab-policy.json)
   from this repo. Name the policy `SEC546LabDeploy` and attach it to the user.

   <details>
   <summary>Shortcut for a throwaway personal account</summary>

   You can attach the AWS-managed `AmazonEC2FullAccess` policy instead. It is
   broader than needed. Never do this in an employer account.
   </details>

4. Open the new user → **Security credentials → Access keys → Create access key**
   → choose **Third-party service** → create.
5. Copy the **Access key ID** and **Secret access key** now. The secret is shown
   exactly once.

---

## Step 3 — Create your own copy of this repository

You need your **own** repo so the workflows run under your account with your
secrets.

### Option A — Fork (easiest)

Click **Fork** at the top of this repository page. Then in your fork go to the
**Actions** tab and click **I understand my workflows, go ahead and enable them**
(forks have Actions disabled by default).

### Option B — Clone and push to a fresh repo (recommended)

A fresh private repo keeps your lab work separate from the public upstream.

```bash
git clone https://github.com/<UPSTREAM-OWNER>/sec546-ami-deploy.git
cd sec546-ami-deploy

# Point at your own new (empty) GitHub repo
git remote set-url origin https://github.com/<YOUR-GITHUB-USERNAME>/<YOUR-REPO>.git
git push -u origin main
```

> **Make it private if you can.** The workflow's artifact contains your private
> SSH key. Artifacts are only visible to people with repo access, so a private
> repo is the safer default. Public repos do get unlimited free Actions minutes,
> which is the only reason to prefer public.

---

## Step 4 — Add your AWS credentials as GitHub secrets

In **your** repo: **Settings → Secrets and variables → Actions →
New repository secret**. Add these two, named **exactly** as shown:

| Secret name | Value |
|-------------|-------|
| `AWS_ACCESS_KEY_ID` | The access key ID from Step 2 |
| `AWS_SECRET_ACCESS_KEY` | The secret access key from Step 2 |

The region is **not** a secret — it is set to `us-east-2` inside the workflow.

> Secrets are write-only. GitHub masks them in logs and you can never read them
> back — if you lose them, delete the access key in IAM and create a new one.

---

## Step 5 — Run the deploy workflow

1. In your repo, open the **Actions** tab.
2. Select **Deploy Student VM** in the left sidebar.
3. Click **Run workflow** (top right) and fill in:

   | Input | Value |
   |-------|-------|
   | **ami_id** | The `ami-...` ID SANS gave you in Step 1 |
   | **course** | `5-day (L02)` or `2-day (main)` — a label only; the AMI decides the actual content |

4. Click the green **Run workflow** button.

The job takes roughly **3–5 minutes**. It will:

- validate the AMI ID format and confirm the AMI is `available` in your account
- find (or create) your default VPC in `us-east-2`
- create a security group `sec546-student-sg-<run_number>` opening TCP
  **22, 80, 443, 1080** to `0.0.0.0/0`
- generate a fresh ed25519 SSH keypair and import the public half to AWS
- launch one `m6i.2xlarge` with a 100 GB gp3 root volume, tagged
  `DeployRun=<run_number>`
- build your connection package and upload it as a workflow artifact

When it finishes, open the run's **Summary** page. It shows your **Public IP**,
**Instance ID**, and **run number** — write the run number down, you need it to
tear things down.

### Download and unpack your connection package

At the bottom of the run Summary, under **Artifacts**, download
**`sec546-student-package-run<N>.zip`**. It contains:

| File | What to do with it |
|------|--------------------|
| `smartproxy-sec546.json` | SmartProxy configuration for Firefox. Your VM's IP is already filled in. |
| `sec546-cloud-ca.der` | The lab CA certificate, for Firefox to trust the lab sites. |
| `sec546-student.key` | Your private SSH key. **Not needed for normal lab work** — see [Optional: connect over SSH](#optional--connect-to-the-vm-over-ssh). |
| `README` | A short quickstart. |

> **Do not commit these files.** The package contains your private SSH key and a
> proxy config with your VM's IP. This repo ships a `.gitignore` that already
> excludes them by name, so unzipping the package inside your clone is safe — but
> never use `git add -f` on them, and if you unzip somewhere else, keep them out
> of any other repository too.

### Set up Firefox — follow your class lab setup guide

> **Use the SEC546 lab setup guide provided during class** for the steps to
> import `smartproxy-sec546.json` and `sec546-cloud-ca.der` into Firefox and to
> work through the labs. That guide is the authoritative reference for using
> these artifacts — this repository only covers getting the VM running and
> producing the package.

Once Firefox is configured per that guide, you browse the lab targets through
the VM and **you are done with this repository** until it is time to tear the
lab down in Step 6.

---

## Optional — connect to the VM over SSH

> **You do not need SSH for normal lab work.** Everything in the course is done
> through Firefox using the artifacts above. Use SSH only if something is wrong
> with the setup and you or your instructor need to inspect the VM directly.

```bash
chmod 600 sec546-student.key
ssh -i sec546-student.key ubuntu@<PUBLIC-IP-FROM-THE-SUMMARY>
```

On Windows PowerShell, `chmod` does not exist — if SSH complains the key is too
open, lock the file down with `icacls`:

```powershell
icacls .\sec546-student.key /inheritance:r /grant:r "$env:USERNAME:(R)"
```

---

## Step 6 — Tear the lab down when you're done

**Do this at the end of every class day you are not returning to.** The VM bills
by the hour whether or not you are using it.

1. **Actions → Delete Student VM → Run workflow**.
2. Enter the **deploy_run_number** — the run number of the *Deploy Student VM*
   run from Step 5 (shown in its summary and in the artifact name).
3. Leave **region** as `us-east-2`.

The workflow terminates the instance, waits for it to fully terminate, then
deletes the security group and the key pair for that run.

Afterwards, confirm nothing is left: EC2 console → **Instances** in `us-east-2`,
filter by tag `Project = sec546`. Anything not in state `terminated` is still
costing you money.

Also delete the IAM access key from Step 2 once the course is over
(**IAM → Users → `sec546-github-actions` → Security credentials → Delete**).

---

## Optional — if the SANS LLM API key stops working

Several SEC546 labs call an LLM. The AMI is configured to reach a **SANS-provided
LiteLLM endpoint** using a **SANS-provided API key**, which your class lab setup
guide tells you how to set.

> **Keep using the SANS endpoint and key for as long as they work — that is the
> first preference.** The same key you used in class also works on the VM you
> deploy into your own AWS account, and it normally keeps working for **a few
> days after the course ends**. Carry it over from your class setup and change
> nothing.
>
> **The SANS endpoint itself should remain available, but the key will expire.**
> There is **no refreshed key** — once it stops, it is done. If your LLM-backed
> labs start failing with `401 Unauthorized`, `403 Forbidden`, or an
> authentication error, that is what has happened.
>
> **Only then** set up your own Bedrock access below.

When that day comes, the fallback is to point the labs at **your own AWS Bedrock
account** instead, using these models:

| Model ID | Notes |
|----------|-------|
| `openai.gpt-oss-20b-1:0` | The model most labs use |
| `openai.gpt-oss-safeguard-120b` | Larger safeguard variant |
| `us.amazon.nova-2-lite-v1:0` | Amazon Nova. The `us.` prefix means this is a **cross-region inference profile**, not a plain model ID — request access to it by that exact string |

**You pay for your own Bedrock usage.** These models are inexpensive for lab-sized
prompts, but the cost is yours, not SANS's.

### Step 1 — Enable the models in Bedrock

In the AWS console → **Bedrock → Model access**, request access to all three IDs
above. Approval for these is typically immediate.

> **Region matters.** These models are **not** offered in `us-east-2`, where your
> lab VM runs. Use **`us-east-1`** and expect your LLM calls to cross regions —
> this is normal and adds only latency. Set your console region to `us-east-1`
> before requesting access, or you will not see the models listed.

### Step 2 — Create credentials

Create an IAM user (or reuse the one from Step 2 of the main setup) with
`bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream` on `*`, then
generate an access key. Bedrock's OpenAI-compatible endpoint authenticates with a
**Bedrock API key**, which you generate under
**Bedrock → API keys** — this is what you will use as your LLM API key.

### Step 3 — Point the labs at your own endpoint

The AMI reads the endpoint and key from environment variables in a `.env` file on
the VM. **Check your class lab setup guide for the exact path** — it varies by lab
and by AMI build. Replace the SANS values with your own:

```bash
# Your own Bedrock endpoint, replacing the SANS LiteLLM endpoint
OPENAI_BASE_URL=https://bedrock-runtime.us-east-1.amazonaws.com/openai/v1
OPENAI_API_KEY=<YOUR-BEDROCK-API-KEY>
OPENAI_MODEL=openai.gpt-oss-20b-1:0
```

Some labs use `LITELLM_BASE_URL` / `LITELLM_API_KEY`, or pass the endpoint as a
tool flag, instead of the `OPENAI_*` names above. Match whatever names your lab
guide and the existing `.env` already use — **replace the values, do not rename
the variables.** Restart the lab tool or service after editing so it re-reads the
file.

Verify the endpoint answers before returning to the lab:

```bash
curl -s https://bedrock-runtime.us-east-1.amazonaws.com/openai/v1/chat/completions \
  -H "Authorization: Bearer ${OPENAI_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"model":"openai.gpt-oss-20b-1:0","messages":[{"role":"user","content":"ping"}]}'
```

A JSON reply containing `choices` means you are working again. `401`/`403` means
the key is wrong; `AccessDeniedException` means model access was not granted in
Step 1.

### If a lab needs a real LiteLLM proxy

A few labs depend on LiteLLM-specific behaviour (virtual keys, request logging, or
routing across several models) and will not work against Bedrock directly. In that
case run your own LiteLLM proxy on the lab VM:

```bash
# On the lab VM
cat > litellm-config.yaml << 'YAML'
model_list:
  - model_name: gpt-oss-20b
    litellm_params:
      model: bedrock/openai.gpt-oss-20b-1:0
      aws_region_name: us-east-1
  - model_name: nova-2-lite
    litellm_params:
      model: bedrock/us.amazon.nova-2-lite-v1:0
      aws_region_name: us-east-1
YAML

docker run -d --name litellm -p 4000:4000 \
  -e AWS_ACCESS_KEY_ID=<YOUR-KEY-ID> \
  -e AWS_SECRET_ACCESS_KEY=<YOUR-SECRET> \
  -e LITELLM_MASTER_KEY=sk-my-lab-key \
  -v "$(pwd)/litellm-config.yaml:/app/config.yaml" \
  ghcr.io/berriai/litellm:main-latest --config /app/config.yaml
```

Then set `OPENAI_BASE_URL=http://localhost:4000/v1` and
`OPENAI_API_KEY=sk-my-lab-key` in the `.env`. Note this uses IAM access keys
rather than a Bedrock API key, and the proxy disappears when you terminate the VM.

---

## Troubleshooting

| Symptom | Cause and fix |
|---------|---------------|
| `AMI ami-... is not 'available' (state=missing)` | SANS has not shared the AMI with your account, you are in the wrong region, or you typed the AMI ID wrong. Re-verify with Step 1. |
| `UnauthorizedOperation` on any `ec2:` call | Your IAM user lacks a permission. Confirm the `SEC546LabDeploy` policy from `infra/iam/` is attached, or temporarily use `AmazonEC2FullAccess`. |
| `InvalidClientTokenId` / `AuthFailure` | The GitHub secrets are wrong, have a trailing space, or the access key was deleted. Recreate both secrets. |
| `VcpuLimitExceeded` | Your account's On-Demand vCPU quota is below the 8 vCPUs an `m6i.2xlarge` needs. Service Quotas → EC2 → *Running On-Demand Standard instances* → request an increase to at least 8. New accounts often need this. |
| `InvalidSnapshot.NotFound` or a KMS error at launch | The AMI's encrypted snapshots use a KMS key that was not shared with you. Only SANS can fix this — ask them to share the KMS key too. |
| `Unsupported` when launching | `m6i.2xlarge` is not offered in the Availability Zone the default VPC picked. Rare in `us-east-2`. Contact your instructor. |
| Public IP is blank in the summary | The default VPC subnet does not auto-assign public IPs. Assign an Elastic IP in the console, or delete and recreate the default VPC. |
| Workflow doesn't appear in the Actions tab | On a fork, Actions are disabled until you click *I understand my workflows, go ahead and enable them*. |
| SmartProxy connects but pages fail to load | The VM is still booting the lab services — wait 2–3 minutes after launch. If it persists, re-check the Firefox steps in your class lab setup guide, then ask your instructor. |
| LLM labs fail with `401` / `403` / auth error | The SANS-provided LLM API key has expired. There is no replacement key — switch to [your own Bedrock account](#optional--if-the-sans-llm-api-key-stops-working). |
| LLM labs fail with `AccessDeniedException` | You are on your own Bedrock account but have not been granted model access. Bedrock → Model access in `us-east-1`. |

---

## What's in this repository

```
.github/workflows/
  deploy-student-vms.yml        Launch the VM and build the connection package
  delete-student-vm.yml         Terminate the VM and clean up SG + key pair
infra/certs/
  sec546-cloud-ca.der           Lab CA certificate (DER — import into Firefox)
  sec546-cloud-ca.pem           Same certificate, PEM form
infra/iam/
  sec546-lab-policy.json        Least-privilege IAM policy for the workflow user
scripts/
  generate-student-package.py   Builds the SmartProxy config + package
```

---

## Security notes

- The security group opens ports **22, 80, 443, 1080 to the entire internet**.
  This matches the classroom lab design. The VM is short-lived by intent —
  terminate it when class ends rather than leaving it exposed.
- The SSH private key is generated per run and shipped inside the workflow
  artifact. Anyone with read access to your repo can download it. Keep the repo
  private if you can.
- The lab CA certificate in this repo is a **teaching CA for intercepting lab
  traffic**. Import it into a browser profile you use for the class, and remove
  it from Firefox when the course is over.
- Never commit AWS credentials to the repository. They belong in GitHub Actions
  secrets only.

---

*SEC546 is a SANS Institute course. This repository contains deployment
automation only — the lab AMI itself is provided by SANS and is not distributed
here.*
