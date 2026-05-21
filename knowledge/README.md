# Knowledge Directory

This directory is a placeholder for local knowledge base files used during development and testing of Dify DSL workflows.

## Purpose

In production Dify deployments, knowledge bases are managed within the Dify platform UI and referenced by dataset IDs in the DSL YAML. This directory provides a local scratch space for:

- Sample documents to upload to a Dify knowledge base for testing
- Notes about knowledge base configuration and dataset IDs for each environment
- Reference material used when designing RAG pipelines

## Usage

1. Create your knowledge base in the Dify UI under **Knowledge** > **Create Knowledge Base**.
2. Upload your documents.
3. Copy the dataset ID from the knowledge base settings page.
4. Replace `YOUR_DATASET_ID_HERE` in any generated DSL YAML with the actual dataset ID.

## Note

Do not commit sensitive documents or proprietary content to this directory. Use `.gitignore` to exclude any files you add here that should not be tracked.
