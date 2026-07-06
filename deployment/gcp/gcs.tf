# Sprint 12 — migração do MinIO local (docker/docker-compose.yml) para GCS.
#
# EXERCÍCIO DE ARQUITETURA: não rode `terraform apply` neste arquivo, mesmo
# o GCS tendo free tier — mantemos a mesma regra das outras duas migrações
# do sprint, pra não abrir exceção no meio do exercício.

resource "google_storage_bucket" "mlflow_artifacts" {
  name     = "${var.project_id}-mlflow-artifacts" # nomes de bucket são globais no GCS
  location = "US-CENTRAL1"                        # região elegível para o Always Free tier
  project  = var.project_id

  storage_class               = "STANDARD"
  uniform_bucket_level_access = true # IAM controla acesso; sem ACLs por objeto

  # Equivalente ao "mc mb" do serviço minio-init no docker-compose.yml —
  # lá o bucket era criado por um script de init; aqui é declarativo.

  lifecycle_rule {
    condition {
      age = 90 # artefatos com +90 dias
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE" # mais barato para acesso raro
    }
  }

  versioning {
    enabled = true # protege contra overwrite acidental de um model.pkl
  }
}

# Dá à mesma service account do Cloud SQL (mlflow_runner, definida em
# cloud_sql.tf) permissão para ler/escrever no bucket. Repare que não existe
# nenhum "access key" ou "secret" aqui — a identidade já é suficiente.
resource "google_storage_bucket_iam_member" "mlflow_runner_access" {
  bucket = google_storage_bucket.mlflow_artifacts.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.mlflow_runner.email}"
}

# Referência para o comando `mlflow server` — troca direta de:
#   --default-artifact-root s3://mlflow-artifacts/
# por:
output "mlflow_artifact_root" {
  value = "gs://${google_storage_bucket.mlflow_artifacts.name}/"
}
