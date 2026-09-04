# AMI Access Request Template

Send this to your SANS SEC546 instructor or course support contact **before**
class. Nothing in this repository will work until SANS has shared the AMI with
your account.

Replace every `<...>` placeholder with your own values.

---

**Subject:** SEC546 — Request AMI share to AWS account `<YOUR-12-DIGIT-ACCOUNT-ID>`

Hello,

I am enrolled in SEC546 and would like to run the lab VM in my own AWS account.
Please share the latest SEC546 lab AMI with the account below.

| Field | Value |
|-------|-------|
| AWS account ID (12 digits) | `<YOUR-12-DIGIT-ACCOUNT-ID>` |
| Region                     | `us-east-2` (US East / Ohio) |
| Course edition             | `<5-day (L02)>` or `<2-day (main)>` |
| Class / event date         | `<EVENT NAME AND DATE>` |

Please confirm the **AMI ID** (`ami-...`) once the share is in place, so I can
supply it to the deployment workflow.

Thank you,
`<YOUR NAME>`

---

## What SANS does on their side

For reference, the share is a single API call on the AMI owner's account:

```bash
aws ec2 modify-image-attribute \
  --image-id ami-xxxxxxxxxxxxxxxxx \
  --region us-east-2 \
  --launch-permission "Add=[{UserId=<YOUR-12-DIGIT-ACCOUNT-ID>}]"
```

If the AMI's EBS snapshots are encrypted with a customer-managed KMS key, the
key must be shared with your account as well, otherwise the launch fails with
`Client.InvalidSnapshot.NotFound` or a KMS access-denied error.

## Verifying the share landed

Once SANS confirms, run this from your own account:

```bash
aws ec2 describe-images \
  --image-ids ami-xxxxxxxxxxxxxxxxx \
  --region us-east-2 \
  --query "Images[0].[ImageId,Name,State]" \
  --output table
```

`State` must be `available`. If you get `InvalidAMIID.NotFound`, the share has
not been applied to your account yet — go back to SANS before continuing.
