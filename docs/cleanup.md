
Cleanup Guide

The project should be destroyed after testing unless resources are intentionally retained.

Planned cleanup command:

cd infra
terraform plan -destroy
terraform destroy

After destroying, verify that cost-sensitive resources have been removed.
