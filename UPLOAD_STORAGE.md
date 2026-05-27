# Upload Storage

Render free services do not provide persistent local disk storage. Uploaded post images must be stored in an external object storage service such as Cloudflare R2.

## Cloudflare R2 settings

Create an R2 bucket and an R2 API token with object read/write access. Then set these Render environment variables.

```env
STORAGE_BACKEND=r2
S3_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
S3_BUCKET=<bucket-name>
S3_PUBLIC_BASE_URL=https://<public-r2-domain-or-custom-domain>
S3_ACCESS_KEY_ID=<r2-access-key-id>
S3_SECRET_ACCESS_KEY=<r2-secret-access-key>
S3_REGION=auto
```

New uploads are saved under `uploads/` in the bucket, and the public image URL is stored in the `posts.image_path` column.

Existing records that contain `uploads/...` still point to the old Render local path. If the original file disappeared from Render, edit the post and upload the image again after enabling R2.
