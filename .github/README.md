# GitHub Actions Workflows

This directory contains CI/CD workflows for automated deployment.

## Workflows

### deploy.yml - Production Deployment

**Trigger:** Push to `main` branch or manual trigger

**What it does:**
1. Checks out latest code
2. Sets up SSH connection to DigitalOcean Droplet
3. Connects to server and:
   - Pulls latest code from GitHub
   - Stops running containers
   - Rebuilds Docker images
   - Starts new containers
   - Performs health check
4. Reports success or failure

**Required Secrets:**

Configure these in: **Repository Settings → Secrets and variables → Actions**

| Secret Name | Description | Example |
|------------|-------------|---------|
| `DROPLET_HOST` | Your Droplet's IP address | `164.92.123.45` |
| `DROPLET_USER` | SSH user on Droplet | `jmx` |
| `DROPLET_SSH_KEY` | Private SSH key for authentication | Contents of `~/.ssh/id_rsa` |

## Setting Up Secrets

### 1. Get Your SSH Private Key

On your local machine:
```bash
cat ~/.ssh/id_rsa
```

Copy the entire output including:
```
-----BEGIN OPENSSH PRIVATE KEY-----
...
-----END OPENSSH PRIVATE KEY-----
```

### 2. Add to GitHub

1. Go to: https://github.com/JavohirMX/jarvis/settings/secrets/actions
2. Click "New repository secret"
3. Add each secret with its value

### 3. Verify Setup

After adding secrets, push a commit to trigger deployment:
```bash
git add .
git commit -m "Test deployment"
git push origin main
```

Monitor at: https://github.com/JavohirMX/jarvis/actions

## Manual Deployment Trigger

You can manually trigger deployment:
1. Go to **Actions** tab
2. Select "Deploy to DigitalOcean" workflow
3. Click "Run workflow"
4. Select `main` branch
5. Click "Run workflow"

## Troubleshooting

### SSH Connection Failed

**Error:** `Permission denied (publickey)`

**Solutions:**
1. Verify `DROPLET_SSH_KEY` is the complete private key
2. Ensure the corresponding public key is in `/home/jmx/.ssh/authorized_keys` on the Droplet
3. Test SSH manually: `ssh -i ~/.ssh/id_rsa jmx@your-droplet-ip`

### Deployment Script Failed

**Check server logs:**
```bash
ssh jmx@your-droplet-ip
cd /home/jmx/jarvis
docker-compose logs -f
```

**Common issues:**
- `.env` file missing or incomplete
- Port conflicts
- Docker service not running

### Health Check Failed

**Error:** `curl: (7) Failed to connect`

**Solutions:**
1. Check if containers are running:
   ```bash
   ssh jmx@your-droplet-ip
   docker-compose ps
   ```
2. Check application logs:
   ```bash
   docker-compose logs web
   ```
3. Verify port 8080 is accessible:
   ```bash
   curl http://localhost:8080/admin/login/
   ```

## Workflow Customization

### Change Deployment Branch

Edit `.github/workflows/deploy.yml`:
```yaml
on:
  push:
    branches:
      - main        # Change to your branch
      - production  # Add more branches
```

### Add Build Tests

Add a test job before deployment:
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Tests
        run: |
          # Add your test commands
          
  deploy:
    needs: test  # Only deploy if tests pass
    # ... existing deploy steps
```

### Add Slack Notifications

Add Slack notifications on deployment:
```yaml
- name: Notify Slack
  if: always()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

## Security Best Practices

1. **Never commit secrets** to the repository
2. **Rotate SSH keys** regularly
3. **Use least privilege** - SSH user should only have necessary permissions
4. **Monitor workflow logs** for suspicious activity
5. **Enable branch protection** for main branch

## Deployment Flow

```
Developer
    ↓
Push to GitHub (main branch)
    ↓
GitHub Actions Triggered
    ↓
Build & Test (optional)
    ↓
SSH to DigitalOcean Droplet
    ↓
Pull Latest Code
    ↓
Docker Compose Build
    ↓
Restart Containers
    ↓
Health Check
    ↓
✅ Deployment Complete
```

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Docker Compose in CI/CD](https://docs.docker.com/compose/ci-cd/)

---

**Questions?** Check [DEPLOYMENT.md](../DEPLOYMENT.md) for complete deployment documentation.

